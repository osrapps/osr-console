"""State-machine combat engine for B/X-style tactical encounters."""

import math
import uuid
from collections import deque
from dataclasses import dataclass

from osrlib.monster import Monster, MonsterParty
from osrlib.party import Party
from osrlib.player_character import PlayerCharacter

from osrlib.combat.context import CombatContext, CombatSide, CombatantRef
from osrlib.combat.dice_service import BXDiceService, DiceService
from osrlib.combat.events import (
    ActionRejected,
    AttackRolled,
    DamageApplied,
    EncounterEvent,
    EncounterFaulted,
    EncounterStarted,
    EntityDied,
    InitiativeRolled,
    RoundStarted,
    SurpriseRolled,
    TurnQueueBuilt,
    TurnSkipped,
    TurnStarted,
    VictoryDetermined,
)
from osrlib.combat.intents import ActionIntent, MeleeAttackIntent
from osrlib.combat.state import EncounterLoopError, EncounterOutcome, EncounterState


@dataclass(frozen=True)
class StepResult:
    """Value returned by each ``CombatEngine.step()`` call."""

    state: EncounterState
    needs_intent: bool
    pending_combatant_id: str | None
    events: tuple[EncounterEvent, ...]


class CombatEngine:
    """State-machine combat engine.

    Call ``step()`` repeatedly to advance combat one state at a time, or
    ``step_until_decision()`` to run until the engine needs an external intent
    (or combat ends).

    In Phase 1 the engine auto-submits intents for all combatants, so calling
    ``step()`` in a loop until ``state == ENDED`` runs a full encounter.
    """

    def __init__(
        self,
        pc_party: Party,
        monster_party: MonsterParty,
        dice: DiceService | None = None,
    ) -> None:
        self._ctx = CombatContext.build(pc_party, monster_party)
        self._dice: DiceService = dice or BXDiceService()
        self._state = EncounterState.INIT
        self._encounter_id = uuid.uuid4().hex[:12]
        self._pending_intent: ActionIntent | None = None
        self._outcome: EncounterOutcome | None = None

    # -- Public API ----------------------------------------------------------

    @property
    def state(self) -> EncounterState:
        return self._state

    @property
    def outcome(self) -> EncounterOutcome | None:
        return self._outcome

    def step(self, intent: ActionIntent | None = None) -> StepResult:
        """Execute a single state transition and return the result."""
        if intent is not None:
            self._pending_intent = intent

        events: list[EncounterEvent] = []
        try:
            handler = self._handlers[self._state]
            handler(self, events)
        except Exception as exc:
            events.append(
                EncounterFaulted(
                    state=self._state,
                    error_type=type(exc).__name__,
                    message=str(exc),
                )
            )
            self._outcome = EncounterOutcome.FAULTED
            self._state = EncounterState.ENDED

        return StepResult(
            state=self._state,
            needs_intent=self._state == EncounterState.AWAIT_INTENT,
            pending_combatant_id=self._ctx.current_combatant_id,
            events=tuple(events),
        )

    def step_until_decision(
        self, intent: ActionIntent | None = None, max_steps: int = 64
    ) -> tuple[StepResult, ...]:
        """Advance the engine until it needs an intent or combat ends.

        Returns all ``StepResult`` objects produced along the way.

        Raises:
            EncounterLoopError: If *max_steps* is exhausted without reaching
                a decision point or the ``ENDED`` state.
        """
        results: list[StepResult] = []
        for _ in range(max_steps):
            result = self.step(intent)
            intent = None  # only apply on first step
            results.append(result)
            if result.needs_intent or self._state == EncounterState.ENDED:
                return tuple(results)
        raise EncounterLoopError(
            f"Combat engine did not reach a decision point within {max_steps} steps"
        )

    # -- State handlers (private) --------------------------------------------

    def _handle_init(self, events: list[EncounterEvent]) -> None:
        events.append(EncounterStarted(encounter_id=self._encounter_id))

        pc_roll = self._dice.roll("1d6")
        monster_roll = self._dice.roll("1d6")
        pc_surprised = monster_roll > pc_roll
        monster_surprised = pc_roll > monster_roll

        events.append(
            SurpriseRolled(
                pc_roll=pc_roll,
                monster_roll=monster_roll,
                pc_surprised=pc_surprised,
                monster_surprised=monster_surprised,
            )
        )
        self._state = EncounterState.ROUND_START

    def _handle_round_start(self, events: list[EncounterEvent]) -> None:
        self._ctx.round_number += 1
        events.append(RoundStarted(round_number=self._ctx.round_number))

        # Roll initiative for every living combatant
        initiative: list[tuple[str, int]] = []
        for cid, ref in self._ctx.combatants.items():
            if ref.is_alive:
                roll = ref.entity.get_initiative_roll()
                initiative.append((cid, roll))

        # Sort descending by roll
        initiative.sort(key=lambda x: x[1], reverse=True)
        events.append(InitiativeRolled(order=tuple(initiative)))

        # Build turn queue
        self._ctx.turn_queue = deque(cid for cid, _ in initiative)
        events.append(TurnQueueBuilt(queue=tuple(self._ctx.turn_queue)))

        self._state = EncounterState.TURN_START

    def _handle_turn_start(self, events: list[EncounterEvent]) -> None:
        # If queue is empty, go to CHECK_VICTORY (which will start a new round if needed)
        if not self._ctx.turn_queue:
            self._ctx.current_combatant_id = None
            self._state = EncounterState.CHECK_VICTORY
            return

        cid = self._ctx.turn_queue.popleft()
        self._ctx.current_combatant_id = cid
        ref = self._ctx.combatants[cid]

        # Skip dead combatants
        if not ref.is_alive:
            events.append(TurnSkipped(combatant_id=cid, reason="dead"))
            self._state = EncounterState.TURN_START
            return

        events.append(TurnStarted(combatant_id=cid))

        # Phase 1 auto-provider: auto-submit a MeleeAttackIntent
        opposite_side = (
            CombatSide.MONSTER if ref.side == CombatSide.PC else CombatSide.PC
        )
        living_targets = self._ctx.living(opposite_side)

        if not living_targets:
            # No targets remain — go straight to victory check
            self._state = EncounterState.CHECK_VICTORY
            return

        target = self._dice.choice(living_targets)
        self._pending_intent = MeleeAttackIntent(actor_id=cid, target_id=target.id)
        self._state = EncounterState.VALIDATE_INTENT

    def _handle_await_intent(self, events: list[EncounterEvent]) -> None:
        if self._pending_intent is not None:
            self._state = EncounterState.VALIDATE_INTENT
        # else: stay in AWAIT_INTENT (engine pauses)

    def _handle_validate_intent(self, events: list[EncounterEvent]) -> None:
        intent = self._pending_intent
        self._pending_intent = None

        if intent is None:
            events.append(
                ActionRejected(
                    combatant_id=self._ctx.current_combatant_id or "",
                    reason="no intent",
                )
            )
            self._state = EncounterState.AWAIT_INTENT
            return

        # Validate actor matches current combatant
        if intent.actor_id != self._ctx.current_combatant_id:
            events.append(
                ActionRejected(
                    combatant_id=intent.actor_id,
                    reason=f"not current combatant (expected {self._ctx.current_combatant_id})",
                )
            )
            self._state = EncounterState.AWAIT_INTENT
            return

        # Validate target is alive
        target_ref = self._ctx.combatants.get(intent.target_id)
        if target_ref is None or not target_ref.is_alive:
            events.append(
                ActionRejected(
                    combatant_id=intent.actor_id, reason="target is dead or invalid"
                )
            )
            self._state = EncounterState.AWAIT_INTENT
            return

        # Intent is valid — stash for execution
        self._validated_intent = intent
        self._state = EncounterState.EXECUTE_ACTION

    def _handle_execute_action(self, events: list[EncounterEvent]) -> None:
        intent: MeleeAttackIntent = self._validated_intent
        self._validated_intent = None

        attacker_ref = self._ctx.combatants[intent.actor_id]
        defender_ref = self._ctx.combatants[intent.target_id]

        if attacker_ref.side == CombatSide.PC:
            self._execute_pc_attack(attacker_ref, defender_ref, events)
        else:
            self._execute_monster_attack(attacker_ref, defender_ref, events)

        self._state = EncounterState.CHECK_DEATHS

    def _execute_pc_attack(
        self,
        attacker_ref: CombatantRef,
        defender_ref: CombatantRef,
        events: list[EncounterEvent],
    ) -> None:
        pc: PlayerCharacter = attacker_ref.entity
        defender: Monster = defender_ref.entity

        needed = pc.character_class.current_level.get_to_hit_target_ac(
            defender.armor_class
        )
        attack_roll = pc.get_attack_roll()
        raw = attack_roll.total
        total = attack_roll.total_with_modifier

        is_critical = raw == 20
        is_hit = is_critical or (raw > 1 and total >= needed)

        events.append(
            AttackRolled(
                attacker_id=attacker_ref.id,
                defender_id=defender_ref.id,
                roll=raw,
                total=total,
                needed=needed,
                hit=is_hit,
                critical=is_critical,
            )
        )

        if is_hit:
            damage_roll = pc.get_damage_roll()
            multiplier = 1.5 if is_critical else 1
            amount = math.ceil(damage_roll.total_with_modifier * multiplier)
            defender.apply_damage(amount)
            events.append(
                DamageApplied(
                    source_id=attacker_ref.id,
                    target_id=defender_ref.id,
                    amount=amount,
                    target_hp_after=defender.hit_points,
                )
            )

    def _execute_monster_attack(
        self,
        attacker_ref: CombatantRef,
        defender_ref: CombatantRef,
        events: list[EncounterEvent],
    ) -> None:
        monster: Monster = attacker_ref.entity
        defender: PlayerCharacter = defender_ref.entity

        needed = monster.get_to_hit_target_ac(defender.armor_class)

        for attack_roll in monster.get_attack_rolls():
            raw = attack_roll.total
            total = attack_roll.total_with_modifier
            is_hit = defender.is_alive and total >= needed

            events.append(
                AttackRolled(
                    attacker_id=attacker_ref.id,
                    defender_id=defender_ref.id,
                    roll=raw,
                    total=total,
                    needed=needed,
                    hit=is_hit,
                    critical=False,
                )
            )

            if is_hit:
                damage_roll = monster.get_damage_roll()
                amount = damage_roll.total_with_modifier
                defender.apply_damage(amount)
                events.append(
                    DamageApplied(
                        source_id=attacker_ref.id,
                        target_id=defender_ref.id,
                        amount=amount,
                        target_hp_after=defender.hit_points,
                    )
                )

    def _handle_check_deaths(self, events: list[EncounterEvent]) -> None:
        for cid, ref in self._ctx.combatants.items():
            if not ref.is_alive and cid not in self._ctx.announced_deaths:
                self._ctx.announced_deaths.add(cid)
                events.append(EntityDied(entity_id=cid))
        self._state = EncounterState.CHECK_MORALE

    def _handle_check_morale(self, events: list[EncounterEvent]) -> None:
        # Phase 1: pass-through, no morale checks
        self._state = EncounterState.CHECK_VICTORY

    def _handle_check_victory(self, events: list[EncounterEvent]) -> None:
        if not self._ctx.monsters_alive():
            self._outcome = EncounterOutcome.PARTY_VICTORY
            events.append(VictoryDetermined(outcome=EncounterOutcome.PARTY_VICTORY))
            self._state = EncounterState.ENDED
        elif not self._ctx.pcs_alive():
            self._outcome = EncounterOutcome.OPPOSITION_VICTORY
            events.append(
                VictoryDetermined(outcome=EncounterOutcome.OPPOSITION_VICTORY)
            )
            self._state = EncounterState.ENDED
        elif self._ctx.turn_queue:
            self._state = EncounterState.TURN_START
        else:
            self._state = EncounterState.ROUND_START

    # Handler dispatch table
    _handlers: dict = {
        EncounterState.INIT: _handle_init,
        EncounterState.ROUND_START: _handle_round_start,
        EncounterState.TURN_START: _handle_turn_start,
        EncounterState.AWAIT_INTENT: _handle_await_intent,
        EncounterState.VALIDATE_INTENT: _handle_validate_intent,
        EncounterState.EXECUTE_ACTION: _handle_execute_action,
        EncounterState.CHECK_DEATHS: _handle_check_deaths,
        EncounterState.CHECK_MORALE: _handle_check_morale,
        EncounterState.CHECK_VICTORY: _handle_check_victory,
    }

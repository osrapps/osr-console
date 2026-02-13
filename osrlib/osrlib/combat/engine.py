"""State-machine combat engine for B/X-style tactical encounters."""

import uuid
from collections import deque
from dataclasses import dataclass

from osrlib.monster import MonsterParty
from osrlib.party import Party

from osrlib.combat.actions import CombatAction, MeleeAttackAction
from osrlib.combat.context import CombatContext, CombatSide
from osrlib.combat.dice_service import BXDiceService, DiceService
from osrlib.combat.effects import (
    ApplyConditionEffect,
    ConsumeSlotEffect,
    DamageEffect,
    Effect,
)
from osrlib.combat.events import (
    ActionRejected,
    ConditionApplied,
    DamageApplied,
    EncounterEvent,
    EncounterFaulted,
    EncounterStarted,
    EntityDied,
    InitiativeRolled,
    RoundStarted,
    SpellSlotConsumed,
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

    The current implementation auto-submits intents for all combatants, so
    calling ``step()`` in a loop until ``state == ENDED`` runs a full encounter.
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
        self._validated_action: CombatAction | None = None
        self._pending_effects: tuple[Effect, ...] = ()
        self._spell_slots_remaining_by_caster: dict[str, dict[int, int]] = {}
        self._outcome: EncounterOutcome | None = None

    # -- Public API ----------------------------------------------------------

    @property
    def state(self) -> EncounterState:
        return self._state

    @property
    def outcome(self) -> EncounterOutcome | None:
        return self._outcome

    def step(self, intent: ActionIntent | None = None) -> StepResult:
        """Execute a single state transition and return the result.

        Calling ``step()`` after the engine has reached ``ENDED`` is a safe
        no-op: the original outcome is preserved and no events are emitted.
        """
        if self._state == EncounterState.ENDED:
            return StepResult(
                state=EncounterState.ENDED,
                needs_intent=False,
                pending_combatant_id=None,
                events=(),
            )

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
        # Fault the engine into a safe terminal state before raising.
        self._outcome = EncounterOutcome.FAULTED
        self._state = EncounterState.ENDED
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

        # Auto-provider: submit a MeleeAttackIntent against a random living opponent.
        opposite_side = (
            CombatSide.MONSTER if ref.side == CombatSide.PC else CombatSide.PC
        )
        living_targets = self._ctx.living(opposite_side)

        if not living_targets:
            # No targets remain, go straight to victory check.
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

        action = self._action_for_intent(intent)
        if action is None:
            events.append(
                ActionRejected(combatant_id=intent.actor_id, reason="unsupported intent")
            )
            self._state = EncounterState.AWAIT_INTENT
            return

        reasons = action.validate(self._ctx)
        if reasons:
            events.append(ActionRejected(combatant_id=intent.actor_id, reason="; ".join(reasons)))
            self._state = EncounterState.AWAIT_INTENT
            return

        self._validated_action = action
        self._state = EncounterState.EXECUTE_ACTION

    def _handle_execute_action(self, events: list[EncounterEvent]) -> None:
        action = self._validated_action
        self._validated_action = None

        if action is None:
            events.append(
                ActionRejected(
                    combatant_id=self._ctx.current_combatant_id or "",
                    reason="no validated action",
                )
            )
            self._state = EncounterState.AWAIT_INTENT
            return

        result = action.execute(self._ctx)
        events.extend(result.events)
        self._pending_effects = result.effects
        self._state = EncounterState.APPLY_EFFECTS

    def _handle_apply_effects(self, events: list[EncounterEvent]) -> None:
        effects = self._pending_effects
        self._pending_effects = ()

        for effect in effects:
            match effect:
                case DamageEffect(source_id=source_id, target_id=target_id, amount=amount):
                    target_ref = self._ctx.combatants[target_id]
                    target_ref.entity.apply_damage(amount)
                    events.append(
                        DamageApplied(
                            source_id=source_id,
                            target_id=target_id,
                            amount=amount,
                            target_hp_after=target_ref.entity.hit_points,
                        )
                    )
                case ConsumeSlotEffect(caster_id=caster_id, level=level):
                    caster_ref = self._ctx.combatants[caster_id]
                    try:
                        remaining = self._consume_spell_slot(
                            caster_id=caster_id,
                            caster_entity=caster_ref.entity,
                            level=level,
                        )
                    except ValueError as exc:
                        events.append(
                            ActionRejected(combatant_id=caster_id, reason=str(exc))
                        )
                        continue
                    events.append(
                        SpellSlotConsumed(
                            caster_id=caster_id,
                            level=level,
                            remaining=remaining,
                        )
                    )
                case ApplyConditionEffect(
                    source_id=source_id,
                    target_id=target_id,
                    condition_id=condition_id,
                    duration=duration,
                ):
                    events.append(
                        ConditionApplied(
                            source_id=source_id,
                            target_id=target_id,
                            condition_id=condition_id,
                            duration=duration,
                        )
                    )
                case _:
                    events.append(
                        ActionRejected(
                            combatant_id=self._ctx.current_combatant_id or "",
                            reason=f"unknown effect type: {type(effect).__name__}",
                        )
                    )

        self._state = EncounterState.CHECK_DEATHS

    def _consume_spell_slot(
        self, caster_id: str, caster_entity: object, level: int
    ) -> int:
        """Consume one spell slot and return remaining slots at that level."""
        use_spell_slot = getattr(caster_entity, "use_spell_slot", None)
        if callable(use_spell_slot):
            return int(use_spell_slot(level))

        if caster_id not in self._spell_slots_remaining_by_caster:
            self._spell_slots_remaining_by_caster[caster_id] = (
                self._get_spell_slots_for_caster(caster_entity)
            )

        slots = self._spell_slots_remaining_by_caster[caster_id]
        if slots.get(level, 0) <= 0:
            raise ValueError(f"no level {level} spell slots remaining")

        slots[level] -= 1
        return slots[level]

    @staticmethod
    def _get_spell_slots_for_caster(caster_entity: object) -> dict[int, int]:
        """Extract spell-slot counts from the caster's current class level."""
        character_class = getattr(caster_entity, "character_class", None)
        if character_class is None:
            return {}

        current_level = getattr(character_class, "current_level", None)
        spell_slots = getattr(current_level, "spell_slots", None)
        if not spell_slots:
            return {}

        return {int(slot_level): int(count) for slot_level, count in spell_slots}

    def _action_for_intent(self, intent: ActionIntent) -> CombatAction | None:
        if isinstance(intent, MeleeAttackIntent):
            return MeleeAttackAction(actor_id=intent.actor_id, target_id=intent.target_id)
        return None

    def _handle_check_deaths(self, events: list[EncounterEvent]) -> None:
        for cid, ref in self._ctx.combatants.items():
            if not ref.is_alive and cid not in self._ctx.announced_deaths:
                self._ctx.announced_deaths.add(cid)
                events.append(EntityDied(entity_id=cid))
        self._state = EncounterState.CHECK_MORALE

    def _handle_check_morale(self, events: list[EncounterEvent]) -> None:
        # Phase 2: pass-through, no morale checks yet.
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
        EncounterState.APPLY_EFFECTS: _handle_apply_effects,
        EncounterState.CHECK_DEATHS: _handle_check_deaths,
        EncounterState.CHECK_MORALE: _handle_check_morale,
        EncounterState.CHECK_VICTORY: _handle_check_victory,
    }

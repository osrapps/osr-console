"""Combat action interfaces and the Phase 2 melee action implementation."""

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass

from osrlib.combat.context import CombatContext, CombatSide
from osrlib.combat.effects import DamageEffect, Effect
from osrlib.combat.events import AttackRolled, EncounterEvent
from osrlib.monster import Monster
from osrlib.player_character import PlayerCharacter


@dataclass(frozen=True)
class ActionResult:
    """Pure action output: resolution events plus deferred mutation effects."""

    events: tuple[EncounterEvent, ...]
    effects: tuple[Effect, ...]


class CombatAction(ABC):
    """Interface implemented by each concrete combat action."""

    @abstractmethod
    def validate(self, ctx: CombatContext) -> tuple[str, ...]:
        """Return rejection reasons if the action is illegal."""

    @abstractmethod
    def execute(self, ctx: CombatContext) -> ActionResult:
        """Resolve the action and return events plus effects."""


@dataclass(frozen=True)
class MeleeAttackAction(CombatAction):
    """Resolve a melee attack while deferring mutations as effects."""

    actor_id: str
    target_id: str

    def validate(self, ctx: CombatContext) -> tuple[str, ...]:
        actor_ref = ctx.combatants.get(self.actor_id)
        if actor_ref is None:
            return ("actor is invalid",)
        if self.actor_id != ctx.current_combatant_id:
            return (f"not current combatant (expected {ctx.current_combatant_id})",)
        if not actor_ref.is_alive:
            return ("actor is dead",)

        target_ref = ctx.combatants.get(self.target_id)
        if target_ref is None or not target_ref.is_alive:
            return ("target is dead or invalid",)
        if target_ref.side == actor_ref.side:
            return ("target must be an opponent",)

        return ()

    def execute(self, ctx: CombatContext) -> ActionResult:
        attacker_ref = ctx.combatants[self.actor_id]
        defender_ref = ctx.combatants[self.target_id]

        if attacker_ref.side == CombatSide.PC:
            return self._execute_pc_attack(
                attacker_id=attacker_ref.id,
                defender_id=defender_ref.id,
                attacker=attacker_ref.entity,
                defender=defender_ref.entity,
            )

        return self._execute_monster_attack(
            attacker_id=attacker_ref.id,
            defender_id=defender_ref.id,
            attacker=attacker_ref.entity,
            defender=defender_ref.entity,
        )

    @staticmethod
    def _execute_pc_attack(
        attacker_id: str,
        defender_id: str,
        attacker: PlayerCharacter,
        defender: Monster,
    ) -> ActionResult:
        needed = attacker.character_class.current_level.get_to_hit_target_ac(
            defender.armor_class
        )
        attack_roll = attacker.get_attack_roll()
        raw = attack_roll.total
        total = attack_roll.total_with_modifier

        is_critical = raw == 20
        is_hit = is_critical or (raw > 1 and total >= needed)

        events: list[EncounterEvent] = [
            AttackRolled(
                attacker_id=attacker_id,
                defender_id=defender_id,
                roll=raw,
                total=total,
                needed=needed,
                hit=is_hit,
                critical=is_critical,
            )
        ]
        effects: list[Effect] = []

        if is_hit:
            damage_roll = attacker.get_damage_roll()
            multiplier = 1.5 if is_critical else 1
            amount = math.ceil(damage_roll.total_with_modifier * multiplier)
            effects.append(
                DamageEffect(source_id=attacker_id, target_id=defender_id, amount=amount)
            )

        return ActionResult(events=tuple(events), effects=tuple(effects))

    @staticmethod
    def _execute_monster_attack(
        attacker_id: str,
        defender_id: str,
        attacker: Monster,
        defender: PlayerCharacter,
    ) -> ActionResult:
        needed = attacker.get_to_hit_target_ac(defender.armor_class)
        defender_hp = defender.hit_points

        events: list[EncounterEvent] = []
        effects: list[Effect] = []

        for attack_roll in attacker.get_attack_rolls():
            raw = attack_roll.total
            total = attack_roll.total_with_modifier
            is_hit = defender_hp > 0 and total >= needed

            events.append(
                AttackRolled(
                    attacker_id=attacker_id,
                    defender_id=defender_id,
                    roll=raw,
                    total=total,
                    needed=needed,
                    hit=is_hit,
                    critical=False,
                )
            )

            if is_hit:
                damage_roll = attacker.get_damage_roll()
                amount = damage_roll.total_with_modifier
                effects.append(
                    DamageEffect(
                        source_id=attacker_id, target_id=defender_id, amount=amount
                    )
                )
                defender_hp = max(defender_hp - amount, 0)

        return ActionResult(events=tuple(events), effects=tuple(effects))

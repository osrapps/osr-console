"""Combat action interfaces and concrete action implementations."""

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass

from osrlib.combat.context import CombatContext, CombatSide
from osrlib.combat.effects import (
    ApplyConditionEffect,
    ConsumeSlotEffect,
    DamageEffect,
    Effect,
    FleeEffect,
)
from osrlib.combat.events import (
    AttackRolled,
    EncounterEvent,
    Rejection,
    RejectionCode,
    SpellCast,
)
from osrlib.combat.spells import get_spell
from osrlib.dice_roller import roll_dice
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
    def validate(self, ctx: CombatContext) -> tuple[Rejection, ...]:
        """Return rejection reasons if the action is illegal."""

    @abstractmethod
    def execute(self, ctx: CombatContext) -> ActionResult:
        """Resolve the action and return events plus effects."""


def _validate_actor_and_target(
    actor_id: str, target_id: str, ctx: CombatContext
) -> tuple[Rejection, ...]:
    """Shared validation for actor-alive, current-combatant, target-alive, opponent."""
    actor_ref = ctx.combatants.get(actor_id)
    if actor_ref is None:
        return (
            Rejection(code=RejectionCode.INVALID_ACTOR, message="actor is invalid"),
        )
    if actor_id != ctx.current_combatant_id:
        return (
            Rejection(
                code=RejectionCode.NOT_CURRENT_COMBATANT,
                message=f"not current combatant (expected {ctx.current_combatant_id})",
            ),
        )
    if not actor_ref.is_alive:
        return (Rejection(code=RejectionCode.ACTOR_DEAD, message="actor is dead"),)

    target_ref = ctx.combatants.get(target_id)
    if target_ref is None or not target_ref.is_alive:
        return (
            Rejection(
                code=RejectionCode.INVALID_TARGET,
                message="target is dead or invalid",
            ),
        )
    if target_ref.side == actor_ref.side:
        return (
            Rejection(
                code=RejectionCode.TARGET_NOT_OPPONENT,
                message="target must be an opponent",
            ),
        )
    return ()


@dataclass(frozen=True)
class MeleeAttackAction(CombatAction):
    """Resolve a melee attack while deferring mutations as effects."""

    actor_id: str
    target_id: str

    def validate(self, ctx: CombatContext) -> tuple[Rejection, ...]:
        return _validate_actor_and_target(self.actor_id, self.target_id, ctx)

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
                DamageEffect(
                    source_id=attacker_id, target_id=defender_id, amount=amount
                )
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


@dataclass(frozen=True)
class RangedAttackAction(CombatAction):
    """Resolve a ranged attack (PC only — monsters continue melee)."""

    actor_id: str
    target_id: str

    def validate(self, ctx: CombatContext) -> tuple[Rejection, ...]:
        base = _validate_actor_and_target(self.actor_id, self.target_id, ctx)
        if base:
            return base

        actor_ref = ctx.combatants[self.actor_id]
        if actor_ref.side != CombatSide.PC:
            return (
                Rejection(
                    code=RejectionCode.MONSTER_ACTION_NOT_SUPPORTED,
                    message="ranged attacks are not supported for monsters",
                ),
            )

        pc: PlayerCharacter = actor_ref.entity
        if not pc.has_ranged_weapon_equipped():
            return (
                Rejection(
                    code=RejectionCode.NO_RANGED_WEAPON,
                    message="no ranged weapon equipped",
                ),
            )
        return ()

    def execute(self, ctx: CombatContext) -> ActionResult:
        attacker_ref = ctx.combatants[self.actor_id]
        defender_ref = ctx.combatants[self.target_id]
        attacker: PlayerCharacter = attacker_ref.entity

        needed = attacker.character_class.current_level.get_to_hit_target_ac(
            defender_ref.armor_class
        )
        attack_roll = attacker.get_ranged_attack_roll()
        raw = attack_roll.total
        total = attack_roll.total_with_modifier

        is_critical = raw == 20
        is_hit = is_critical or (raw > 1 and total >= needed)

        events: list[EncounterEvent] = [
            AttackRolled(
                attacker_id=self.actor_id,
                defender_id=self.target_id,
                roll=raw,
                total=total,
                needed=needed,
                hit=is_hit,
                critical=is_critical,
            )
        ]
        effects: list[Effect] = []

        if is_hit:
            damage_roll = attacker.get_ranged_damage_roll()
            multiplier = 1.5 if is_critical else 1
            amount = math.ceil(damage_roll.total_with_modifier * multiplier)
            effects.append(
                DamageEffect(
                    source_id=self.actor_id, target_id=self.target_id, amount=amount
                )
            )

        return ActionResult(events=tuple(events), effects=tuple(effects))


@dataclass(frozen=True)
class CastSpellAction(CombatAction):
    """Resolve a spell cast using the spell catalog."""

    actor_id: str
    spell_id: str
    slot_level: int
    target_ids: tuple[str, ...]

    def validate(self, ctx: CombatContext) -> tuple[Rejection, ...]:
        actor_ref = ctx.combatants.get(self.actor_id)
        if actor_ref is None:
            return (
                Rejection(code=RejectionCode.INVALID_ACTOR, message="actor is invalid"),
            )
        if self.actor_id != ctx.current_combatant_id:
            return (
                Rejection(
                    code=RejectionCode.NOT_CURRENT_COMBATANT,
                    message=f"not current combatant (expected {ctx.current_combatant_id})",
                ),
            )
        if not actor_ref.is_alive:
            return (Rejection(code=RejectionCode.ACTOR_DEAD, message="actor is dead"),)

        spell_def = get_spell(self.spell_id)
        if spell_def is None:
            return (
                Rejection(
                    code=RejectionCode.UNKNOWN_SPELL,
                    message=f"unknown spell: {self.spell_id}",
                ),
            )

        # Caster class must be in spell's usable_by set
        if isinstance(actor_ref.entity, PlayerCharacter):
            pc: PlayerCharacter = actor_ref.entity
            if pc.character_class.class_type not in spell_def.usable_by:
                return (
                    Rejection(
                        code=RejectionCode.INELIGIBLE_CASTER,
                        message=f"{pc.character_class.class_type.value} cannot cast {spell_def.name}",
                    ),
                )

            # Slot level must match the spell's defined level
            if self.slot_level != spell_def.spell_level:
                return (
                    Rejection(
                        code=RejectionCode.SLOT_LEVEL_MISMATCH,
                        message=(
                            f"slot_level {self.slot_level} does not match "
                            f"spell level {spell_def.spell_level}"
                        ),
                    ),
                )

            # PC's class level must have slots at the requested level
            spell_slots = pc.character_class.current_level.spell_slots
            if not spell_slots or not any(
                int(sl) == self.slot_level and int(cnt) > 0 for sl, cnt in spell_slots
            ):
                return (
                    Rejection(
                        code=RejectionCode.NO_SPELL_SLOT,
                        message=f"no level {self.slot_level} spell slots available for this class/level",
                    ),
                )

        # Validate targets — use `is None` not `not targets` per podcast warning
        if self.target_ids is None:
            return (
                Rejection(
                    code=RejectionCode.INVALID_TARGET,
                    message="target_ids must not be None",
                ),
            )

        for tid in self.target_ids:
            target_ref = ctx.combatants.get(tid)
            if target_ref is None or not target_ref.is_alive:
                return (
                    Rejection(
                        code=RejectionCode.INVALID_TARGET,
                        message=f"target {tid} is dead or invalid",
                    ),
                )

        return ()

    def execute(self, ctx: CombatContext) -> ActionResult:
        spell_def = get_spell(self.spell_id)

        events: list[EncounterEvent] = [
            SpellCast(
                caster_id=self.actor_id,
                spell_id=self.spell_id,
                spell_name=spell_def.name,
                target_ids=self.target_ids,
            )
        ]
        effects: list[Effect] = [
            ConsumeSlotEffect(caster_id=self.actor_id, level=self.slot_level)
        ]

        for tid in self.target_ids:
            if spell_def.damage_die:
                dmg_roll = roll_dice(spell_def.damage_die)
                effects.append(
                    DamageEffect(
                        source_id=self.actor_id,
                        target_id=tid,
                        amount=dmg_roll.total_with_modifier,
                    )
                )
            if spell_def.condition_id:
                effects.append(
                    ApplyConditionEffect(
                        source_id=self.actor_id,
                        target_id=tid,
                        condition_id=spell_def.condition_id,
                        duration=spell_def.condition_duration,
                    )
                )

        return ActionResult(events=tuple(events), effects=tuple(effects))


@dataclass(frozen=True)
class FleeAction(CombatAction):
    """Resolve a flee action — the combatant leaves combat."""

    actor_id: str

    def validate(self, ctx: CombatContext) -> tuple[Rejection, ...]:
        actor_ref = ctx.combatants.get(self.actor_id)
        if actor_ref is None:
            return (
                Rejection(code=RejectionCode.INVALID_ACTOR, message="actor is invalid"),
            )
        if self.actor_id != ctx.current_combatant_id:
            return (
                Rejection(
                    code=RejectionCode.NOT_CURRENT_COMBATANT,
                    message=f"not current combatant (expected {ctx.current_combatant_id})",
                ),
            )
        if not actor_ref.is_alive:
            return (Rejection(code=RejectionCode.ACTOR_DEAD, message="actor is dead"),)
        return ()

    def execute(self, ctx: CombatContext) -> ActionResult:
        return ActionResult(
            events=(),
            effects=(FleeEffect(combatant_id=self.actor_id),),
        )

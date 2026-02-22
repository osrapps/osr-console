"""Combat action interfaces and concrete action implementations."""

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass

from osrlib.combat.context import CombatContext, CombatSide
from osrlib.combat.modifiers import ModifiedStat
from osrlib.combat.effects import (
    ApplyConditionEffect,
    ApplyModifierEffect,
    ConsumeItemEffect,
    ConsumeSlotEffect,
    DamageEffect,
    Effect,
    FleeEffect,
    HealEffect,
)
from osrlib.combat.targeting import TargetMode
from osrlib.combat.events import (
    AttackRolled,
    EncounterEvent,
    GroupTargetsResolved,
    ItemUsed,
    Rejection,
    RejectionCode,
    SavingThrowRolled,
    SpellCast,
    TurnResult,
    TurnUndeadAttempted,
    UndeadTurned,
)
from osrlib.combat.spells import get_spell
from osrlib.combat.targeting import (
    get_combatant_hd,
    resolve_hd_pool,
    resolve_random_group,
)
from osrlib.dice_roller import roll_dice
from osrlib.enums import AttackType, CharacterClassType
from osrlib.monster import Monster
from osrlib.player_character import PlayerCharacter
from osrlib.saving_throws import get_saving_throws_for_class_and_level


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

        # Gather modifiers from buffs/debuffs
        atk_mod = ctx.modifiers.get_total(self.actor_id, ModifiedStat.ATTACK)
        def_ac_mod = ctx.modifiers.get_total(self.target_id, ModifiedStat.ARMOR_CLASS)

        if attacker_ref.side == CombatSide.PC:
            return self._execute_pc_attack(
                attacker_id=attacker_ref.id,
                defender_id=defender_ref.id,
                attacker=attacker_ref.entity,
                defender=defender_ref.entity,
                attack_modifier=atk_mod,
                defender_ac_modifier=def_ac_mod,
            )

        return self._execute_monster_attack(
            attacker_id=attacker_ref.id,
            defender_id=defender_ref.id,
            attacker=attacker_ref.entity,
            defender=defender_ref.entity,
            attack_modifier=atk_mod,
            defender_ac_modifier=def_ac_mod,
        )

    @staticmethod
    def _execute_pc_attack(
        attacker_id: str,
        defender_id: str,
        attacker: PlayerCharacter,
        defender: Monster,
        attack_modifier: int = 0,
        defender_ac_modifier: int = 0,
    ) -> ActionResult:
        effective_ac = defender.armor_class + defender_ac_modifier
        needed = attacker.character_class.current_level.get_to_hit_target_ac(
            effective_ac
        )
        attack_roll = attacker.get_attack_roll()
        raw = attack_roll.total
        total = attack_roll.total_with_modifier + attack_modifier

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
        attack_modifier: int = 0,
        defender_ac_modifier: int = 0,
    ) -> ActionResult:
        effective_ac = defender.armor_class + defender_ac_modifier
        needed = attacker.get_to_hit_target_ac(effective_ac)
        defender_hp = defender.hit_points

        events: list[EncounterEvent] = []
        effects: list[Effect] = []

        for attack_roll in attacker.get_attack_rolls():
            raw = attack_roll.total
            total = attack_roll.total_with_modifier + attack_modifier
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

        atk_mod = ctx.modifiers.get_total(self.actor_id, ModifiedStat.ATTACK)
        def_ac_mod = ctx.modifiers.get_total(self.target_id, ModifiedStat.ARMOR_CLASS)

        effective_ac = defender_ref.armor_class + def_ac_mod
        needed = attacker.character_class.current_level.get_to_hit_target_ac(
            effective_ac
        )
        attack_roll = attacker.get_ranged_attack_roll()
        raw = attack_roll.total
        total = attack_roll.total_with_modifier + atk_mod

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


def _get_save_target(entity: PlayerCharacter | Monster, attack_type: AttackType) -> int:
    """Look up the saving throw target number for a PC or Monster.

    Returns:
        The target number the entity must roll >= on 1d20 to save.
    """
    if isinstance(entity, PlayerCharacter):
        saves = get_saving_throws_for_class_and_level(
            entity.character_class.class_type, entity.level
        )
        if saves and attack_type in saves:
            return saves[attack_type]
        return 20  # fallback: nearly impossible save
    if isinstance(entity, Monster):
        saves = getattr(entity, "saving_throws", None)
        if saves and attack_type in saves:
            return saves[attack_type]
        return 20
    return 20


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

        # Validate targets based on target_mode
        ally_modes = {TargetMode.SINGLE_ALLY, TargetMode.ALL_ALLIES, TargetMode.SELF}
        for tid in self.target_ids:
            target_ref = ctx.combatants.get(tid)
            if target_ref is None or not target_ref.is_alive:
                return (
                    Rejection(
                        code=RejectionCode.INVALID_TARGET,
                        message=f"target {tid} is dead or invalid",
                    ),
                )
            # Ally-targeting spells must target same-side combatants
            if spell_def.target_mode in ally_modes:
                if target_ref.side != actor_ref.side:
                    return (
                        Rejection(
                            code=RejectionCode.TARGET_NOT_ALLY,
                            message=f"target {tid} must be an ally",
                        ),
                    )

        return ()

    @staticmethod
    def _get_caster_level(ctx: CombatContext, actor_id: str) -> int:
        """Resolve the caster's level for scaling spells."""
        ref = ctx.combatants.get(actor_id)
        if ref is None:
            return 1
        entity = ref.entity
        if isinstance(entity, PlayerCharacter):
            return entity.level or 1
        # Monsters: use save_as_level as a proxy for caster level
        return getattr(entity, "save_as_level", 1) or 1

    @staticmethod
    def _resolve_projectile_count(
        thresholds: tuple[tuple[int, int], ...], caster_level: int
    ) -> int:
        """Determine how many projectiles to fire based on caster level thresholds."""
        count = 1
        for level_min, num_projectiles in thresholds:
            if caster_level >= level_min:
                count = num_projectiles
        return count

    @staticmethod
    def _check_saving_throw(
        ctx: CombatContext,
        target_id: str,
        spell_def,
        events: list[EncounterEvent],
        penalty: int = 0,
    ) -> bool:
        """Roll a saving throw for *target_id* against *spell_def*.

        Appends a `SavingThrowRolled` event to *events* and returns True if
        the target saved successfully.  Returns False (no save attempted) when
        the spell allows no save.

        Args:
            penalty: Modifier to the target number. Negative values make the
                save harder (raise the effective threshold).
        """
        if spell_def.save_type is None:
            return False
        target_ref = ctx.combatants.get(target_id)
        if target_ref is None:
            return False
        target_number = _get_save_target(target_ref.entity, spell_def.save_type)
        effective_target = target_number - penalty
        save_roll = roll_dice("1d20").total
        saved = save_roll >= effective_target
        events.append(
            SavingThrowRolled(
                target_id=target_id,
                save_type=spell_def.save_type.name,
                target_number=effective_target,
                roll=save_roll,
                success=saved,
                spell_name=spell_def.name,
                penalty=penalty,
            )
        )
        return saved

    def execute(self, ctx: CombatContext) -> ActionResult:
        spell_def = get_spell(self.spell_id)
        caster_level = self._get_caster_level(ctx, self.actor_id)

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

        # Resolve actual target list — may be filtered by HD-pool or group dice
        target_ids = self.target_ids
        save_penalty = 0

        # HD-pool targeting (e.g. Sleep): roll pool, select lowest-HD first
        if spell_def.hd_pool_dice:
            pool_roll = roll_dice(spell_def.hd_pool_dice).total_with_modifier
            candidates = tuple(
                (tid, get_combatant_hd(ctx.combatants[tid].entity))
                for tid in target_ids
                if ctx.combatants.get(tid)
                and ctx.combatants[tid].is_alive
                and (
                    spell_def.max_target_hd is None
                    or get_combatant_hd(ctx.combatants[tid].entity)
                    <= spell_def.max_target_hd
                )
                and not getattr(ctx.combatants[tid].entity, "is_undead", False)
            )
            target_ids = resolve_hd_pool(candidates, pool_roll)
            events.append(
                GroupTargetsResolved(
                    spell_name=spell_def.name,
                    pool_roll=pool_roll,
                    resolved_target_ids=target_ids,
                )
            )
        # Group random targeting (e.g. Hold Person group mode)
        elif spell_def.group_target_dice and len(target_ids) > 1:
            # Filter by max_target_hd if set
            if spell_def.max_target_hd is not None:
                target_ids = tuple(
                    tid
                    for tid in target_ids
                    if get_combatant_hd(ctx.combatants[tid].entity)
                    <= spell_def.max_target_hd
                )
            count_roll = roll_dice(spell_def.group_target_dice).total_with_modifier
            target_ids = resolve_random_group(target_ids, count_roll)
            events.append(
                GroupTargetsResolved(
                    spell_name=spell_def.name,
                    pool_roll=count_roll,
                    resolved_target_ids=target_ids,
                )
            )
        else:
            # Single-target mode: apply single_save_penalty if set
            save_penalty = spell_def.single_save_penalty
            # Filter by max_target_hd for single target too
            if spell_def.max_target_hd is not None:
                target_ids = tuple(
                    tid
                    for tid in target_ids
                    if ctx.combatants.get(tid)
                    and get_combatant_hd(ctx.combatants[tid].entity)
                    <= spell_def.max_target_hd
                )

        # Handle projectile-based spells (e.g. Magic Missile at higher levels)
        if spell_def.projectile_thresholds and spell_def.damage_die:
            num_projectiles = self._resolve_projectile_count(
                spell_def.projectile_thresholds, caster_level
            )
            # Distribute projectiles across targets round-robin
            targets = target_ids
            for i in range(num_projectiles):
                tid = targets[i % len(targets)]
                saved = self._check_saving_throw(
                    ctx, tid, spell_def, events, penalty=save_penalty
                )
                if saved and spell_def.save_negates:
                    continue
                dmg_roll = roll_dice(spell_def.damage_die)
                amount = dmg_roll.total_with_modifier
                if saved and not spell_def.save_negates:
                    amount = max(1, amount // 2)
                effects.append(
                    DamageEffect(source_id=self.actor_id, target_id=tid, amount=amount)
                )
            return ActionResult(events=tuple(events), effects=tuple(effects))

        for tid in target_ids:
            saved = self._check_saving_throw(
                ctx, tid, spell_def, events, penalty=save_penalty
            )

            if saved and spell_def.save_negates:
                continue

            if spell_def.heal_die:
                heal_roll = roll_dice(spell_def.heal_die)
                effects.append(
                    HealEffect(
                        source_id=self.actor_id,
                        target_id=tid,
                        amount=heal_roll.total_with_modifier,
                    )
                )
            elif spell_def.damage_per_level:
                dice_expr = f"{caster_level}{spell_def.damage_per_level}"
                dmg_roll = roll_dice(dice_expr)
                amount = dmg_roll.total_with_modifier
                if saved and not spell_def.save_negates:
                    amount = max(1, amount // 2)
                effects.append(
                    DamageEffect(
                        source_id=self.actor_id,
                        target_id=tid,
                        amount=amount,
                    )
                )
            elif spell_def.damage_die:
                dmg_roll = roll_dice(spell_def.damage_die)
                amount = dmg_roll.total_with_modifier
                if saved and not spell_def.save_negates:
                    amount = max(1, amount // 2)
                effects.append(
                    DamageEffect(
                        source_id=self.actor_id,
                        target_id=tid,
                        amount=amount,
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
            for spell_mod in spell_def.modifiers:
                effects.append(
                    ApplyModifierEffect(
                        source_id=self.actor_id,
                        target_id=tid,
                        modifier_id=spell_mod.modifier_id,
                        stat=spell_mod.stat,
                        value=spell_mod.value,
                        duration=spell_mod.duration,
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


# Throwable combat item definitions
THROWABLE_ITEMS: dict[str, dict] = {
    "Flask of Oil": {"damage_die": "1d8", "range": 10},
    "Holy Water": {"damage_die": "1d8", "range": 10},
}


@dataclass(frozen=True)
class UseItemAction(CombatAction):
    """Resolve using a thrown combat item (oil flask, holy water, etc.)."""

    actor_id: str
    item_name: str
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

        if self.item_name not in THROWABLE_ITEMS:
            return (
                Rejection(
                    code=RejectionCode.ITEM_NOT_THROWABLE,
                    message=f"{self.item_name} is not a throwable combat item",
                ),
            )

        # Verify the actor actually has the item in inventory
        from osrlib.player_character import PlayerCharacter

        if isinstance(actor_ref.entity, PlayerCharacter):
            has_item = any(
                item.name == self.item_name
                for item in actor_ref.entity.inventory.equipment
            )
            if not has_item:
                return (
                    Rejection(
                        code=RejectionCode.ITEM_NOT_IN_INVENTORY,
                        message=f"{self.item_name} is not in inventory",
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
        item_data = THROWABLE_ITEMS.get(self.item_name, {})
        damage_die = item_data.get("damage_die", "1d4")

        events: list[EncounterEvent] = [
            ItemUsed(
                actor_id=self.actor_id,
                item_name=self.item_name,
                target_ids=self.target_ids,
            )
        ]
        effects: list[Effect] = [
            ConsumeItemEffect(actor_id=self.actor_id, item_name=self.item_name),
        ]

        for tid in self.target_ids:
            dmg_roll = roll_dice(damage_die)
            effects.append(
                DamageEffect(
                    source_id=self.actor_id,
                    target_id=tid,
                    amount=dmg_roll.total_with_modifier,
                )
            )

        return ActionResult(events=tuple(events), effects=tuple(effects))


# OSE B/X Turn Undead table.
# Rows = cleric level (1-11+), Columns = undead tier (1-8).
# Tier mapping: 1=Skeleton, 2=Zombie, 2*=Ghoul (HD 2 with specials),
# 3=Wight, 4=Wraith, 5=Mummy, 6=Spectre, 7-9=Vampire.
# None = impossible, positive int = need that on 2d6, 0 = auto-turn, -1 = auto-destroy.
_TURN_TABLE: tuple[tuple[int | None, ...], ...] = (
    # Tier:  1     2    2*    3     4     5     6    7-9
    (7, 9, 11, None, None, None, None, None),  # Lvl 1
    (0, 7, 9, 11, None, None, None, None),  # Lvl 2
    (0, 0, 7, 9, 11, None, None, None),  # Lvl 3
    (-1, 0, 0, 7, 9, 11, None, None),  # Lvl 4
    (-1, -1, 0, 0, 7, 9, 11, None),  # Lvl 5
    (-1, -1, -1, 0, 0, 7, 9, 11),  # Lvl 6
    (-1, -1, -1, -1, 0, 0, 7, 9),  # Lvl 7
    (-1, -1, -1, -1, -1, 0, 0, 7),  # Lvl 8
    (-1, -1, -1, -1, -1, -1, 0, 0),  # Lvl 9
    (-1, -1, -1, -1, -1, -1, -1, 0),  # Lvl 10
    (-1, -1, -1, -1, -1, -1, -1, -1),  # Lvl 11+
)


@dataclass(frozen=True)
class TurnUndeadAction(CombatAction):
    """Resolve a Cleric's Turn Undead ability using the OSE B/X table."""

    actor_id: str

    @staticmethod
    def _get_undead_tier(monster: Monster) -> int:
        """Map a monster to its undead tier (1-8) for the turn table.

        The table columns are: 1=Skeleton, 2=Zombie, 2*=Ghoul (index 2),
        3=Wight (index 3), 4=Wraith, 5=Mummy, 6=Spectre, 7-9=Vampire.
        Because the 2* slot inserts an extra column between HD 2 and HD 3,
        monsters with HD >= 3 must shift +1 to land on the correct column.
        """
        hd = monster.hp_roll.num_dice
        if hd <= 1:
            return 1
        if hd == 2:
            num_special = monster.num_special_abilities
            return 3 if num_special > 0 else 2
        # HD 3+ shift by 1 to account for the 2* slot
        return min(hd + 1, 8)

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

        # Must be a Cleric
        if not isinstance(actor_ref.entity, PlayerCharacter):
            return (
                Rejection(
                    code=RejectionCode.INELIGIBLE_CASTER,
                    message="only Clerics can turn undead",
                ),
            )
        if actor_ref.entity.character_class.class_type != CharacterClassType.CLERIC:
            return (
                Rejection(
                    code=RejectionCode.INELIGIBLE_CASTER,
                    message="only Clerics can turn undead",
                ),
            )

        # Must have at least one living undead enemy
        has_undead = any(
            ref.is_alive
            and not ref.has_fled
            and ref.side == CombatSide.MONSTER
            and isinstance(ref.entity, Monster)
            and getattr(ref.entity, "is_undead", False)
            for ref in ctx.combatants.values()
        )
        if not has_undead:
            return (
                Rejection(
                    code=RejectionCode.INVALID_TARGET,
                    message="no undead enemies present",
                ),
            )
        return ()

    def execute(self, ctx: CombatContext) -> ActionResult:
        actor_ref = ctx.combatants[self.actor_id]
        pc: PlayerCharacter = actor_ref.entity
        cleric_level = pc.level
        level_idx = min(max(cleric_level - 1, 0), 10)

        events: list[EncounterEvent] = []
        effects: list[Effect] = []

        # Find all living undead enemies
        undead_targets: list[tuple[str, Monster, int]] = []
        for cid, ref in ctx.combatants.items():
            if (
                ref.side == CombatSide.MONSTER
                and ref.is_alive
                and not ref.has_fled
                and isinstance(ref.entity, Monster)
                and getattr(ref.entity, "is_undead", False)
            ):
                tier = self._get_undead_tier(ref.entity)
                undead_targets.append((cid, ref.entity, tier))

        if not undead_targets:
            events.append(
                TurnUndeadAttempted(
                    actor_id=self.actor_id,
                    roll=0,
                    target_number=None,
                    result=TurnResult.IMPOSSIBLE,
                )
            )
            return ActionResult(events=tuple(events), effects=tuple(effects))

        # Use the best (lowest) tier present to determine initial success
        best_tier = min(t[2] for t in undead_targets)
        table_entry = _TURN_TABLE[level_idx][best_tier - 1]

        if table_entry is None:
            events.append(
                TurnUndeadAttempted(
                    actor_id=self.actor_id,
                    roll=0,
                    target_number=None,
                    result=TurnResult.IMPOSSIBLE,
                )
            )
            return ActionResult(events=tuple(events), effects=tuple(effects))

        # Roll once for the attempt (if needed)
        if table_entry > 0:
            turn_roll = roll_dice("2d6").total_with_modifier
            if turn_roll < table_entry:
                events.append(
                    TurnUndeadAttempted(
                        actor_id=self.actor_id,
                        roll=turn_roll,
                        target_number=table_entry,
                        result=TurnResult.FAILED,
                    )
                )
                return ActionResult(events=tuple(events), effects=tuple(effects))
        else:
            turn_roll = 0

        # Determine overall result from the best-tier entry
        overall_result = TurnResult.DESTROYED if table_entry == -1 else TurnResult.TURNED

        events.append(
            TurnUndeadAttempted(
                actor_id=self.actor_id,
                roll=turn_roll,
                target_number=table_entry if table_entry > 0 else None,
                result=overall_result,
            )
        )

        # Roll 2d6 for HD affected
        hd_pool = roll_dice("2d6").total_with_modifier

        # Sort undead by tier ascending, then consume from pool with per-tier checks
        undead_targets.sort(key=lambda t: t[2])
        affected_count = 0
        for cid, monster, tier in undead_targets:
            # Per-tier check: look up this specific undead's entry
            entry = _TURN_TABLE[level_idx][tier - 1]
            if entry is None:
                continue  # impossible for this tier
            if entry > 0 and turn_roll < entry:
                continue  # roll wasn't high enough for this tier
            this_destroy = entry == -1

            effective_hd = max(monster.hp_roll.num_dice, 1)
            if effective_hd > hd_pool and affected_count > 0:
                break
            # Always affect at least one target
            if effective_hd <= hd_pool:
                hd_pool -= effective_hd

            affected_count += 1

            if this_destroy:
                effects.append(
                    DamageEffect(
                        source_id=self.actor_id,
                        target_id=cid,
                        amount=monster.hit_points,
                    )
                )
            else:
                effects.append(FleeEffect(combatant_id=cid))

            events.append(
                UndeadTurned(
                    actor_id=self.actor_id,
                    target_id=cid,
                    destroyed=this_destroy,
                    hd_spent=effective_hd,
                )
            )

            if hd_pool <= 0 and affected_count > 0:
                break

        return ActionResult(events=tuple(events), effects=tuple(effects))

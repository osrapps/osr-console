"""Lightweight spell catalog for combat actions.

This is NOT a full data-driven spell/effects DSL — just exemplar definitions
that ``CastSpellAction`` looks up at execution time.
"""

from dataclasses import dataclass

from osrlib.enums import AttackType, CharacterClassType
from osrlib.combat.targeting import TargetMode


@dataclass(frozen=True)
class SpellModifier:
    """A temporary stat modifier applied by a spell."""

    modifier_id: str
    stat: str  # ModifiedStat name (e.g. "ATTACK", "ARMOR_CLASS")
    value: int
    duration: int


@dataclass(frozen=True)
class SpellDefinition:
    """Static definition of a combat spell looked up by ``spell_id``."""

    spell_id: str
    name: str
    spell_level: int
    damage_die: str | None
    num_targets: int  # 1 = single target, -1 = all opponents (legacy)
    auto_hit: bool
    condition_id: str | None
    condition_duration: int | None
    usable_by: frozenset[CharacterClassType]
    save_type: AttackType | None = None  # None = no save (Magic Missile, Sleep)
    save_negates: bool = True  # True = save negates; False = save halves damage
    target_mode: TargetMode = TargetMode.SINGLE_ENEMY
    heal_die: str | None = None  # e.g. "1d6+1" for Cure Light Wounds
    modifiers: tuple[SpellModifier, ...] = ()  # buff/debuff modifiers
    # Phase 4: scaling fields
    damage_per_level: str | None = None  # e.g. "1d6" — damage = Nd6 where N=caster_level
    projectile_thresholds: tuple[tuple[int, int], ...] = ()  # ((1,1),(6,3),(11,5)) for MM
    reverse_id: str | None = None  # spell_id of the reversed form
    is_reversed: bool = False


SPELL_CATALOG: dict[str, SpellDefinition] = {}


def _register(*defs: SpellDefinition) -> None:
    for d in defs:
        SPELL_CATALOG[d.spell_id] = d


_register(
    SpellDefinition(
        spell_id="magic_missile",
        name="Magic Missile",
        spell_level=1,
        damage_die="1d6+1",
        num_targets=1,
        auto_hit=True,
        condition_id=None,
        condition_duration=None,
        usable_by=frozenset({CharacterClassType.MAGIC_USER, CharacterClassType.ELF}),
        target_mode=TargetMode.SINGLE_ENEMY,
        projectile_thresholds=((1, 1), (6, 3), (11, 5)),
    ),
    SpellDefinition(
        spell_id="sleep",
        name="Sleep",
        spell_level=1,
        damage_die=None,
        num_targets=-1,
        auto_hit=True,
        condition_id="asleep",
        condition_duration=None,
        usable_by=frozenset({CharacterClassType.MAGIC_USER, CharacterClassType.ELF}),
        target_mode=TargetMode.ALL_ENEMIES,
    ),
    SpellDefinition(
        spell_id="hold_person",
        name="Hold Person",
        spell_level=2,
        damage_die=None,
        num_targets=1,
        auto_hit=True,
        condition_id="held",
        condition_duration=9,
        usable_by=frozenset({CharacterClassType.CLERIC}),
        save_type=AttackType.RODS_STAVES_SPELLS,
        target_mode=TargetMode.SINGLE_ENEMY,
    ),
    SpellDefinition(
        spell_id="light_offensive",
        name="Light",
        spell_level=1,
        damage_die=None,
        num_targets=1,
        auto_hit=True,
        condition_id="blinded",
        condition_duration=12,
        usable_by=frozenset(
            {
                CharacterClassType.CLERIC,
                CharacterClassType.MAGIC_USER,
                CharacterClassType.ELF,
            }
        ),
        target_mode=TargetMode.SINGLE_ENEMY,
    ),
    SpellDefinition(
        spell_id="cure_light_wounds",
        name="Cure Light Wounds",
        spell_level=1,
        damage_die=None,
        num_targets=1,
        auto_hit=True,
        condition_id=None,
        condition_duration=None,
        usable_by=frozenset({CharacterClassType.CLERIC}),
        target_mode=TargetMode.SINGLE_ALLY,
        heal_die="1d6+1",
        reverse_id="cause_light_wounds",
    ),
    SpellDefinition(
        spell_id="cause_light_wounds",
        name="Cause Light Wounds",
        spell_level=1,
        damage_die="1d6+1",
        num_targets=1,
        auto_hit=False,
        condition_id=None,
        condition_duration=None,
        usable_by=frozenset({CharacterClassType.CLERIC}),
        target_mode=TargetMode.SINGLE_ENEMY,
        is_reversed=True,
        reverse_id="cure_light_wounds",
    ),
    SpellDefinition(
        spell_id="bless",
        name="Bless",
        spell_level=2,
        damage_die=None,
        num_targets=-1,
        auto_hit=True,
        condition_id=None,
        condition_duration=None,
        usable_by=frozenset({CharacterClassType.CLERIC}),
        target_mode=TargetMode.ALL_ALLIES,
        modifiers=(
            SpellModifier("bless_atk", "ATTACK", 1, 6),
            SpellModifier("bless_morale", "SAVING_THROW", 1, 6),
        ),
    ),
    SpellDefinition(
        spell_id="shield",
        name="Shield",
        spell_level=1,
        damage_die=None,
        num_targets=1,
        auto_hit=True,
        condition_id=None,
        condition_duration=None,
        usable_by=frozenset({CharacterClassType.MAGIC_USER, CharacterClassType.ELF}),
        target_mode=TargetMode.SELF,
        modifiers=(SpellModifier("shield_ac", "ARMOR_CLASS", -2, 12),),
    ),
    SpellDefinition(
        spell_id="fireball",
        name="Fireball",
        spell_level=3,
        damage_die=None,  # Uses damage_per_level instead
        num_targets=-1,
        auto_hit=True,
        condition_id=None,
        condition_duration=None,
        usable_by=frozenset({CharacterClassType.MAGIC_USER, CharacterClassType.ELF}),
        target_mode=TargetMode.ALL_ENEMIES,
        save_type=AttackType.DRAGON_BREATH,
        save_negates=False,  # save halves
        damage_per_level="1d6",
    ),
    SpellDefinition(
        spell_id="lightning_bolt",
        name="Lightning Bolt",
        spell_level=3,
        damage_die=None,
        num_targets=-1,
        auto_hit=True,
        condition_id=None,
        condition_duration=None,
        usable_by=frozenset({CharacterClassType.MAGIC_USER, CharacterClassType.ELF}),
        target_mode=TargetMode.ALL_ENEMIES,
        save_type=AttackType.DRAGON_BREATH,
        save_negates=False,  # save halves
        damage_per_level="1d6",
    ),
)


def get_spell(spell_id: str) -> SpellDefinition | None:
    """Look up a spell definition by ID."""
    return SPELL_CATALOG.get(spell_id)

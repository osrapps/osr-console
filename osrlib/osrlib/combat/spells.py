"""Lightweight spell catalog for combat actions.

This is NOT a full data-driven spell/effects DSL — just exemplar definitions
that ``CastSpellAction`` looks up at execution time.
"""

from dataclasses import dataclass

from osrlib.enums import CharacterClassType


@dataclass(frozen=True)
class SpellDefinition:
    """Static definition of a combat spell looked up by ``spell_id``."""

    spell_id: str
    name: str
    spell_level: int
    damage_die: str | None
    num_targets: int  # 1 = single target, -1 = all opponents
    auto_hit: bool
    condition_id: str | None
    condition_duration: int | None
    usable_by: frozenset[CharacterClassType]


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
    ),
)


def get_spell(spell_id: str) -> SpellDefinition | None:
    """Look up a spell definition by ID."""
    return SPELL_CATALOG.get(spell_id)

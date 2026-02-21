"""Intent types submitted to the combat engine by players or AI."""

from dataclasses import dataclass


@dataclass(frozen=True)
class MeleeAttackIntent:
    """Intent to perform a melee attack against a specific target."""

    actor_id: str
    target_id: str


@dataclass(frozen=True)
class RangedAttackIntent:
    """Intent to perform a ranged attack against a specific target."""

    actor_id: str
    target_id: str


@dataclass(frozen=True)
class CastSpellIntent:
    """Intent to cast a spell.

    ``target_ids`` is an empty tuple for self-targeting spells, never ``None``.
    """

    actor_id: str
    spell_id: str
    slot_level: int
    target_ids: tuple[str, ...]


@dataclass(frozen=True)
class UseItemIntent:
    """Intent to use a combat item (thrown oil, holy water, etc.)."""

    actor_id: str
    item_name: str
    target_ids: tuple[str, ...]


@dataclass(frozen=True)
class FleeIntent:
    """Intent to flee from combat (morale failure)."""

    actor_id: str


ActionIntent = MeleeAttackIntent | RangedAttackIntent | CastSpellIntent | UseItemIntent | FleeIntent

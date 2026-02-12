"""Intent types submitted to the combat engine by players or AI."""

from dataclasses import dataclass


@dataclass(frozen=True)
class MeleeAttackIntent:
    """Intent to perform a melee attack against a specific target."""

    actor_id: str
    target_id: str


# Union type that expands in later phases (FleeIntent, RangedAttackIntent, CastSpellIntent).
ActionIntent = MeleeAttackIntent

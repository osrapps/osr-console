"""Effect types produced by combat actions and applied by the engine."""

from dataclasses import dataclass


@dataclass(frozen=True)
class DamageEffect:
    """Apply HP damage to a combatant."""

    source_id: str
    target_id: str
    amount: int


@dataclass(frozen=True)
class ConsumeSlotEffect:
    """Consume a spell slot from a caster."""

    caster_id: str
    level: int


@dataclass(frozen=True)
class ApplyConditionEffect:
    """Apply a named condition to a combatant."""

    source_id: str
    target_id: str
    condition_id: str
    duration: int | None = None


@dataclass(frozen=True)
class FleeEffect:
    """Remove a combatant from active combat (fled)."""

    combatant_id: str


Effect = DamageEffect | ConsumeSlotEffect | ApplyConditionEffect | FleeEffect

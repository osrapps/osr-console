"""Temporary combat stat modifiers with duration tracking.

Supports attack, damage, AC, and saving throw modifiers applied by
buff/debuff spells (Bless, Shield, Protection from Evil).
"""

from dataclasses import dataclass
from enum import Enum, auto


class ModifiedStat(Enum):
    """Which combat stat a modifier affects."""

    ATTACK = auto()
    DAMAGE = auto()
    ARMOR_CLASS = auto()
    SAVING_THROW = auto()


@dataclass
class ActiveModifier:
    """An active modifier instance on a specific combatant."""

    modifier_id: str
    source_id: str
    stat: ModifiedStat
    value: int
    remaining_rounds: int | None  # None = permanent until removed


class ModifierTracker:
    """Stores and queries active modifiers per combatant."""

    def __init__(self) -> None:
        self._modifiers: dict[str, list[ActiveModifier]] = {}

    def add(self, combatant_id: str, modifier: ActiveModifier) -> None:
        """Add an active modifier to a combatant."""
        if combatant_id not in self._modifiers:
            self._modifiers[combatant_id] = []
        self._modifiers[combatant_id].append(modifier)

    def get_total(self, combatant_id: str, stat: ModifiedStat) -> int:
        """Return the sum of all active modifiers for a stat on a combatant."""
        return sum(
            m.value
            for m in self._modifiers.get(combatant_id, [])
            if m.stat == stat
        )

    def get_all(self, combatant_id: str) -> list[ActiveModifier]:
        """Return all active modifiers on a combatant."""
        return list(self._modifiers.get(combatant_id, []))

    def tick_round(self) -> list[tuple[str, str]]:
        """Decrement durations and return expired (combatant_id, modifier_id) pairs."""
        expired: list[tuple[str, str]] = []
        for combatant_id, modifiers in self._modifiers.items():
            remaining: list[ActiveModifier] = []
            for mod in modifiers:
                if mod.remaining_rounds is not None:
                    mod.remaining_rounds -= 1
                    if mod.remaining_rounds <= 0:
                        expired.append((combatant_id, mod.modifier_id))
                        continue
                remaining.append(mod)
            self._modifiers[combatant_id] = remaining
        return expired

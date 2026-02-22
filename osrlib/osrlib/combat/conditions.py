"""Condition tracking for the combat engine.

Manages active conditions (held, asleep, blinded) on combatants, including
duration tracking, turn-skip enforcement, and break-on-damage behavior.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ConditionBehavior:
    """Static flags describing how a condition type behaves."""

    skip_turn: bool = False
    break_on_damage: bool = False


CONDITION_REGISTRY: dict[str, ConditionBehavior] = {
    "held": ConditionBehavior(skip_turn=True),
    "asleep": ConditionBehavior(skip_turn=True, break_on_damage=True),
    "blinded": ConditionBehavior(),
}


@dataclass
class ActiveCondition:
    """An active condition instance on a specific combatant."""

    condition_id: str
    source_id: str
    remaining_rounds: int | None  # None = permanent until removed
    skip_turn: bool
    break_on_damage: bool


class ConditionTracker:
    """Stores and queries active conditions per combatant."""

    def __init__(self) -> None:
        self._conditions: dict[str, list[ActiveCondition]] = {}

    def add(self, target_id: str, condition: ActiveCondition) -> None:
        """Add an active condition to a combatant."""
        if target_id not in self._conditions:
            self._conditions[target_id] = []
        self._conditions[target_id].append(condition)

    def remove(self, target_id: str, condition_id: str) -> ActiveCondition | None:
        """Remove and return the first matching condition, or None."""
        conditions = self._conditions.get(target_id)
        if not conditions:
            return None
        for i, cond in enumerate(conditions):
            if cond.condition_id == condition_id:
                return conditions.pop(i)
        return None

    def has(self, target_id: str, condition_id: str) -> bool:
        """Check if a combatant has a specific active condition."""
        return any(
            c.condition_id == condition_id for c in self._conditions.get(target_id, [])
        )

    def get_all(self, target_id: str) -> list[ActiveCondition]:
        """Return all active conditions on a combatant."""
        return list(self._conditions.get(target_id, []))

    def should_skip_turn(self, target_id: str) -> bool:
        """Return True if any active condition requires skipping the turn."""
        return any(c.skip_turn for c in self._conditions.get(target_id, []))

    def skip_reason(self, target_id: str) -> str | None:
        """Return the condition_id of the first turn-skipping condition, or None."""
        for c in self._conditions.get(target_id, []):
            if c.skip_turn:
                return c.condition_id
        return None

    def tick_round(self) -> list[tuple[str, str]]:
        """Decrement durations and return expired (combatant_id, condition_id) pairs."""
        expired: list[tuple[str, str]] = []
        for target_id, conditions in self._conditions.items():
            remaining: list[ActiveCondition] = []
            for cond in conditions:
                if cond.remaining_rounds is not None:
                    cond.remaining_rounds -= 1
                    if cond.remaining_rounds <= 0:
                        expired.append((target_id, cond.condition_id))
                        continue
                remaining.append(cond)
            self._conditions[target_id] = remaining
        return expired

    def remove_break_on_damage(self, target_id: str) -> list[str]:
        """Remove all break-on-damage conditions from a combatant.

        Returns:
            List of removed condition_ids.
        """
        conditions = self._conditions.get(target_id)
        if not conditions:
            return []
        removed: list[str] = []
        remaining: list[ActiveCondition] = []
        for cond in conditions:
            if cond.break_on_damage:
                removed.append(cond.condition_id)
            else:
                remaining.append(cond)
        self._conditions[target_id] = remaining
        return removed

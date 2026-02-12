"""Dice abstraction layer for the combat engine.

Provides a protocol for dice rolling so the engine can be tested with deterministic sequences.
"""

import random
from collections.abc import Sequence
from typing import Protocol, TypeVar

from osrlib.dice_roller import roll_dice

T = TypeVar("T")


class DiceService(Protocol):
    """Protocol that the combat engine uses for all randomness."""

    def roll(self, expr: str) -> int:
        """Roll dice using standard notation (e.g. ``"1d6"``) and return the total."""
        ...

    def d20(self) -> int:
        """Roll a single d20 and return the raw result (no modifiers)."""
        ...

    def choice(self, items: Sequence[T]) -> T:
        """Pick a random element from *items*."""
        ...


class BXDiceService:
    """Production dice service wrapping ``osrlib.dice_roller.roll_dice``."""

    def __init__(self) -> None:
        self._rng = random.SystemRandom()

    def roll(self, expr: str) -> int:
        return roll_dice(expr).total_with_modifier

    def d20(self) -> int:
        return self._rng.randint(1, 20)

    def choice(self, items: Sequence[T]) -> T:
        return self._rng.choice(items)


class FixedDiceService:
    """Deterministic dice service for testing.

    Accepts a sequence of ints and returns them in order, cycling when exhausted.
    """

    def __init__(self, values: Sequence[int]) -> None:
        if not values:
            raise ValueError("FixedDiceService requires at least one value")
        self._values = list(values)
        self._index = 0

    def _next(self) -> int:
        val = self._values[self._index % len(self._values)]
        self._index += 1
        return val

    def roll(self, expr: str) -> int:
        return self._next()

    def d20(self) -> int:
        return self._next()

    def choice(self, items: Sequence[T]) -> T:
        idx = self._next() % len(items)
        return items[idx]

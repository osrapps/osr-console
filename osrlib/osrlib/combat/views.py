"""Immutable view dataclasses for UI consumption of combat state."""

from dataclasses import dataclass

from osrlib.combat.context import CombatSide


@dataclass(frozen=True)
class CombatantView:
    """Frozen snapshot of a single combatant's observable state."""

    id: str
    name: str
    side: CombatSide
    hp: int
    max_hp: int
    armor_class: int
    is_alive: bool


@dataclass(frozen=True)
class CombatView:
    """Frozen snapshot of the entire combat state for UI rendering."""

    round_number: int
    current_combatant_id: str | None
    combatants: tuple[CombatantView, ...]
    announced_deaths: frozenset[str]

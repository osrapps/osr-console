"""Centralized game state shared across all screens."""

from dataclasses import dataclass, field

from osrlib.adventure import Adventure


@dataclass
class GameState:
    """Mutable game state accessed via ``self.app.game_state``."""

    adventure: Adventure | None = None
    party_gold: int = 0
    party_gems: list[dict] = field(default_factory=list)
    party_jewelry: list[dict] = field(default_factory=list)
    turn_count: int = 0
    in_dungeon: bool = False

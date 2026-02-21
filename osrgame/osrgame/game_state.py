"""Centralized game state shared across all screens."""

from dataclasses import dataclass

from osrlib.adventure import Adventure


@dataclass
class GameState:
    """Mutable game state accessed via ``self.app.game_state``."""

    adventure: Adventure | None = None
    turn_count: int = 0
    in_dungeon: bool = False

    def to_dict(self) -> dict:
        """Serialize game state to a dictionary for save files."""
        data = {
            "turn_count": self.turn_count,
            "in_dungeon": self.in_dungeon,
        }
        if self.adventure:
            data["adventure"] = self.adventure.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "GameState":
        """Restore game state from a saved dictionary."""
        gs = cls()
        gs.turn_count = data.get("turn_count", 0)
        gs.in_dungeon = data.get("in_dungeon", False)
        if "adventure" in data:
            gs.adventure = Adventure.from_dict(data["adventure"])
        return gs

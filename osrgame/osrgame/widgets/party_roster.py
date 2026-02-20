"""Compact party HP/status roster reused across screens."""

from rich.text import Text
from textual.widgets import DataTable


class PartyRosterWidget(DataTable):
    """DataTable showing party members with Name, Class, Lv, HP, AC."""

    DEFAULT_CSS = """
    PartyRosterWidget {
        height: 100%;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(cursor_type="row", **kwargs)

    def on_mount(self) -> None:
        self.add_columns("Name", "Class", "Lv", "HP", "AC")

    def refresh_roster(self) -> None:
        """Rebuild rows from the current party."""
        gs = self.app.game_state
        if gs.adventure is None or gs.adventure.active_party is None:
            return
        party = gs.adventure.active_party
        self.clear()
        for pc in party.members:
            hp_text = (
                "DEAD" if pc.hit_points <= 0 else f"{pc.hit_points}/{pc.max_hit_points}"
            )
            self.add_row(
                pc.name,
                pc.character_class.class_type.value,
                Text(str(pc.level), justify="center"),
                Text(hp_text, justify="center"),
                Text(str(pc.armor_class), justify="center"),
                key=pc.name,
            )

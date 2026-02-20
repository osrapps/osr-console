"""Direction and action command bar for the exploration screen."""

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Button, Static

from osrlib.dungeon import Direction, Exit


class CommandBar(Horizontal):
    """Direction buttons + action buttons for dungeon exploration."""

    DEFAULT_CSS = """
    CommandBar {
        height: auto;
        padding: 0 1;
        align: center middle;
    }

    CommandBar Button {
        margin: 0 1;
        min-width: 6;
    }

    CommandBar .dir-btn {
        min-width: 6;
    }

    CommandBar .separator {
        width: 2;
        height: 3;
        content-align: center middle;
        color: #4a4a8a;
    }

    CommandBar .action-btn {
        min-width: 10;
    }
    """

    def compose(self) -> ComposeResult:
        yield Button("N", id="btn-dir-north", classes="dir-btn", disabled=True)
        yield Button("S", id="btn-dir-south", classes="dir-btn", disabled=True)
        yield Button("E", id="btn-dir-east", classes="dir-btn", disabled=True)
        yield Button("W", id="btn-dir-west", classes="dir-btn", disabled=True)
        yield Button("U", id="btn-dir-up", classes="dir-btn", disabled=True)
        yield Button("D", id="btn-dir-down", classes="dir-btn", disabled=True)
        yield Static("|", classes="separator")
        yield Button("Camp", id="btn-camp", classes="action-btn")
        yield Button("Town", id="btn-town", classes="action-btn")

    def update_exits(self, exits: list[Exit]) -> None:
        """Enable direction buttons matching available exits, disable the rest."""
        available = {e.direction for e in exits}
        dir_map = {
            Direction.NORTH: "#btn-dir-north",
            Direction.SOUTH: "#btn-dir-south",
            Direction.EAST: "#btn-dir-east",
            Direction.WEST: "#btn-dir-west",
            Direction.UP: "#btn-dir-up",
            Direction.DOWN: "#btn-dir-down",
        }
        for direction, btn_id in dir_map.items():
            btn = self.query_one(btn_id, Button)
            btn.disabled = direction not in available

"""Main menu screen with title art and New/Load/Quit."""

from textual import on
from textual.app import ComposeResult
from textual.containers import Center, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Static


TITLE_ART = r"""
  ___  ____  ____     ____                      _
 / _ \/ ___||  _ \   / ___|___  _ __  ___  ___ | | ___
| | | \___ \| |_) | | |   / _ \| '_ \/ __|/ _ \| |/ _ \
| |_| |___) |  _ <  | |__| (_) | | | \__ \ (_) | |  __/
 \___/|____/|_| \_\  \____\___/|_| |_|___/\___/|_|\___|

        Adventures in turn-based text
"""


class MainMenuScreen(Screen):
    """Title screen with New game, Load game, and Quit buttons."""

    BINDINGS = [
        ("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Center():
            with Vertical(id="main-menu-container"):
                yield Static(TITLE_ART, id="title-art")
                with Center(id="menu-buttons"):
                    with Vertical():
                        yield Button("New game", id="btn-new-game", variant="primary")
                        yield Button("Load game", id="btn-load-game")
                        yield Button("Quit", id="btn-quit")
        yield Footer()

    @on(Button.Pressed, "#btn-new-game")
    def start_new_game(self) -> None:
        """Create a default party and adventure, then go to town."""
        self.app.start_new_game()

    @on(Button.Pressed, "#btn-load-game")
    def load_game(self) -> None:
        """Load a saved game (stub - goes to town with default party)."""
        self.app.start_new_game()

    @on(Button.Pressed, "#btn-quit")
    def quit_game(self) -> None:
        self.app.exit()

    def action_quit(self) -> None:
        self.app.exit()

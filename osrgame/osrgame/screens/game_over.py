"""Game over screen displayed on total party kill."""

from textual import on
from textual.app import ComposeResult
from textual.containers import Center, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Static


class GameOverScreen(Screen):
    """TPK screen with Load/Quit options."""

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Center():
            with Vertical(id="game-over-container"):
                yield Static(
                    "GAME OVER\n\nYour party has been slain...",
                    id="game-over-text",
                )
                with Center():
                    with Vertical():
                        yield Button(
                            "Load saved game", id="btn-load", variant="primary"
                        )
                        yield Button("Quit", id="btn-quit")
        yield Footer()

    @on(Button.Pressed, "#btn-load")
    def load_game(self) -> None:
        # Pop back to main menu for now
        while len(self.app.screen_stack) > 1:
            self.app.pop_screen()

    @on(Button.Pressed, "#btn-quit")
    def quit_game(self) -> None:
        self.app.exit()

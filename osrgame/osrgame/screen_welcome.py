from textual.screen import Screen
from textual.app import ComposeResult
from textual.widgets import Header, Footer, Button


class WelcomeScreen(Screen):
    BINDINGS = [
        ("escape", "app.pop_screen", "Pop screen"),
        ("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True, id="header")

        yield Footer()

    def on_mount(self) -> None:
        pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        pass

    def action_quit(self) -> None:
        """An action to quit the application."""
        self.exit()

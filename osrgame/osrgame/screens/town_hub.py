"""Town hub screen with 6 location buttons and Depart."""

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Static

from ..widgets import PartyRosterWidget


class TownHubScreen(Screen):
    """Town hub with Training hall, Temple, Shop, Tavern, Inn, and Depart."""

    BINDINGS = [
        ("d", "depart", "Depart"),
        ("escape", "app.pop_screen", "Back"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="town-layout"):
            with Vertical(id="town-left"):
                yield Static("Welcome to town", id="town-title")
                with Vertical(id="town-grid"):
                    yield Button("Training hall", id="btn-training")
                    yield Button("Temple", id="btn-temple")
                    yield Button("Shop", id="btn-shop")
                    yield Button("Tavern", id="btn-tavern")
                    yield Button("Inn", id="btn-inn")
                    yield Button("Depart", id="btn-depart", variant="warning")
            yield PartyRosterWidget(id="town-roster")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#town-roster", PartyRosterWidget).refresh_roster()

    @on(Button.Pressed, "#btn-training")
    def go_training(self) -> None:
        from .town_training import TrainingHallScreen

        self.app.push_screen(TrainingHallScreen(), callback=self._on_return)

    def _on_return(self, result=None) -> None:
        """Refresh roster when returning from sub-screens."""
        self.query_one("#town-roster", PartyRosterWidget).refresh_roster()

    @on(Button.Pressed, "#btn-temple")
    def go_temple(self) -> None:
        self.notify("Temple coming soon", title="Temple")

    @on(Button.Pressed, "#btn-shop")
    def go_shop(self) -> None:
        self.notify("Shop coming soon", title="Shop")

    @on(Button.Pressed, "#btn-tavern")
    def go_tavern(self) -> None:
        self.notify("Tavern coming soon", title="Tavern")

    @on(Button.Pressed, "#btn-inn")
    def go_inn(self) -> None:
        self.notify("Inn coming soon", title="Inn")

    @on(Button.Pressed, "#btn-depart")
    def depart(self) -> None:
        self.action_depart()

    def action_depart(self) -> None:
        """Leave town and enter the dungeon."""
        from .explore import ExploreScreen

        gs = self.app.game_state
        if gs.adventure is None:
            self.notify("No adventure loaded", severity="error")
            return

        gs.in_dungeon = True

        # Move party to start location if not already placed
        dungeon = gs.adventure.active_dungeon
        if dungeon.current_party_location is None:
            dungeon.set_start_location(1)

        self.app.push_screen(ExploreScreen())

"""Camping screen for resting, watch order, and camp management."""

from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Log

from osrlib.dice_roller import roll_dice
from osrlib.encounter import Encounter

from ..widgets import PartyRosterWidget


class CampingScreen(Screen):
    """Rest, set watch order, and manage camp activities."""

    BINDINGS = [
        ("escape", "break_camp", "Break camp"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(id="camp-left"):
            yield PartyRosterWidget(id="camp-roster")
            yield Log(id="camp-log", auto_scroll=True)
        with Vertical(id="camp-right"):
            yield Button("Rest", id="btn-rest", variant="primary")
            yield Button("Watch order", id="btn-watch")
            yield Button("Memorize spells", id="btn-spells", disabled=True)
            yield Button("Break camp", id="btn-break-camp")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#camp-roster", PartyRosterWidget).refresh_roster()
        log = self.query_one("#camp-log", Log)
        log.border_title = "Camp log"
        log.write_line("The party makes camp.")

    @on(Button.Pressed, "#btn-rest")
    def rest(self) -> None:
        """Rest the party with a 1-in-6 chance of wandering monster interruption."""
        log = self.query_one("#camp-log", Log)

        # Wandering monster check
        roll = roll_dice("1d6")
        if roll.total == 1:
            log.write_line("The camp is attacked during the night!")
            encounter = Encounter.get_random_encounter(1)
            self.dismiss({"interrupted": True, "encounter": encounter})
            return

        # Successful rest — heal party
        gs = self.app.game_state
        party = gs.adventure.active_party
        party.heal_party()
        gs.turn_count += 6

        log.write_line("The party rests peacefully. HP restored.")
        self.query_one("#camp-roster", PartyRosterWidget).refresh_roster()

    @on(Button.Pressed, "#btn-watch")
    def set_watch_order(self) -> None:
        """Push the party manager to reorder the party."""
        from .party_manager import PartyManagerScreen

        self.app.push_screen(PartyManagerScreen(), callback=self._on_watch_return)

    def _on_watch_return(self, result=None) -> None:
        """Refresh roster when returning from watch order."""
        self.query_one("#camp-roster", PartyRosterWidget).refresh_roster()
        log = self.query_one("#camp-log", Log)
        log.write_line("Watch order updated.")

    @on(Button.Pressed, "#btn-break-camp")
    def break_camp(self) -> None:
        self.action_break_camp()

    def action_break_camp(self) -> None:
        """Break camp and return to exploration."""
        self.dismiss({"rested": True, "interrupted": False})

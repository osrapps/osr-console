"""Training hall screen — create characters, level up, manage party order."""

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Static

from ..widgets import CharSheetWidget, PartyRosterWidget


class TrainingHallScreen(Screen):
    """Training hall: create new characters, level up, manage marching order."""

    BINDINGS = [
        ("escape", "done", "Done"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static("Training hall", id="town-title", classes="gold-heading")
        with Horizontal(id="training-layout"):
            with Vertical(id="training-left"):
                yield PartyRosterWidget(id="training-roster")
                with Horizontal(id="training-actions"):
                    yield Button(
                        "Create character", id="btn-create-char", variant="primary"
                    )
                    yield Button("Level up", id="btn-level-up")
                    yield Button("Manage party", id="btn-manage-order")
                    yield Button("Done", id="btn-done")
            yield CharSheetWidget(id="training-sheet")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#training-roster", PartyRosterWidget).refresh_roster()

    @on(Button.Pressed, "#btn-create-char")
    def create_character(self) -> None:
        from .char_creation import CharCreationScreen

        self.app.push_screen(CharCreationScreen(), callback=self._on_char_created)

    def _on_char_created(self, pc) -> None:
        """Callback when character creation finishes."""
        if pc is None:
            return
        gs = self.app.game_state
        party = gs.adventure.active_party
        try:
            party.add_character(pc)
            self.notify(f"{pc.name} joined the party!", title="New recruit")
        except Exception as e:
            self.notify(str(e), severity="error")
        self.query_one("#training-roster", PartyRosterWidget).refresh_roster()

    @on(Button.Pressed, "#btn-level-up")
    def level_up(self) -> None:
        from .level_up import LevelUpScreen

        gs = self.app.game_state
        party = gs.adventure.active_party
        # Find first character eligible for level up
        for pc in party.members:
            if pc.xp >= pc.xp_needed_for_next_level:
                self.app.push_screen(LevelUpScreen(pc), callback=self._on_level_up_done)
                return
        self.notify("No characters are eligible for level up.", title="Training hall")

    def _on_level_up_done(self, result) -> None:
        self.query_one("#training-roster", PartyRosterWidget).refresh_roster()

    @on(Button.Pressed, "#btn-manage-order")
    def manage_order(self) -> None:
        from .party_manager import PartyManagerScreen

        self.app.push_screen(PartyManagerScreen(), callback=self._on_manage_return)

    def _on_manage_return(self, result=None) -> None:
        """Refresh roster when returning from party manager (character may have been dropped)."""
        self.query_one("#training-roster", PartyRosterWidget).refresh_roster()

    @on(Button.Pressed, "#btn-done")
    def done(self) -> None:
        self.action_done()

    def action_done(self) -> None:
        self.app.pop_screen()

    def on_data_table_row_selected(self, event) -> None:
        """Show character sheet when a roster row is selected."""
        event.stop()
        gs = self.app.game_state
        party = gs.adventure.active_party
        if event.cursor_row < len(party.members):
            pc = party.members[event.cursor_row]
            self.query_one("#training-sheet", CharSheetWidget).update_character(pc)

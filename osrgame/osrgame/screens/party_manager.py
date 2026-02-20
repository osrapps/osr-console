"""Party manager screen for viewing, reordering, and managing party members."""

from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Static

from ..widgets import PartyRosterWidget


class PartyManagerScreen(Screen):
    """View party members, reorder, and manage the roster."""

    BINDINGS = [
        ("escape", "done", "Done"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield PartyRosterWidget(id="party-mgr-roster")
        yield Vertical(
            Static(
                "Party manager — select a character to view details",
                classes="gold-heading",
            ),
            id="party-mgr-details",
        )
        with Vertical(id="party-mgr-actions"):
            yield Button("Done", id="btn-done", variant="primary")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#party-mgr-roster", PartyRosterWidget).refresh_roster()

    @on(Button.Pressed, "#btn-done")
    def done(self) -> None:
        self.action_done()

    def action_done(self) -> None:
        self.app.pop_screen()

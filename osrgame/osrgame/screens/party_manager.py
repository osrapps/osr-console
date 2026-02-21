"""Party manager screen for viewing, reordering, and managing party members."""

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Static

from ..widgets import CharSheetWidget, PartyRosterWidget
from .confirm_modal import ConfirmModal


class PartyManagerScreen(Screen):
    """View party members, reorder marching order, and drop characters."""

    BINDINGS = [
        ("escape", "done", "Done"),
    ]

    def __init__(self, allow_drop: bool = True, **kwargs) -> None:
        super().__init__(**kwargs)
        self._allow_drop = allow_drop
        self._selected_index: int | None = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static("Party manager", id="town-title", classes="gold-heading")
        with Horizontal(id="party-mgr-layout"):
            with Vertical(id="party-mgr-left"):
                yield PartyRosterWidget(id="party-mgr-roster")
                with Horizontal(id="party-mgr-actions"):
                    yield Button("Move up", id="btn-move-up", disabled=True)
                    yield Button("Move down", id="btn-move-down", disabled=True)
                    if self._allow_drop:
                        yield Button(
                            "Drop character",
                            id="btn-drop-char",
                            variant="error",
                            disabled=True,
                        )
                    yield Button("Done", id="btn-done", variant="primary")
            yield CharSheetWidget(id="party-mgr-sheet")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#party-mgr-roster", PartyRosterWidget).refresh_roster()

    def _get_party_members(self) -> list:
        return self.app.game_state.adventure.active_party.members

    def _update_button_states(self) -> None:
        """Enable/disable buttons based on current selection."""
        members = self._get_party_members()
        has_selection = self._selected_index is not None
        count = len(members)

        self.query_one("#btn-move-up", Button).disabled = (
            not has_selection or self._selected_index == 0
        )
        self.query_one("#btn-move-down", Button).disabled = (
            not has_selection or self._selected_index == count - 1
        )
        drop_btn = self.query_one_optional("#btn-drop-char", Button)
        if drop_btn is not None:
            drop_btn.disabled = not has_selection

    def on_data_table_row_selected(self, event) -> None:
        """Show character sheet when a roster row is clicked."""
        event.stop()
        members = self._get_party_members()
        if event.cursor_row < len(members):
            self._selected_index = event.cursor_row
            pc = members[self._selected_index]
            self.query_one("#party-mgr-sheet", CharSheetWidget).update_character(pc)
            self._update_button_states()

    @on(Button.Pressed, "#btn-move-up")
    def move_up(self) -> None:
        if self._selected_index is None or self._selected_index == 0:
            return
        party = self.app.game_state.adventure.active_party
        pc = party.members[self._selected_index]
        new_index = self._selected_index - 1
        party.move_character_to_index(pc, new_index)
        self._selected_index = new_index
        roster = self.query_one("#party-mgr-roster", PartyRosterWidget)
        roster.refresh_roster()
        roster.move_cursor(row=new_index)
        self._update_button_states()

    @on(Button.Pressed, "#btn-move-down")
    def move_down(self) -> None:
        members = self._get_party_members()
        if self._selected_index is None or self._selected_index >= len(members) - 1:
            return
        party = self.app.game_state.adventure.active_party
        pc = party.members[self._selected_index]
        new_index = self._selected_index + 1
        party.move_character_to_index(pc, new_index)
        self._selected_index = new_index
        roster = self.query_one("#party-mgr-roster", PartyRosterWidget)
        roster.refresh_roster()
        roster.move_cursor(row=new_index)
        self._update_button_states()

    @on(Button.Pressed, "#btn-drop-char")
    def drop_character(self) -> None:
        if self._selected_index is None:
            return
        pc = self._get_party_members()[self._selected_index]
        self.app.push_screen(
            ConfirmModal(
                f"Permanently remove {pc.name} from the party? This cannot be undone.",
                title="Drop character",
            ),
            callback=self._on_drop_confirmed,
        )

    def _on_drop_confirmed(self, confirmed: bool) -> None:
        if not confirmed or self._selected_index is None:
            return
        party = self.app.game_state.adventure.active_party
        pc = party.members[self._selected_index]
        name = pc.name
        party.remove_character(pc)
        self.notify(f"{name} has been removed from the party.", title="Character dropped")
        self._selected_index = None
        self.query_one("#party-mgr-roster", PartyRosterWidget).refresh_roster()
        self.query_one("#party-mgr-sheet", CharSheetWidget).update_character(None)
        self._update_button_states()

    @on(Button.Pressed, "#btn-done")
    def done(self) -> None:
        self.action_done()

    def action_done(self) -> None:
        self.dismiss()

"""Temple screen — heal wounds, raise dead."""

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, DataTable, Footer, Header, Static

from ..widgets import PartyRosterWidget


class TempleScreen(Screen):
    """Temple: heal characters and raise the dead."""

    BINDINGS = [
        ("escape", "done", "Done"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static("Temple", id="town-title", classes="gold-heading")
        with Horizontal(id="temple-layout"):
            with Vertical(id="temple-left"):
                yield PartyRosterWidget(id="temple-roster")
                yield Static("Gold: 0", id="temple-gold")
            with Vertical(id="temple-right"):
                yield Static("Select a character to see available services.", id="temple-info")
                with Vertical(id="temple-services"):
                    yield Button("Heal wounds (1 gp/HP)", id="btn-heal", disabled=True)
                    yield Button("Heal all (1 gp/HP)", id="btn-heal-all")
                    yield Button("Raise dead (500 gp)", id="btn-raise", disabled=True)
                    yield Button("Cure poison", id="btn-cure-poison", disabled=True)
                    yield Button("Cure disease", id="btn-cure-disease", disabled=True)
                    yield Button("Remove curse", id="btn-remove-curse", disabled=True)
                    yield Button("Done", id="btn-done")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#temple-roster", PartyRosterWidget).refresh_roster()
        self._refresh_gold()
        # Disable stub service buttons with tooltip
        for btn_id in ("#btn-cure-poison", "#btn-cure-disease", "#btn-remove-curse"):
            btn = self.query_one(btn_id, Button)
            btn.tooltip = "Not yet available"
        self._selected_pc = None

    def _refresh_gold(self) -> None:
        party = self.app.game_state.adventure.active_party
        self.query_one("#temple-gold", Static).update(f"Gold: {party.treasury.gold}")

    def _refresh_info(self) -> None:
        pc = self._selected_pc
        if pc is None:
            self.query_one("#temple-info", Static).update("Select a character to see available services.")
            self.query_one("#btn-heal", Button).disabled = True
            return

        if not pc.is_alive:
            info = f"{pc.name} is dead."
            self.query_one("#btn-heal", Button).disabled = True
        else:
            missing = pc.character_class.max_hp - pc.character_class.hp
            if missing > 0:
                info = f"{pc.name}: {pc.character_class.hp}/{pc.character_class.max_hp} HP (heal cost: {missing} gp)"
                self.query_one("#btn-heal", Button).disabled = False
            else:
                info = f"{pc.name}: Full health ({pc.character_class.hp}/{pc.character_class.max_hp} HP)"
                self.query_one("#btn-heal", Button).disabled = True
        self.query_one("#temple-info", Static).update(info)

    def _check_raise_button(self) -> None:
        party = self.app.game_state.adventure.active_party
        has_dead = any(not pc.is_alive for pc in party.members)
        self.query_one("#btn-raise", Button).disabled = not has_dead

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        event.stop()
        party = self.app.game_state.adventure.active_party
        if event.cursor_row < len(party.members):
            self._selected_pc = party.members[event.cursor_row]
            self._refresh_info()
            self._check_raise_button()

    @on(Button.Pressed, "#btn-heal")
    def heal_selected(self) -> None:
        pc = self._selected_pc
        if pc is None or not pc.is_alive:
            return
        party = self.app.game_state.adventure.active_party
        missing = pc.character_class.max_hp - pc.character_class.hp
        if missing <= 0:
            self.notify(f"{pc.name} is already at full health.", title="Temple")
            return
        if not party.treasury.spend_gold(missing):
            self.notify("Not enough gold.", severity="error", title="Temple")
            return
        pc.heal(missing)
        self.notify(f"Healed {pc.name} for {missing} HP.", title="Temple")
        self._refresh_gold()
        self._refresh_info()
        self.query_one("#temple-roster", PartyRosterWidget).refresh_roster()

    @on(Button.Pressed, "#btn-heal-all")
    def heal_all(self) -> None:
        party = self.app.game_state.adventure.active_party
        total_cost = 0
        for pc in party.members:
            if pc.is_alive:
                total_cost += pc.character_class.max_hp - pc.character_class.hp
        if total_cost <= 0:
            self.notify("Everyone is at full health.", title="Temple")
            return
        if not party.treasury.spend_gold(total_cost):
            self.notify(f"Not enough gold (need {total_cost} gp).", severity="error", title="Temple")
            return
        for pc in party.members:
            if pc.is_alive:
                missing = pc.character_class.max_hp - pc.character_class.hp
                pc.heal(missing)
        self.notify(f"Healed all living members for {total_cost} gp.", title="Temple")
        self._refresh_gold()
        self._refresh_info()
        self.query_one("#temple-roster", PartyRosterWidget).refresh_roster()

    @on(Button.Pressed, "#btn-raise")
    def raise_dead(self) -> None:
        party = self.app.game_state.adventure.active_party
        # Raise the first dead member found
        dead_pc = next((pc for pc in party.members if not pc.is_alive), None)
        if dead_pc is None:
            self.notify("No dead party members.", title="Temple")
            return
        if not party.treasury.spend_gold(500):
            self.notify("Not enough gold (need 500 gp).", severity="error", title="Temple")
            return
        # TODO: Add a PlayerCharacter.resurrect() method instead of
        # directly setting hp. The hp = 0 assignment bypasses heal()
        # and any future side effects (logging, events, etc.).
        dead_pc.character_class.hp = 0
        dead_pc.heal(1)
        self.notify(f"{dead_pc.name} has been raised from the dead!", title="Temple")
        self._refresh_gold()
        self._refresh_info()
        self._check_raise_button()
        self.query_one("#temple-roster", PartyRosterWidget).refresh_roster()

    @on(Button.Pressed, "#btn-done")
    def done(self) -> None:
        self.action_done()

    def action_done(self) -> None:
        self.dismiss()

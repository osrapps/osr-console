"""Interactive combat screen using the CombatEngine in manual mode."""

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Label, Log, OptionList
from textual.widgets.option_list import Option

from osrlib.combat import (
    CombatEngine,
    EncounterState,
    EventFormatter,
    NeedAction,
    VictoryDetermined,
)
from osrlib.combat.context import CombatSide
from osrlib.combat.intents import ActionIntent
from osrlib.combat.state import EncounterOutcome
from osrlib.encounter import Encounter
from osrlib.party import Party

from ..widgets import PartyRosterWidget


class CombatScreen(Screen):
    """Tactical combat driven by the state-machine CombatEngine in manual mode."""

    BINDINGS = [
        ("escape", "dismiss_screen", "End combat"),
    ]

    def __init__(
        self,
        encounter: Encounter,
        party: Party,
        name: str | None = None,
        id: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id)
        self.encounter = encounter
        self.party = party
        self.engine: CombatEngine | None = None
        self._formatter = EventFormatter()
        self._combat_ended = False
        self._outcome: EncounterOutcome | None = None
        self._pending_need_action: NeedAction | None = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield PartyRosterWidget(id="combat-party-roster")
        yield Log(id="combat-log", auto_scroll=True)
        yield DataTable(id="combat-monster-roster", cursor_type=None)
        yield Container(
            Label("Select a target:", id="target-prompt"),
            OptionList(id="target-menu"),
            id="combat-action-panel",
        )
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#combat-log", Log).border_title = "Combat log"
        self.query_one("#combat-party-roster").border_title = "Party"
        self.query_one("#target-prompt", Label).display = False
        self.query_one("#target-menu", OptionList).display = False

        # Set up monster roster table
        monster_table = self.query_one("#combat-monster-roster", DataTable)
        monster_table.add_columns("Monster", "HP", "Status")
        monster_table.border_title = "Monsters"

        # Update party roster
        self.query_one("#combat-party-roster", PartyRosterWidget).refresh_roster()

        # Create engine in manual mode
        self.engine = CombatEngine(
            pc_party=self.party,
            monster_party=self.encounter.monster_party,
            auto_resolve_intents=False,
        )
        self.encounter.pc_party = self.party
        self.encounter.engine = self.engine

        self.set_timer(0.1, self._advance_combat)

    def _advance_combat(self, intent: ActionIntent | None = None) -> None:
        """Core combat loop: advance engine, update UI, handle next decision point."""
        if self._combat_ended:
            return

        try:
            results = self.engine.step_until_decision(intent=intent)
        except Exception as exc:
            self._write_log(f"Combat error: {exc}")
            self._finish_combat(EncounterOutcome.FAULTED)
            return

        for result in results:
            for event in result.events:
                line = self._formatter.format(event)
                self._write_log(line)
                if isinstance(event, VictoryDetermined):
                    self._outcome = event.outcome

        self._refresh_rosters()

        if self.engine.state == EncounterState.ENDED:
            self._finish_combat(self._outcome or self.engine.outcome)
            return

        last_result = results[-1]
        if not last_result.needs_intent:
            return

        combatant_id = last_result.pending_combatant_id
        if combatant_id is None:
            return

        need_action = None
        for result in results:
            for event in result.events:
                if isinstance(event, NeedAction):
                    need_action = event

        if need_action is None:
            return

        self._pending_need_action = need_action
        self._show_target_menu(combatant_id, need_action)

    def _show_target_menu(self, combatant_id: str, need_action: NeedAction) -> None:
        """Populate and display the target OptionList for a PC's turn."""
        option_list = self.query_one("#target-menu", OptionList)
        option_list.clear_options()

        pc_name = combatant_id.split(":", 1)[1] if ":" in combatant_id else combatant_id
        prompt = self.query_one("#target-prompt", Label)
        prompt.update(f"{pc_name}'s turn — select an action:")
        prompt.display = True

        for i, choice in enumerate(need_action.available):
            option_list.add_option(Option(choice.label, id=str(i)))

        option_list.display = True
        option_list.focus()

    def _hide_target_menu(self) -> None:
        self.query_one("#target-prompt", Label).display = False
        self.query_one("#target-menu", OptionList).display = False

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        event.stop()
        if self._pending_need_action is None or self._combat_ended:
            return

        idx = int(event.option_id)
        choices = self._pending_need_action.available
        if idx >= len(choices):
            return

        chosen_intent = choices[idx].intent
        self._pending_need_action = None
        self._hide_target_menu()
        self.set_timer(0.05, lambda: self._advance_combat(intent=chosen_intent))

    def _finish_combat(self, outcome: EncounterOutcome | None) -> None:
        self._combat_ended = True
        self._outcome = outcome
        self._hide_target_menu()

        if outcome == EncounterOutcome.PARTY_VICTORY:
            self._write_log("")
            self._write_log("*** Victory! Press Escape to continue. ***")
        elif outcome == EncounterOutcome.OPPOSITION_VICTORY:
            self._write_log("")
            self._write_log("*** Defeat... Press Escape to continue. ***")
        else:
            self._write_log("")
            self._write_log("*** Combat ended. Press Escape to continue. ***")

    def _write_log(self, text: str) -> None:
        self.query_one("#combat-log", Log).write_line(text)
        self.encounter.log_mesg(text)

    def _refresh_rosters(self) -> None:
        self.query_one("#combat-party-roster", PartyRosterWidget).refresh_roster()
        view = self.engine.get_view()
        monster_table = self.query_one("#combat-monster-roster", DataTable)
        monster_table.clear()
        for c in view.combatants:
            if c.side != CombatSide.MONSTER:
                continue
            hp_text = str(c.hp) if c.is_alive else "0"
            status = (
                "Dead" if c.id in view.announced_deaths or not c.is_alive else "Alive"
            )
            monster_table.add_row(
                c.name,
                Text(hp_text, justify="center"),
                Text(status, justify="center"),
                key=c.id,
            )

    def action_dismiss_screen(self) -> None:
        if not self._combat_ended:
            return
        self.dismiss({"outcome": self._outcome, "encounter": self.encounter})

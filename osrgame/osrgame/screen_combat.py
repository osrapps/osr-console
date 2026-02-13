"""Bard's Tale-style interactive combat screen."""

import random

from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Footer, Header, Label, Log, OptionList
from textual.widgets.option_list import Option

from osrlib.combat import (
    CombatEngine,
    CombatSide,
    EncounterState,
    EventFormatter,
    NeedAction,
    VictoryDetermined,
)
from osrlib.combat.intents import ActionIntent
from osrlib.combat.state import EncounterOutcome
from osrlib.encounter import Encounter
from osrlib.party import Party

from .widgets import MonsterRosterTable, PartyRosterTable


class CombatScreen(Screen):
    """Interactive combat screen driven by the state-machine CombatEngine in manual mode."""

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
        yield PartyRosterTable(id="combat_party_table", classes="box")
        yield Log(id="combat_log", auto_scroll=True, classes="box")
        yield MonsterRosterTable(id="monster_roster", classes="box")
        yield Container(
            Label("Select a target:", id="target_prompt"),
            OptionList(id="target_menu"),
            id="action_panel",
        )
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#combat_log", Log).border_title = "Combat log"
        self.query_one("#combat_party_table", PartyRosterTable).border_title = "Party"
        self.query_one("#monster_roster", MonsterRosterTable).border_title = "Monsters"
        self.query_one("#target_prompt", Label).display = False
        self.query_one("#target_menu", OptionList).display = False

        # Update party roster
        self.query_one("#combat_party_table", PartyRosterTable).update_table()

        # Create engine in manual mode
        self.engine = CombatEngine(
            pc_party=self.party,
            monster_party=self.encounter.monster_party,
            auto_resolve_intents=False,
        )

        # Set pc_party so end_encounter() can award XP/treasure
        self.encounter.pc_party = self.party

        # Store engine on encounter so the TUI callback can access the log
        self.encounter.engine = self.engine

        # Kick off combat after first render
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

        # Format and display all events from this batch
        for result in results:
            for event in result.events:
                line = self._formatter.format(event)
                self._write_log(line)

                if isinstance(event, VictoryDetermined):
                    self._outcome = event.outcome

        # Update rosters after each batch
        self._refresh_rosters()

        # Check terminal state
        if self.engine.state == EncounterState.ENDED:
            self._finish_combat(self._outcome or self.engine.outcome)
            return

        # Engine is awaiting intent — figure out whose turn it is
        last_result = results[-1]
        if not last_result.needs_intent:
            return

        combatant_id = last_result.pending_combatant_id
        if combatant_id is None:
            return

        # Find the NeedAction event to get available choices
        need_action = None
        for result in results:
            for event in result.events:
                if isinstance(event, NeedAction):
                    need_action = event

        if need_action is None:
            return

        # Determine side
        ref = self.engine._ctx.combatants.get(combatant_id)
        if ref is None:
            return

        if ref.side == CombatSide.MONSTER:
            # Auto-resolve monster turn: pick random living PC target
            choices = need_action.available
            if choices:
                chosen = random.choice(choices)
                # Use set_timer to let UI render between monster turns
                self.set_timer(0.05, lambda: self._advance_combat(intent=chosen.intent))
        else:
            # PC turn: show target selection
            self._pending_need_action = need_action
            self._show_target_menu(combatant_id, need_action)

    def _show_target_menu(self, combatant_id: str, need_action: NeedAction) -> None:
        """Populate and display the target OptionList for a PC's turn."""
        option_list = self.query_one("#target_menu", OptionList)
        option_list.clear_options()

        # Extract PC display name from combatant_id (format: "pc:Name")
        pc_name = combatant_id.split(":", 1)[1] if ":" in combatant_id else combatant_id

        prompt = self.query_one("#target_prompt", Label)
        prompt.update(f"{pc_name}'s turn - select a target:")
        prompt.display = True

        for i, choice in enumerate(need_action.available):
            option_list.add_option(Option(choice.label, id=str(i)))

        option_list.display = True
        option_list.focus()

    def _hide_target_menu(self) -> None:
        """Hide the target selection UI."""
        self.query_one("#target_prompt", Label).display = False
        self.query_one("#target_menu", OptionList).display = False

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle player selecting a target from the option list."""
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

        # Advance combat with the chosen intent
        self.set_timer(0.05, lambda: self._advance_combat(intent=chosen_intent))

    def _finish_combat(self, outcome: EncounterOutcome | None) -> None:
        """Show outcome and prepare for dismissal."""
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
        """Write a line to the combat log."""
        self.query_one("#combat_log", Log).write_line(text)
        # Also record in encounter log for summarize_battle()
        self.encounter.log_mesg(text)

    def _refresh_rosters(self) -> None:
        """Update party and monster roster tables from current engine state."""
        self.query_one("#combat_party_table", PartyRosterTable).update_table()
        self.query_one("#monster_roster", MonsterRosterTable).update_table(
            self.engine._ctx.combatants,
            self.engine._ctx.announced_deaths,
        )

    def action_dismiss_screen(self) -> None:
        """Dismiss the combat screen, returning outcome data."""
        if not self._combat_ended:
            # Don't allow dismissing mid-combat
            return
        self.dismiss(
            {
                "outcome": self._outcome,
                "encounter": self.encounter,
            }
        )

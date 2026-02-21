"""Bard's Tale-style combat screen with per-character action cycling."""

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Footer, Header, RichLog

from osrlib.combat import (
    ColorEventFormatter,
    CombatEngine,
    EncounterState,
    NeedAction,
    VictoryDetermined,
)
from osrlib.combat.intents import ActionIntent
from osrlib.combat.state import EncounterOutcome
from osrlib.encounter import Encounter
from osrlib.party import Party

from ..widgets import PartyRosterWidget
from ..widgets.combat_action_bar import CombatActionBar, CombatActionChosen
from ..widgets.monster_group import MonsterGroupWidget


class CombatScreen(Screen):
    """Bard's Tale-style combat with per-character action cycling.

    Layout: 3-column top (party | combat log | monsters) + full-width action bar.
    """

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
        self._formatter = ColorEventFormatter()
        self._combat_ended = False
        self._outcome: EncounterOutcome | None = None
        self._pending_need_action: NeedAction | None = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Container(
            PartyRosterWidget(id="combat-party-roster"),
            RichLog(id="combat-log", auto_scroll=True, wrap=True, markup=True),
            MonsterGroupWidget(id="combat-monster-roster"),
            id="combat-top",
        )
        yield CombatActionBar(id="combat-action-bar")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#combat-log", RichLog).border_title = "Combat log"
        self.query_one("#combat-party-roster", PartyRosterWidget).border_title = "Party"
        self.query_one(
            "#combat-monster-roster", MonsterGroupWidget
        ).border_title = "Monsters"

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
            self._write_log(Text(f"Combat error: {exc}", style="bold red"))
            self._finish_combat(EncounterOutcome.FAULTED)
            return

        for result in results:
            for event in result.events:
                styled = self._formatter.format(event)
                self._write_log(styled)
                # Also log plain text to encounter log
                self.encounter.log_mesg(self._formatter.format_plain(event))
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
        self._show_action_bar(combatant_id, need_action)

    def _show_action_bar(self, combatant_id: str, need_action: NeedAction) -> None:
        """Configure the action bar for a PC's turn."""
        action_bar = self.query_one("#combat-action-bar", CombatActionBar)
        action_bar.set_need_action(need_action)

        # Highlight active PC in roster
        roster = self.query_one("#combat-party-roster", PartyRosterWidget)
        roster.highlight_pc(combatant_id)

        action_bar.focus()

    def _hide_action_bar(self) -> None:
        action_bar = self.query_one("#combat-action-bar", CombatActionBar)
        action_bar.clear_action()

    def on_combat_action_chosen(self, event: CombatActionChosen) -> None:
        """Handle the CombatActionChosen message from the action bar."""
        event.stop()
        if self._pending_need_action is None or self._combat_ended:
            return

        chosen_intent = event.intent
        self._pending_need_action = None
        self._hide_action_bar()
        self.set_timer(0.05, lambda: self._advance_combat(intent=chosen_intent))

    def _finish_combat(self, outcome: EncounterOutcome | None) -> None:
        self._combat_ended = True
        self._outcome = outcome
        self._hide_action_bar()

        log = self.query_one("#combat-log", RichLog)
        log.write(Text(""))
        if outcome == EncounterOutcome.PARTY_VICTORY:
            log.write(
                Text("*** Victory! Press Escape to continue. ***", style="bold green")
            )
        elif outcome == EncounterOutcome.OPPOSITION_VICTORY:
            log.write(
                Text("*** Defeat... Press Escape to continue. ***", style="bold red")
            )
        else:
            log.write(
                Text(
                    "*** Combat ended. Press Escape to continue. ***",
                    style="bold yellow",
                )
            )

    def _write_log(self, text: Text) -> None:
        self.query_one("#combat-log", RichLog).write(text)

    def _refresh_rosters(self) -> None:
        self.query_one("#combat-party-roster", PartyRosterWidget).refresh_roster()
        view = self.engine.get_view()
        self.query_one("#combat-monster-roster", MonsterGroupWidget).refresh_from_view(
            view
        )

    def action_dismiss_screen(self) -> None:
        if not self._combat_ended:
            return
        self.dismiss({"outcome": self._outcome, "encounter": self.encounter})

"""Dungeon exploration screen with map, party roster, narrative, and commands."""

from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Footer, Header, Log, Static

from osrlib.dungeon import Direction

from ..widgets import PartyRosterWidget


class ExploreScreen(Screen):
    """Dungeon exploration with movement, encounters, and camping."""

    BINDINGS = [
        ("n", "move('NORTH')", "North"),
        ("s", "move('SOUTH')", "South"),
        ("e", "move('EAST')", "East"),
        ("w", "move('WEST')", "West"),
        ("u", "move('UP')", "Up"),
        ("d", "move('DOWN')", "Down"),
        ("c", "camp", "Camp"),
        ("t", "return_to_town", "Town"),
        ("escape", "return_to_town", "Town"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Container(
            Static("Map placeholder", classes="gold-heading"),
            id="explore-map",
        )
        yield PartyRosterWidget(id="explore-roster")
        yield Log(id="explore-narrative", auto_scroll=True)
        yield Static(
            " [N]orth  [S]outh  [E]ast  [W]est  [U]p  [D]own  |  [C]amp  [T]own",
            id="explore-commands",
        )
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#explore-roster", PartyRosterWidget).refresh_roster()
        narrative = self.query_one("#explore-narrative", Log)
        narrative.border_title = "Adventure log"

        gs = self.app.game_state
        dungeon = gs.adventure.active_dungeon
        loc = dungeon.current_party_location
        if loc is not None:
            self._describe_location(loc)

    def action_move(self, direction_name: str) -> None:
        """Move the party in the given direction."""
        gs = self.app.game_state
        dungeon = gs.adventure.active_dungeon
        loc = dungeon.current_party_location
        direction = Direction[direction_name]

        # Check if exit exists
        exit_obj = loc.get_exit(direction)
        if exit_obj is None:
            self._log(f"No exit to the {direction.value.lower()}.")
            return

        try:
            new_loc = dungeon.move(direction)
        except Exception as exc:
            self._log(f"Can't go that way: {exc}")
            return

        gs.turn_count += 1
        self._log(f"> Move {direction.value.lower()}")
        self._describe_location(new_loc)
        self.query_one("#explore-roster", PartyRosterWidget).refresh_roster()

        # Check for encounter
        self._check_encounter(new_loc)

    def _describe_location(self, loc) -> None:
        """Write location info to the narrative log."""
        exits = ", ".join(e.direction.value for e in loc.exits)
        self._log(f"Location {loc.id} — Exits: {exits}")
        if loc.keywords:
            self._log(f"  {', '.join(loc.keywords)}")

    def _check_encounter(self, loc) -> None:
        """If the location has an active encounter, push the combat screen."""
        if not loc.encounter or loc.encounter.is_ended:
            return

        encounter = loc.encounter
        if encounter.monster_party and len(encounter.monster_party.members) > 0:
            self._log(f"Encounter: {encounter.monster_party}")
            self._push_combat(encounter)

    def _push_combat(self, encounter) -> None:
        """Push the combat screen for this encounter."""
        from .combat import CombatScreen

        party = self.app.game_state.adventure.active_party
        self.app.push_screen(
            CombatScreen(encounter=encounter, party=party),
            callback=self._on_combat_ended,
        )

    def _on_combat_ended(self, result: dict | None) -> None:
        """Handle combat screen dismissal."""
        if result is None:
            self.query_one("#explore-roster", PartyRosterWidget).refresh_roster()
            return

        encounter = result.get("encounter")
        if encounter is not None:
            encounter.end_encounter()
            self._log("Combat ended. XP and treasure awarded.")

        self.query_one("#explore-roster", PartyRosterWidget).refresh_roster()

    def action_camp(self) -> None:
        self._log("The party rests... (camping coming soon)")
        gs = self.app.game_state
        if gs.adventure and gs.adventure.active_party:
            gs.adventure.active_party.heal_party()
            self.query_one("#explore-roster", PartyRosterWidget).refresh_roster()
            self._log("Party healed.")

    def action_return_to_town(self) -> None:
        """Return to the town hub."""
        gs = self.app.game_state
        gs.in_dungeon = False
        self.app.pop_screen()

    def _log(self, text: str) -> None:
        self.query_one("#explore-narrative", Log).write_line(text)

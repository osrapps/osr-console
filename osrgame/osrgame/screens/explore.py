"""Dungeon exploration screen with map, party roster, narrative, and commands."""

from textual import on
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Button, Footer, Header

from osrlib.dice_roller import roll_dice
from osrlib.dungeon import Direction
from osrlib.encounter import Encounter

from ..widgets import CommandBar, DungeonMapWidget, NarrativePanel, PartyRosterWidget


def _pluralize_monster(name: str, count: int) -> str:
    """Return a properly pluralized monster encounter string."""
    if count == 1:
        return f"A {name} appears!"
    return f"{count} {name}s appear!"


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

    # Default dungeon level for encounter generation. Dungeon doesn't persist its
    # level yet, so this matches the get_random_dungeon(level=1) default.
    _DUNGEON_LEVEL = 1

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield DungeonMapWidget(id="explore-map")
        yield PartyRosterWidget(id="explore-roster")
        yield NarrativePanel(id="explore-narrative")
        yield CommandBar(id="explore-commands")
        yield Footer()

    def on_mount(self) -> None:
        gs = self.app.game_state
        dungeon = gs.adventure.active_dungeon
        loc = dungeon.current_party_location

        # Mark start location as visited
        if loc is not None:
            loc.is_visited = True
            self._narrate(f"Entering {dungeon.name}")
            self._narrate(dungeon.description)
            self._narrate("")
            self._describe_location(loc)

        self._refresh_map()
        self._refresh_roster()
        self._update_command_bar()

    def action_move(self, direction_name: str) -> None:
        """Move the party in the given direction."""
        gs = self.app.game_state
        dungeon = gs.adventure.active_dungeon
        loc = dungeon.current_party_location
        if loc is None:
            self._narrate("No current location.")
            return

        direction = Direction[direction_name]

        # Check if exit exists
        exit_obj = loc.get_exit(direction)
        if exit_obj is None:
            self._narrate(f"No exit to the {direction.value.lower()}.")
            return

        try:
            new_loc = dungeon.move(direction)
        except Exception as exc:
            self._narrate(f"Can't go that way: {exc}")
            return

        if new_loc is None:
            self._narrate("Can't go that way.")
            return

        first_visit = not new_loc.is_visited
        new_loc.is_visited = True

        gs.turn_count += 1
        self._narrate(f"> Move {direction.value.lower()}")
        self._describe_location(new_loc, detailed=first_visit)

        self._refresh_map()
        self._refresh_roster()
        self._update_command_bar()

        # Check for location encounter
        self._check_location_encounter(new_loc)

        # Check for wandering monsters every 2 turns
        if gs.turn_count % 2 == 0:
            self._check_wandering_monsters()

    def _describe_location(self, loc, detailed: bool = False) -> None:
        """Write location info to the narrative log."""
        exits_str = ", ".join(e.direction.value for e in loc.exits)
        if detailed:
            self._narrate(f"Location {loc.id} — Exits: {exits_str}")
            if loc.keywords:
                self._narrate(f"  {', '.join(loc.keywords)}")
        else:
            self._narrate(f"Location {loc.id} (visited) — Exits: {exits_str}")

    def _check_location_encounter(self, loc) -> None:
        """If the location has an active encounter with monsters, push combat."""
        if not loc.encounter or loc.encounter.is_ended:
            return

        encounter = loc.encounter
        if encounter.monster_party and len(encounter.monster_party.members) > 0:
            monster_name = encounter.monster_party.members[0].name
            count = len(encounter.monster_party.members)
            self._narrate(f"Encounter! {_pluralize_monster(monster_name, count)}")
            self._push_combat(encounter)

    def _check_wandering_monsters(self) -> None:
        """Roll 1d6; on a 1, generate a wandering monster encounter."""
        roll = roll_dice("1d6")
        if roll.total == 1:
            encounter = Encounter.get_random_encounter(self._DUNGEON_LEVEL)
            if encounter.monster_party and len(encounter.monster_party.members) > 0:
                monster_name = encounter.monster_party.members[0].name
                count = len(encounter.monster_party.members)
                self._narrate(
                    f"Wandering monsters! {_pluralize_monster(monster_name, count)}"
                )
                self._push_combat(encounter)

    def _push_combat(self, encounter: Encounter) -> None:
        """Push the combat screen for this encounter."""
        from .combat import CombatScreen

        party = self.app.game_state.adventure.active_party
        self.app.push_screen(
            CombatScreen(encounter=encounter, party=party),
            callback=self._on_combat_ended,
        )

    def _on_combat_ended(self, result: dict | None) -> None:
        """Handle combat screen dismissal."""
        gs = self.app.game_state
        party = gs.adventure.active_party

        if result is not None:
            encounter = result.get("encounter")
            if encounter is not None:
                encounter.end_encounter()
                self._narrate("Combat ended.")

        self._refresh_roster()
        self._refresh_map()
        self._update_command_bar()

        # Check for TPK
        if not party.is_alive:
            self._narrate("The party has been slain...")
            from .game_over import GameOverScreen

            self.app.push_screen(GameOverScreen())

    def action_camp(self) -> None:
        """Push the camping screen."""
        from .camping import CampingScreen

        self.app.push_screen(CampingScreen(), callback=self._on_camp_ended)

    def _on_camp_ended(self, result: dict | None) -> None:
        """Handle camping screen dismissal."""
        if result is None:
            self._refresh_roster()
            return

        if result.get("interrupted"):
            encounter = result.get("encounter")
            if encounter is not None:
                self._narrate("The camp is attacked!")
                self._push_combat(encounter)
        elif result.get("rested"):
            self._narrate("The party breaks camp, well rested.")

        self._refresh_roster()
        self._refresh_map()
        self._update_command_bar()

    def action_return_to_town(self) -> None:
        """Return to the town hub."""
        gs = self.app.game_state
        gs.in_dungeon = False
        self.app.pop_screen()

    # --- Button press handlers ---

    @on(Button.Pressed, "#btn-dir-north")
    def press_north(self) -> None:
        self.action_move("NORTH")

    @on(Button.Pressed, "#btn-dir-south")
    def press_south(self) -> None:
        self.action_move("SOUTH")

    @on(Button.Pressed, "#btn-dir-east")
    def press_east(self) -> None:
        self.action_move("EAST")

    @on(Button.Pressed, "#btn-dir-west")
    def press_west(self) -> None:
        self.action_move("WEST")

    @on(Button.Pressed, "#btn-dir-up")
    def press_up(self) -> None:
        self.action_move("UP")

    @on(Button.Pressed, "#btn-dir-down")
    def press_down(self) -> None:
        self.action_move("DOWN")

    @on(Button.Pressed, "#btn-camp")
    def press_camp(self) -> None:
        self.action_camp()

    @on(Button.Pressed, "#btn-town")
    def press_town(self) -> None:
        self.action_return_to_town()

    # --- Helper methods ---

    def _narrate(self, text: str) -> None:
        """Append text to the narrative panel."""
        self.query_one("#explore-narrative", NarrativePanel).write(text)

    def _refresh_map(self) -> None:
        """Redraw the dungeon map."""
        gs = self.app.game_state
        dungeon = gs.adventure.active_dungeon
        self.query_one("#explore-map", DungeonMapWidget).refresh_map(dungeon)

    def _refresh_roster(self) -> None:
        """Refresh the party roster table."""
        self.query_one("#explore-roster", PartyRosterWidget).refresh_roster()

    def _update_command_bar(self) -> None:
        """Update direction button states based on current location exits."""
        gs = self.app.game_state
        dungeon = gs.adventure.active_dungeon
        loc = dungeon.current_party_location
        if loc is not None:
            self.query_one("#explore-commands", CommandBar).update_exits(loc.exits)

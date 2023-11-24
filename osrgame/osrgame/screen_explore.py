from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Log, Placeholder

from osrlib.adventure import Adventure
from osrlib.dungeon_master import DungeonMaster
from osrlib.dungeon import Direction
from osrlib.utils import wrap_text

from widgets import PartyRosterTable


class ExploreScreen(Screen):
    BINDINGS = [
        ("b", "start_session", "Begin session"),
        ("n", "move_north", "North"),
        ("s", "move_south", "South"),
        ("e", "move_east", "East"),
        ("w", "move_west", "West"),
        ("k", "clear_logs", "Clear logs"),
        ("?", "summarize", "Summarize session"),
        ("ctrl+s", "save_game", "Save game"),
        ("ctrl+l", "load_game", "Load game"),
    ]

    dungeon_master = None
    save_path = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield PartyRosterTable(id="pc_party_table", classes="box")  # upper-left
        yield Log(id="dm_log", auto_scroll=True, classes="box")     # right (row-span=2)
        yield Log(id="player_log", auto_scroll=True, classes="box") # lower-left
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#player_log", Log).border_title = "Command Log"
        self.query_one("#dm_log", Log).border_title = "Adventure Log"
        self.query_one(PartyRosterTable).border_title = "Adventuring Party"
        self.query_one(PartyRosterTable).update_table()
        self.query_one("#dm_log", Log).write_line("Press 'b' to begin a new session.")
        self.dungeon_master = DungeonMaster(self.app.adventure)

    def perform_move_action(self, direction: Direction, log_message: str) -> None:
        """Move the party in the specified direction, execute battle (if any), and log the results."""

        self.query_one("#player_log").write_line("---")
        self.query_one("#player_log").write_line(log_message)

        dm_response = self.dungeon_master.move_party(direction)

        self.query_one("#dm_log").write_line("---")
        self.query_one("#dm_log").write_line("> " + str(self.dungeon_master.adventure.active_dungeon.current_location))
        self.query_one("#dm_log").write_line(wrap_text(dm_response))
        self.query_one("#dm_log").write_line(" ")

        self.check_for_encounter()

    def check_for_encounter(self) -> None:
        """Check for an encounter and execute battle if there are monsters in the encounter."""
        if self.dungeon_master.adventure.active_dungeon.current_location.encounter and not self.dungeon_master.adventure.active_dungeon.current_location.encounter.is_ended:
            encounter = self.dungeon_master.adventure.active_dungeon.current_location.encounter

            self.query_one("#dm_log").write_line("> Encounter!")

            # TODO: Check whether monsters were surprised, and if so, give the player a chance to flee.
            self.query_one("#player_log").write_line("Fight!")

            encounter.start_encounter(self.dungeon_master.adventure.active_party)
            encounter_log = encounter.get_encounter_log()
            dm_response = self.dungeon_master.summarize_battle(encounter_log)
            self.query_one("#dm_log").write_line(wrap_text(dm_response))
            self.query_one("#dm_log").write_line(" ")

            self.query_one("#pc_party_table").update_table()

    def action_start_session(self) -> None:
        """Start a new session."""

        player_log = self.query_one("#player_log")
        dm_log = self.query_one("#dm_log")

        dm_response = self.dungeon_master.start_session()

        # Move the party to the first location
        first_exit = self.dungeon_master.adventure.active_dungeon.get_location_by_id(1).exits[0]
        dm_response = self.dungeon_master.move_party(first_exit.direction)

        player_log.clear()
        player_log.write_line("The party stands ready.")
        dm_log.write_line("---")
        dm_log.write_line("> " + str(self.dungeon_master.adventure.active_dungeon.current_location))
        dm_log.write_line(wrap_text(dm_response))

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()

    def action_move_north(self) -> None:
        """Move the party north."""
        self.perform_move_action(Direction.NORTH, "Moving north...")

    def action_move_south(self) -> None:
        """Move the party south."""
        self.perform_move_action(Direction.SOUTH, "Moving south...")

    def action_move_east(self) -> None:
        """Move the party east."""
        self.perform_move_action(Direction.EAST, "Moving east...")

    def action_move_west(self) -> None:
        """Move the party west."""
        self.perform_move_action(Direction.WEST, "Moving west...")

    def action_move_up(self) -> None:
        """Move the party up."""
        self.perform_move_action(Direction.UP, "Climbing up the stairs...")

    def action_move_down(self) -> None:
        """Move the party down."""
        self.perform_move_action(Direction.DOWN, "Descending the stairs...")

    def action_clear_logs(self) -> None:
        """An action to clear the logs."""
        self.query_one("#player_log").clear()
        self.query_one("#dm_log").clear()

    def action_summarize(self) -> None:
        """An action to summarize the session."""
        self.query_one("#player_log").write_line("Summarizing session...")
        self.query_one("#player_log").write_line("===")
        formatted_message = self.dungeon_master.format_user_message("Please provide a journal entry for the adventurers that summarizes the locations they've seen and encounters they've had in this game session. Include only what the player characters in the adventuring party would know. Add a bulleted list at the end with number of locations visited, monsters killed, PCs killed, and total experience points earned.")
        dm_response = self.dungeon_master.player_message(formatted_message)
        self.query_one("#dm_log").write_line(wrap_text(dm_response))
        self.query_one("#dm_log").write_line("===")

    def action_save_game(self) -> None:
        """An action to save the game."""
        self.query_one("#player_log").write_line("> Save adventure")
        self.query_one("#player_log").write_line("---")
        self.query_one("#dm_log").write_line("> Saving adventure...")
        self.save_path = self.dungeon_master.adventure.save_adventure()
        self.query_one("#dm_log").write_line(f"Adventure {self.dungeon_master.adventure.name} saved to {self.save_path}.")
        self.query_one("#dm_log").write_line("===")

    def action_load_game(self) -> None:
        """An action to save the game."""
        self.query_one("#player_log").write_line("> Load adventure")
        self.query_one("#player_log").write_line("---")
        self.query_one("#dm_log").write_line("> Loading adventure...")
        if self.save_path is None:
            self.query_one("#dm_log").write_line("No save path found.")
        else:
            self.app.adventure = Adventure.load_adventure(self.save_path)
            loaded_adventure = Adventure.load_adventure(self.save_path)
            self.dungeon_master.adventure = loaded_adventure
            self.query_one("#dm_log").write_line(f"Adventure {loaded_adventure.name} loaded from {self.save_path}.")
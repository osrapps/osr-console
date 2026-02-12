from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Log

from osrlib.dungeon import Direction
from osrlib.utils import wrap_text

from .widgets import PartyRosterTable


class ExploreScreen(Screen):
    BINDINGS = [
        ("n", "move_north", "North"),
        ("s", "move_south", "South"),
        ("e", "move_east", "East"),
        ("w", "move_west", "West"),
        ("?", "summarize", "Describe location"),
        ("c", "character", "Character screen"),
        ("h", "heal_party", "Heal party"),
        ("ctrl+s", "save_game", "Save game"),
    ]

    dungeon_assistant = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield PartyRosterTable(id="pc_party_table", classes="box")  # upper-left
        yield Log(id="dm_log", auto_scroll=True, classes="box")  # right (row-span=2)
        yield Log(id="player_log", auto_scroll=True, classes="box")  # lower-left
        yield Footer()

    def on_mount(self) -> None:
        self.dungeon_assistant = self.app.dungeon_assistant
        self.query_one("#player_log", Log).border_title = "Command Log"
        self.query_one("#dm_log", Log).border_title = "Adventure Log"
        self.query_one(PartyRosterTable).border_title = "Adventuring Party"
        self.query_one(PartyRosterTable).update_table()
        self.action_summarize()

    def perform_move_action(self, direction: Direction, log_message: str) -> None:
        """Move the party in the specified direction, execute battle (if any), and log the results."""

        self.query_one("#player_log").write_line(log_message)

        dm_response = self.dungeon_assistant.move_party(direction)

        self.query_one("#dm_log").write_line(
            ""#"> " + str(self.dungeon_assistant.adventure.active_dungeon.current_party_location)
        )
        self.query_one("#dm_log").write_line(wrap_text(dm_response))

        self.check_for_encounter()

    def check_for_encounter(self) -> None:
        """Check for an encounter and execute battle if there are monsters in the encounter."""
        if (
            self.dungeon_assistant.adventure.active_dungeon.current_party_location.encounter
            and not self.dungeon_assistant.adventure.active_dungeon.current_party_location.encounter.is_ended
        ):
            encounter = (
                self.dungeon_assistant.adventure.active_dungeon.current_party_location.encounter
            )

            if (
                encounter.monster_party is not None
                and len(encounter.monster_party.members) > 0
            ):
                self.query_one("#dm_log").write_line("> Encounter:")
                self.query_one("#dm_log").write_line(f"  {encounter.monster_party}".replace("\n", "\n  "))

                # TODO: Check whether monsters were surprised, and if so, give the player a chance to flee.
                self.query_one("#player_log").write_line("> Fight!")

            encounter.start_encounter(self.dungeon_assistant.adventure.active_party)
            encounter_log = encounter.get_encounter_log()
            dm_response = self.dungeon_assistant.summarize_battle(encounter_log)
            self.query_one("#dm_log").write_line(wrap_text(dm_response))

        self.query_one("#pc_party_table").update_table()
        self.query_one("#dm_log").write_line("---")

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()

    def action_move_north(self) -> None:
        """Move the party north."""
        self.perform_move_action(Direction.NORTH, "> Move north")

    def action_move_south(self) -> None:
        """Move the party south."""
        self.perform_move_action(Direction.SOUTH, "> Move south")

    def action_move_east(self) -> None:
        """Move the party east."""
        self.perform_move_action(Direction.EAST, "> Move east")

    def action_move_west(self) -> None:
        """Move the party west."""
        self.perform_move_action(Direction.WEST, "> Move west")

    def action_move_up(self) -> None:
        """Move the party up."""
        self.perform_move_action(Direction.UP, "> Ascend stairs")

    def action_move_down(self) -> None:
        """Move the party down."""
        self.perform_move_action(Direction.DOWN, "> Descend stairs")

    def clear_logs(self) -> None:
        """An action to clear the logs."""
        self.query_one("#player_log").clear()
        self.query_one("#dm_log").clear()

    def action_summarize(self) -> None:
        """An action to summarize the session."""
        self.query_one("#player_log").write_line("> Describe location")
        formatted_message = self.dungeon_assistant.format_user_message(
            "Please describe this location again, including specifying the exit that we entered from and which exit or exits, if any, we haven't yet explored: " \
            + str(self.dungeon_assistant.adventure.active_dungeon.current_party_location)
        )
        dm_response = self.dungeon_assistant.send_player_message(formatted_message)
        self.query_one("#dm_log").write_line(
            ""#"> " + str(self.dungeon_assistant.adventure.active_dungeon.current_party_location)
        )
        self.query_one("#dm_log").write_line(wrap_text(dm_response))
        self.query_one("#dm_log").write_line("---")

    def action_character(self) -> None:
        """Show the character screen."""
        self.app.push_screen("screen_character")

    def action_heal_party(self) -> None:
        """An action to heal the party."""
        self.query_one("#player_log").write_line("> Heal party")
        self.dungeon_assistant.adventure.active_party.heal_party()
        self.query_one("#player_log").write_line("  Party healed.")
        self.query_one("#pc_party_table").update_table()

    def action_save_game(self) -> None:
        """An action to save the game."""
        self.query_one("#player_log").write_line("> Save adventure")
        save_path = self.dungeon_assistant.adventure.save_adventure()
        self.query_one("#player_log").write_line(f"  Saved to: {save_path}")

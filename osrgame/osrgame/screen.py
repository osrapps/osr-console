from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Button, Header, Footer, Log, Placeholder

from osrlib import DungeonMaster
from osrlib.dungeon import Direction
from osrlib.utils import wrap_text
from widgets import CharacterStats, AbilityTable, ItemTable, SavingThrows, CharacterScreenButtons


####################
# Welcome Screen
class WelcomeScreen(Screen):
    BINDINGS = [
        ("escape", "app.pop_screen", "Pop screen"),
        ("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True, id="header")

        yield Footer()

    def on_mount(self) -> None:
        pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        pass

    def action_quit(self) -> None:
        """An action to quit the application."""
        self.exit()


####################
# Main Screen
class MainScreen(Screen):
    BINDINGS = [
        ("escape", "app.pop_screen", "Pop screen"),
        ("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True, id="header")
        yield Placeholder("Main")
        yield Footer()

    def on_mount(self) -> None:
        pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        pass

    def action_quit(self) -> None:
        """An action to quit the application."""
        self.exit()


####################
# Character Screen
class CharacterScreen(Screen):
    BINDINGS = [
        ("k", "clear_log", "Clear log"),
        ("escape", "app.pop_screen", "Pop screen"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(id="header", show_clock=True, classes="header-footer")
        yield CharacterStats(id="stat-block", classes="box")
        yield Log(id="log", auto_scroll=True, classes="box")
        yield AbilityTable(id="ability-block")
        yield SavingThrows(id="saving-throw-block")
        yield ItemTable(id="item-block", classes="box")
        yield CharacterScreenButtons(id="char-buttons", classes="char-buttons-class")
        yield Footer()

    def on_mount(self) -> None:
        """Perform actions when the widget is mounted."""
        self.query_one(Log).border_subtitle = "LOG"
        self.query_one(CharacterStats).pc_name = self.app.player_character.name
        self.query_one(CharacterStats).pc_class = self.app.player_character.character_class
        self.query_one(CharacterStats).pc_level = self.app.player_character.character_class.current_level
        self.query_one(CharacterStats).pc_hp = self.app.player_character.character_class.hp
        self.query_one(CharacterStats).pc_ac = self.app.player_character.armor_class
        self.query_one(AbilityTable).update_table()
        self.query_one(SavingThrows).update_table()
        self.query_one(ItemTable).items = self.app.player_character.inventory.all_items

    def on_button_pressed(self, event: Button.Pressed) -> None:
        pc = self.app.player_character
        if event.button.id == "btn_roll_abilities":
            self.reroll()
            self.query_one(CharacterStats).pc_ac = pc.armor_class

        elif event.button.id == "btn_roll_hp":
            hp_roll = pc.roll_hp()
            pc.character_class.hp = max(hp_roll.total_with_modifier, 1)
            roll_string = hp_roll.pretty_print()
            self.query_one(Log).write_line(roll_string)
            self.query_one(CharacterStats).pc_hp = pc.character_class.hp

    def action_clear_log(self) -> None:
        """An action to clear the log."""
        self.query_one(Log).clear()

    def reroll(self):
        """Rolls the ability scores of the active character."""
        self.app.player_character.roll_abilities()
        self.query_one(AbilityTable).update_table()


####################
# Party Screen
class PartyScreen(Screen):
    BINDINGS = [
        ("escape", "app.pop_screen", "Pop screen"),
        ("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True, id="header")
        yield Placeholder("Party Manager")
        yield Footer()

    def on_mount(self) -> None:
        pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        pass

    def action_quit(self) -> None:
        """An action to quit the application."""
        self.exit()


####################
# Module Screen
class ModuleScreen(Screen):
    BINDINGS = [
        ("escape", "app.pop_screen", "Pop screen"),
        ("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True, id="header")
        yield Placeholder("Module Manager")
        yield Footer()

    def on_mount(self) -> None:
        pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        pass

    def action_quit(self) -> None:
        """An action to quit the application."""
        self.exit()


####################
# Explore Screen
class ExploreScreen(Screen):
    BINDINGS = [
        ("b", "start_session", "Begin session"),
        ("n", "move_north", "North"),
        ("s", "move_south", "South"),
        ("e", "move_east", "East"),
        ("w", "move_west", "West"),
        ("k", "clear_logs", "Clear logs"),
        ("?", "summarize", "Summarize session"),
    ]

    dungeon_master = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Log(id="player_log", auto_scroll=True, classes="box")
        yield Log(id="dm_log", auto_scroll=True, classes="box")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#player_log", Log).border_title = "COMMAND LOG"
        self.query_one("#dm_log", Log).border_subtitle = "ADVENTURE LOG"
        self.query_one("#player_log", Log).write_line("Press 'b' to begin a new session.")

    def action_start_session(self) -> None:
        """Start a new session."""

        player_log = self.query_one("#player_log")
        dm_log = self.query_one("#dm_log")

        self.dungeon_master = DungeonMaster(self.app.adventure)
        dm_response = self.dungeon_master.start_session()

        # Move the party to the first location
        first_exit = self.dungeon_master.adventure.active_dungeon.get_location_by_id(1).exits[0]
        dm_response = self.dungeon_master.move_party(first_exit.direction)

        player_log.clear()
        player_log.write_line("The party stands ready.")
        player_log.write_line("---")
        dm_log.write_line(wrap_text(dm_response))
        dm_log.write_line(str(self.dungeon_master.adventure.active_dungeon.current_location))
        dm_log.write_line("---")

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()

    def perform_move_action(self, direction: Direction, log_message: str) -> None:
        """Move the party in the specified direction, execute battle (if any), and log the results."""

        self.query_one("#player_log").write_line(log_message)
        self.query_one("#player_log").write_line("---")
        dm_response = self.dungeon_master.move_party(direction)
        self.query_one("#dm_log").write_line(wrap_text(dm_response))
        self.check_for_encounter()
        self.query_one("#dm_log").write_line(str(self.dungeon_master.adventure.active_dungeon.current_location))
        self.query_one("#dm_log").write_line("---")

    def check_for_encounter(self) -> None:
        """Check for an encounter and execute battle if there are monsters in the encounter."""
        if self.dungeon_master.adventure.active_dungeon.current_location.encounter and not self.dungeon_master.adventure.active_dungeon.current_location.encounter.is_ended:

            encounter = self.dungeon_master.adventure.active_dungeon.current_location.encounter
            encounter.start_encounter(self.dungeon_master.adventure.active_party)
            encounter_log = encounter.get_encounter_log()

            self.query_one("#dm_log").write_line("---")
            dm_response = self.dungeon_master.summarize_battle(encounter_log)
            self.query_one("#dm_log").write_line(wrap_text(dm_response))

            self.query_one("#player_log").write_line("Encounter!")
            self.query_one("#player_log").write_line(str(self.dungeon_master.adventure.active_party))
            self.query_one("#player_log").write_line("---")

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
        formatted_message = self.dungeon_master.format_user_message("Please summarize the game session thus far. Include only what the players would know.")
        dm_response = self.dungeon_master.player_message(formatted_message)
        self.query_one("#dm_log").write_line(wrap_text(dm_response))
        self.query_one("#dm_log").write_line("===")


####################
# Combat Screen
class CombatScreen(Screen):
    BINDINGS = [
        ("escape", "app.pop_screen", "Pop screen"),
        ("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True, id="header")
        yield Placeholder("Adventure")
        yield Footer()

    def on_mount(self) -> None:
        pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        pass

    def action_quit(self) -> None:
        """An action to quit the application."""
        self.exit()


####################
# Exit Screen
class ExitScreen(Screen):
    BINDINGS = [
        ("escape", "app.pop_screen", "Pop screen"),
        ("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True, id="header")
        yield Placeholder("Goodbye")
        yield Footer()

    def on_mount(self) -> None:
        pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        pass

    def action_quit(self) -> None:
        """An action to quit the application."""
        self.exit()

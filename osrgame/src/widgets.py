from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Button, Header, Footer, Log, Placeholder
from osrlib.character_classes import CharacterClassType

from osrlib.item import Armor, Weapon
from .widgets import CharacterStats, AbilityTable, ItemTable, SavingThrows, CharacterScreenButtons


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
        ("escape", "app.pop_screen", "Pop screen"),
        ("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True, id="header")
        yield Placeholder("Explore")
        yield Footer()

    def on_mount(self) -> None:
        pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        pass

    def action_quit(self) -> None:
        """An action to quit the application."""
        self.exit()


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

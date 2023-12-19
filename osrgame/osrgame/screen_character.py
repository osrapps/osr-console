from typing import Any, Coroutine
from textual import events, on
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Button, Header, Footer, Log
from textual.events import Event

from widgets import (
    CharacterStatsBox,
    AbilityTable,
    ItemTable,
    SavingThrowTable,
    CharacterScreenButtons,
)


class CharacterScreen(Screen):
    BINDINGS = [
        ("k", "clear_log", "Clear log"),
        ("escape", "app.pop_screen", "Back"),
        ("n", "next_character", "Next character"),
        ("ctrl+n", "new_character", "New character"),
        ("ctrl+delete", "delete_character", "Delete character"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(id="header", show_clock=True, classes="header-footer")
        yield CharacterStatsBox(id="stat-block", classes="box")
        yield Log(id="log", auto_scroll=True, classes="box")
        yield AbilityTable(id="ability-block")
        yield SavingThrowTable(id="saving-throw-block")
        yield ItemTable(id="item-block", classes="box")
        yield CharacterScreenButtons(id="char-buttons", classes="char-buttons-class")
        yield Footer()

    def on_mount(self) -> None:
        """Perform actions when the widget is mounted."""
        self.query_one(Log).border_subtitle = "LOG"
        self.query_one(
            CharacterStatsBox
        ).pc_name = self.app.adventure.active_party.active_character.name
        self.query_one(
            CharacterStatsBox
        ).pc_class = self.app.adventure.active_party.active_character.character_class
        self.query_one(
            CharacterStatsBox
        ).pc_level = (
            self.app.adventure.active_party.active_character.character_class.current_level
        )
        self.query_one(
            CharacterStatsBox
        ).pc_hp = self.app.adventure.active_party.active_character.character_class.hp
        self.query_one(
            CharacterStatsBox
        ).pc_ac = self.app.adventure.active_party.active_character.armor_class
        self.query_one(AbilityTable).update_table()
        self.query_one(SavingThrowTable).update_table()
        self.query_one(
            ItemTable
        ).items = self.app.adventure.active_party.active_character.inventory.all_items

    @on(Button.Pressed, "#btn_new_character")
    def btn_new_character(self) -> None:
        self.query_one(Log).write_line(f"Creating a new character...")
        self.action_new_character()

    @on(Button.Pressed, "#btn_delete_character")
    def btn_delete_character(self) -> None:
        self.action_delete_character()

    @on(Button.Pressed, "#btn_roll_abilities")
    def btn_roll_abilities(self) -> None:
        pc = self.app.adventure.active_party.active_character
        self.reroll()
        self.query_one(CharacterStatsBox).pc_ac = pc.armor_class

    @on(Button.Pressed, "#btn_roll_hp")
    def btn_roll_hp(self) -> None:
        roll = self.app.adventure.active_party.active_character.roll_hp()
        self.query_one(Log).write_line(f"HP roll: {roll.total_with_modifier} on {roll}.")
        self.query_one(CharacterStatsBox).pc_hp = self.app.adventure.active_party.active_character.max_hit_points

    @on(Button.Pressed, "#btn_save_character")
    def btn_save_character(self) -> None:
        pc = self.app.adventure.active_party.active_character
        pc.save_character()
        self.query_one(Log).write_line(f"Character {pc.name} saved.")

    def action_clear_log(self) -> None:
        """An action to clear the log."""
        self.query_one(Log).clear()

    def action_new_character(self) -> None:
        """An action to create a new character."""
        self.app.push_screen("screen_modal_new_char")

    def action_next_character(self) -> None:
        """An action to switch to the next character in the party."""
        self.app.adventure.active_party.set_next_character_as_active()
        self.query_one(Log).write_line(
            f"Active character is now {self.app.adventure.active_party.active_character.name}."
        )
        self.on_mount()

    def action_delete_character(self) -> None:
        """An action to delete the active character."""
        character_to_remove = self.app.adventure.active_party.active_character
        self.action_next_character()
        self.app.adventure.active_party.remove_character(character_to_remove)
        self.query_one(Log).write_line(
            f"Character {character_to_remove.name} removed from party."
        )

    def on_event(self, event: Event) -> Coroutine[Any, Any, None]:
        """Handle events."""
        # HACK: This is a hack to get the screen to update when the user switches to it.
        if isinstance(event, events.ScreenResume):
            self.on_mount()
        return super().on_event(event)

    def reroll(self):
        """Rolls the ability scores of the active character."""
        self.app.adventure.active_party.active_character.roll_abilities()
        self.query_one(AbilityTable).update_table()

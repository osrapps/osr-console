from typing import List
from collections import defaultdict
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Container
from textual.reactive import reactive
from textual.widgets import Button, DataTable, Log, Static

from osrlib import Item, ItemType
from osrlib.utils import format_modifiers


class CharacterScreenButtons(Container):
    def compose(self) -> ComposeResult:
        yield Button("Roll abilities", id="btn_roll_abilities", classes="button")
        yield Button("Roll HP", id="btn_roll_hp", classes="button")
        yield Button("Save character", id="btn_save_character", classes="button")


class CharacterStats(Container):
    """A container for the character stats like name, class, level, HP, and AC."""

    pc_name = reactive("")
    pc_class = reactive("")
    pc_level = reactive(0)
    pc_hp = reactive(0)
    pc_ac = reactive(0)

    BORDER_TITLE = "CHARACTER RECORD SHEET"

    def compose(self) -> ComposeResult:
        yield Static(id="name")
        yield Static(id="class")
        yield Static(id="level")
        yield Static(id="hp")
        yield Static(id="ac")

    def watch_pc_name(self, pc_name: str) -> None:
        """Update the name label when the PC's name changes."""
        self.query_one("#name", Static).update(f"Name: {pc_name}")

    def watch_pc_class(self, pc_class: str) -> None:
        """Update the class label when the PC's class changes."""
        self.query_one("#class", Static).update(f"Class: {pc_class}")

    def watch_pc_level(self, pc_level: int) -> None:
        """Update the level label when the PC's level changes."""
        self.query_one("#level", Static).update(f"Level: {pc_level}")

    def watch_pc_hp(self, pc_hp: int) -> None:
        """Update the HP label when the PC's hit points change."""
        self.query_one("#hp", Static).update(f"HP: {pc_hp}")

    def watch_pc_ac(self, pc_ac: int) -> None:
        """Update the AC label when the PC's armor class changes."""
        self.query_one("#ac", Static).update(f"AC: {pc_ac}")


class AbilityTable(Container):
    def compose(self) -> ComposeResult:
        yield DataTable(id="tbl_abilities", cursor_type=None, classes="table")

    def on_mount(self) -> None:
        """Perform actions when the widget is mounted."""
        table = self.query_one(DataTable)
        score_column = Text("Score", justify="center")
        table.add_columns("Ability", score_column, "Modifiers")

    def update_table(self):
        pc = self.app.player_character
        table = self.query_one(DataTable)
        table.clear()
        for k, v in pc.abilities.items():
            row_data = [
                k.value,
                Text(str(v.score), justify="center"),
                format_modifiers(v.modifiers),
            ]
            table.add_row(*row_data, key=k.name)


class SavingThrows(Container):
    def compose(self) -> ComposeResult:
        yield DataTable(cursor_type=None, classes="table")

    def on_mount(self) -> None:
        """Perform actions when the widget is mounted."""
        table = self.query_one(DataTable)
        score_column = Text("Score", justify="center")
        table.add_columns("Saving Throw", score_column)

    def update_table(self):
        pc = self.app.player_character
        table = self.query_one(DataTable)
        table.clear()
        for k, v in pc.character_class.saving_throws.items():
            row_data = [k.value, Text(str(v), justify="center")]
            table.add_row(*row_data, key=k.name)


class ItemTable(Container):
    items = reactive([], always_update=True)

    BORDER_TITLE = "INVENTORY"

    """A container for widgets that render a character's inventory ."""

    def compose(self) -> ComposeResult:
        yield DataTable(cursor_type="row", classes="table")

    def on_mount(self) -> None:
        """Perform actions when the widget is mounted."""
        table = self.query_one(DataTable)
        table.add_columns(
            "Name",
            "Type",
            "Equipped",
            "Value (gp)",
        )
        self.update_table(self.items)

    def watch_items(self, items: List[Item]) -> None:
        """Update the item table when the PC's list changes."""
        self.update_table(items)

    def update_table(self, items: List[Item]) -> None:
        table = self.query_one(DataTable)
        table.clear()
        if not items:
            return
        for item in items:
            row_data = [
                item.name,
                item.item_type.name,
                Text(str(item.is_equipped)),
                Text(str(item.gp_value), justify="center"),
            ]
            table.add_row(*row_data, key=item.name)


class ExploreLogs(Container):
    """A container for the DM and player logs."""

    def compose(self) -> ComposeResult:
        yield Log(id="dm_log", auto_scroll=True, classes="box")
        yield Log(id="player_log", auto_scroll=True, classes="box")

    def on_mount(self) -> None:
        """Perform actions when the widget is mounted."""
        self.query_one("#dm_log", Log).border_title = "DM LOG"
        self.query_one("#player_log", Log).border_subtitle = "PLAYER LOG"

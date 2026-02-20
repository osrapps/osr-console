"""Full character stats panel widget."""

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import DataTable, Static

from osrlib.player_character import PlayerCharacter
from osrlib.utils import format_modifiers


class CharSheetWidget(Vertical):
    """Full character sheet panel showing stats, abilities, saves, and inventory."""

    DEFAULT_CSS = """
    CharSheetWidget {
        height: 100%;
        border: solid #4a4a8a;
        background: #0e0e3a;
        padding: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("No character selected", id="char-header", classes="gold-heading")
        yield DataTable(id="char-abilities", cursor_type=None)
        yield DataTable(id="char-saves", cursor_type=None)
        yield DataTable(id="char-inventory", cursor_type=None)

    def on_mount(self) -> None:
        abilities = self.query_one("#char-abilities", DataTable)
        abilities.add_columns("Ability", "Score", "Modifiers")

        saves = self.query_one("#char-saves", DataTable)
        saves.add_columns("Saving throw", "Score")

        inv = self.query_one("#char-inventory", DataTable)
        inv.add_columns("Item", "Type", "Equipped", "GP")

    def update_character(self, pc: PlayerCharacter) -> None:
        """Refresh all sub-tables from a PlayerCharacter instance."""
        # Header
        header = self.query_one("#char-header", Static)
        alignment = getattr(pc, "alignment", None)
        align_str = f" ({alignment.value})" if alignment else ""
        header.update(
            f"{pc.name} — {pc.character_class.class_type.value} Lv{pc.level}"
            f"  HP: {pc.hit_points}/{pc.max_hit_points}  AC: {pc.armor_class}{align_str}"
        )

        # Abilities
        table = self.query_one("#char-abilities", DataTable)
        table.clear()
        for ability_type, ability in pc.abilities.items():
            table.add_row(
                ability_type.value,
                Text(str(ability.score), justify="center"),
                format_modifiers(ability.modifiers),
                key=ability_type.name,
            )

        # Saving throws
        saves = self.query_one("#char-saves", DataTable)
        saves.clear()
        for save_name, save_val in pc.character_class.saving_throws.items():
            saves.add_row(
                save_name.value,
                Text(str(save_val), justify="center"),
                key=save_name.name,
            )

        # Inventory
        inv = self.query_one("#char-inventory", DataTable)
        inv.clear()
        for idx, item in enumerate(pc.inventory.all_items):
            inv.add_row(
                item.name,
                item.item_type.name,
                Text("Yes" if item.is_equipped else "", justify="center"),
                Text(str(item.gp_value), justify="center"),
                key=f"inv_{idx}",
            )

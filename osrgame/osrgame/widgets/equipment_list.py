"""Equipment list widget for shop and character creation equipment buying."""

from rich.text import Text
from textual.widgets import DataTable

from osrlib.enums import CharacterClassType
from osrlib.item_factories import armor_data, weapon_data, equipment_data


class EquipmentListWidget(DataTable):
    """DataTable listing purchasable equipment with name, type, cost, and usability."""

    DEFAULT_CSS = """
    EquipmentListWidget {
        height: 100%;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(cursor_type="row", **kwargs)
        self._items: list[dict] = []

    def on_mount(self) -> None:
        self.add_columns("Item", "Type", "Cost (GP)")

    def load_items(self, class_type: CharacterClassType | None = None) -> None:
        """Load all purchasable items, optionally filtered by class usability."""
        self.clear()
        self._items = []

        # Armor
        for name, info in armor_data.items():
            if class_type and class_type not in info["usable_by"]:
                continue
            item = {
                "name": name,
                "type": "Armor",
                "gp_value": info["gp_value"],
                "data": info,
            }
            self._items.append(item)
            self.add_row(
                name, "Armor", Text(str(info["gp_value"]), justify="right"), key=name
            )

        # Weapons
        for name, info in weapon_data.items():
            if class_type and class_type not in info["usable_by"]:
                continue
            item = {
                "name": name,
                "type": "Weapon",
                "gp_value": info["gp_value"],
                "data": info,
            }
            self._items.append(item)
            self.add_row(
                name, "Weapon", Text(str(info["gp_value"]), justify="right"), key=name
            )

        # Equipment
        for name, gp_value in equipment_data.items():
            item = {"name": name, "type": "Equipment", "gp_value": gp_value, "data": {}}
            self._items.append(item)
            self.add_row(
                name, "Equipment", Text(str(gp_value), justify="right"), key=name
            )

    def get_item_at_row(self, row_index: int) -> dict | None:
        """Get the item data dict for the given row index."""
        if 0 <= row_index < len(self._items):
            return self._items[row_index]
        return None

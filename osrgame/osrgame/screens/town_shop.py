"""Shop screen — buy and sell equipment."""

from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, DataTable, Footer, Header, Static

from osrlib.item_factories import ArmorFactory, EquipmentFactory, WeaponFactory

from ..widgets import EquipmentListWidget, PartyRosterWidget


class ShopScreen(Screen):
    """Equipment shop: buy and sell weapons, armor, and gear."""

    BINDINGS = [
        ("escape", "done", "Done"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static("Shop", id="town-title", classes="gold-heading")
        with Horizontal(id="shop-layout"):
            with Vertical(id="shop-left"):
                yield PartyRosterWidget(id="shop-roster")
                yield Static("Inventory", id="shop-inv-title", classes="gold-heading")
                yield DataTable(id="shop-inventory", cursor_type="row")
            with Vertical(id="shop-right"):
                yield Static("Gold: 0", id="shop-gold")
                with Horizontal(id="shop-mode-bar"):
                    yield Button("Buy", id="btn-mode-buy", variant="primary")
                    yield Button("Sell", id="btn-mode-sell")
                yield EquipmentListWidget(id="shop-catalog")
                yield Button("Done", id="btn-shop-done")
        yield Footer()

    def on_mount(self) -> None:
        self._selected_pc = None
        self._mode = "buy"
        self.query_one("#shop-roster", PartyRosterWidget).refresh_roster()
        self._refresh_gold()
        inv_table = self.query_one("#shop-inventory", DataTable)
        inv_table.add_columns("Item", "Type", "Equipped", "Value")

    def _refresh_gold(self) -> None:
        party = self.app.game_state.adventure.active_party
        self.query_one("#shop-gold", Static).update(f"Gold: {party.treasury.gold}")

    def _refresh_inventory(self) -> None:
        """Refresh the selected character's inventory display."""
        inv_table = self.query_one("#shop-inventory", DataTable)
        inv_table.clear()
        pc = self._selected_pc
        if pc is None:
            return
        for item in pc.inventory.all_items:
            equipped = "Yes" if item.is_equipped else ""
            inv_table.add_row(
                item.name,
                item.item_type.value[0],
                equipped,
                Text(str(item.gp_value), justify="right"),
            )

    def _load_catalog(self) -> None:
        """Load the shop catalog filtered by selected character's class."""
        catalog = self.query_one("#shop-catalog", EquipmentListWidget)
        if self._selected_pc:
            catalog.load_items(self._selected_pc.character_class.class_type)
        else:
            catalog.load_items()

    def on_data_table_row_selected(self, event) -> None:
        """Handle row selection in both the roster and inventory tables."""
        table_id = event.data_table.id
        if table_id == "shop-roster":
            event.stop()
            party = self.app.game_state.adventure.active_party
            if event.cursor_row < len(party.members):
                self._selected_pc = party.members[event.cursor_row]
                self._load_catalog()
                self._refresh_inventory()
        elif table_id == "shop-catalog" and self._mode == "buy":
            event.stop()
            self._buy_item(event.cursor_row)
        elif table_id == "shop-inventory" and self._mode == "sell":
            event.stop()
            self._sell_item(event.cursor_row)

    def _buy_item(self, row_index: int) -> None:
        pc = self._selected_pc
        if pc is None:
            self.notify("Select a character first.", severity="warning", title="Shop")
            return
        catalog = self.query_one("#shop-catalog", EquipmentListWidget)
        item_data = catalog.get_item_at_row(row_index)
        if item_data is None:
            return

        party = self.app.game_state.adventure.active_party
        cost = item_data["gp_value"]
        if not party.treasury.spend_gold(cost):
            self.notify(f"Not enough gold (need {cost} gp).", severity="error", title="Shop")
            return

        # Create the item via factory
        item_type = item_data["type"]
        name = item_data["name"]
        try:
            if item_type == "Armor":
                item = ArmorFactory.create_armor(name)
            elif item_type == "Weapon":
                item = WeaponFactory.create_weapon(name)
            else:
                item = EquipmentFactory.create_item(name)

            pc.inventory.add_item(item)
            # Auto-equip if it's the first of its type
            if item.is_equipable:
                pc.inventory.equip_item(item)
            self.notify(f"{pc.name} bought {name} for {cost} gp.", title="Shop")
        except Exception as e:
            # Refund on error
            party.treasury.add_coins(cost)
            self.notify(str(e), severity="error", title="Shop")
            return

        self._refresh_gold()
        self._refresh_inventory()

    def _sell_item(self, row_index: int) -> None:
        pc = self._selected_pc
        if pc is None:
            return
        items = pc.inventory.all_items
        if row_index >= len(items):
            return

        item = items[row_index]
        sell_price = item.gp_value // 2
        if sell_price < 1:
            sell_price = 1

        try:
            if item.is_equipped:
                pc.inventory.unequip_item(item)
            pc.inventory.remove_item(item)
        except Exception as e:
            self.notify(str(e), severity="error", title="Shop")
            return

        party = self.app.game_state.adventure.active_party
        party.treasury.add_coins(sell_price)
        self.notify(f"Sold {item.name} for {sell_price} gp.", title="Shop")
        self._refresh_gold()
        self._refresh_inventory()
        self.query_one("#shop-roster", PartyRosterWidget).refresh_roster()

    @on(Button.Pressed, "#btn-mode-buy")
    def set_buy_mode(self) -> None:
        self._mode = "buy"
        self.query_one("#btn-mode-buy", Button).variant = "primary"
        self.query_one("#btn-mode-sell", Button).variant = "default"

    @on(Button.Pressed, "#btn-mode-sell")
    def set_sell_mode(self) -> None:
        self._mode = "sell"
        self.query_one("#btn-mode-sell", Button).variant = "primary"
        self.query_one("#btn-mode-buy", Button).variant = "default"

    @on(Button.Pressed, "#btn-shop-done")
    def done(self) -> None:
        self.action_done()

    def action_done(self) -> None:
        self.dismiss()

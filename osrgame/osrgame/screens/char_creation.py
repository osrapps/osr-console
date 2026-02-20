"""7-step character creation wizard following OSE SRD procedure."""

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    RadioButton,
    RadioSet,
    Static,
)

from rich.text import Text

from osrlib.ability import (
    Charisma,
    Constitution,
    Dexterity,
    Intelligence,
    Strength,
    Wisdom,
)
from osrlib.character_classes import CLASS_REQUIREMENTS, meets_class_requirements
from osrlib.dice_roller import roll_dice
from osrlib.enums import AbilityType, CharacterClassType
from osrlib.item_factories import (
    ArmorFactory,
    EquipmentFactory,
    WeaponFactory,
    armor_data,
    equipment_data,
    weapon_data,
)
from osrlib.player_character import Alignment, PlayerCharacter
from osrlib.utils import format_modifiers


# Classes available for player creation (no Commoner)
PLAYABLE_CLASSES = [
    CharacterClassType.CLERIC,
    CharacterClassType.DWARF,
    CharacterClassType.ELF,
    CharacterClassType.FIGHTER,
    CharacterClassType.HALFLING,
    CharacterClassType.MAGIC_USER,
    CharacterClassType.THIEF,
]

STEP_TITLES = [
    "Roll ability scores",
    "Choose class",
    "Adjust abilities (optional)",
    "Choose alignment",
    "Roll hit points",
    "Name your character",
    "Buy equipment",
]


class CharCreationScreen(Screen):
    """7-step character creation wizard."""

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    step = reactive(0)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._abilities: dict[AbilityType, object] = {}
        self._class_type: CharacterClassType | None = None
        self._alignment: Alignment = Alignment.NEUTRAL
        self._hp: int = 0
        self._name: str = ""
        self._gold: int = 0
        self._purchased_items: list[str] = []
        self._use_3d6: bool = True

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static(
            "Step 1 of 7: Roll ability scores", id="step-title", classes="gold-heading"
        )
        yield Vertical(id="step-content")
        with Horizontal(id="nav-buttons"):
            yield Button("Cancel", id="btn-cancel")
            yield Button("Back", id="btn-back")
            yield Button("Next", id="btn-next", variant="primary")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#btn-back").disabled = True
        self._roll_abilities()
        self._render_step()

    def watch_step(self, step: int) -> None:
        title = self.query_one("#step-title", Static)
        title.update(f"Step {step + 1} of 7: {STEP_TITLES[step]}")
        self.query_one("#btn-back").disabled = step == 0
        btn_next = self.query_one("#btn-next", Button)
        btn_next.label = "Finish" if step == 6 else "Next"

    # --- Navigation ---

    @on(Button.Pressed, "#btn-next")
    def next_step(self) -> None:
        if not self._check_step_complete():
            return
        if self.step == 6:
            self._finish()
        else:
            self.step += 1
            self._render_step()

    @on(Button.Pressed, "#btn-back")
    def prev_step(self) -> None:
        if self.step > 0:
            self.step -= 1
            self._render_step()

    @on(Button.Pressed, "#btn-cancel")
    def cancel(self) -> None:
        self.action_cancel()

    def action_cancel(self) -> None:
        self.dismiss(None)

    # --- Ability rolling ---

    def _roll_abilities(self) -> None:
        """Roll a fresh set of abilities."""
        self._abilities = {}
        ability_classes = [
            Strength,
            Intelligence,
            Wisdom,
            Dexterity,
            Constitution,
            Charisma,
        ]
        for ability_cls in ability_classes:
            if self._use_3d6:
                score = roll_dice("3d6").total
            else:
                score = roll_dice("4d6", drop_lowest=True).total
            ability = ability_cls(score)
            self._abilities[ability.ability_type] = ability

    # --- Step rendering ---

    def _render_step(self) -> None:
        """Clear and re-render the step content area."""
        content = self.query_one("#step-content", Vertical)
        content.remove_children()
        render_fn = [
            self._render_step_abilities,
            self._render_step_class,
            self._render_step_adjust,
            self._render_step_alignment,
            self._render_step_hp,
            self._render_step_name,
            self._render_step_equipment,
        ][self.step]
        render_fn(content)

    def _render_step_abilities(self, container: Vertical) -> None:
        method_label = "3d6 in order" if self._use_3d6 else "4d6 drop lowest"
        container.mount(
            Static(f"Rolling method: {method_label}", classes="gold-heading")
        )
        table = DataTable(id="ability-roll-table", cursor_type=None)
        container.mount(table)
        table.add_columns("Ability", "Score", "Modifiers")
        for ability_type, ability in self._abilities.items():
            table.add_row(
                ability_type.value,
                Text(str(ability.score), justify="center"),
                format_modifiers(ability.modifiers),
                key=ability_type.name,
            )
        container.mount(
            Horizontal(
                Button("Reroll", id="btn-reroll"),
                Button("Toggle 3d6/4d6", id="btn-toggle-method"),
            )
        )

    def _render_step_class(self, container: Vertical) -> None:
        container.mount(
            Static("Choose a class for your character:", classes="gold-heading")
        )
        radio_set = RadioSet(id="class-radio")
        container.mount(radio_set)
        for cls_type in PLAYABLE_CLASSES:
            eligible = meets_class_requirements(self._abilities, cls_type)
            reqs = CLASS_REQUIREMENTS.get(cls_type, {})
            req_str = ""
            if reqs:
                parts = [f"{a.value} {v}+" for a, v in reqs.items()]
                req_str = f" (requires {', '.join(parts)})"
            label = f"{cls_type.value}{req_str}"
            btn = RadioButton(
                label, name=cls_type.name, value=(cls_type == self._class_type)
            )
            btn.disabled = not eligible
            radio_set.mount(btn)

    def _render_step_adjust(self, container: Vertical) -> None:
        container.mount(
            Static(
                "Ability adjustment is not yet implemented.\nPress Next to continue.",
                classes="gold-heading",
            )
        )
        # Show current abilities for reference
        table = DataTable(id="adjust-table", cursor_type=None)
        container.mount(table)
        table.add_columns("Ability", "Score")
        for ability_type, ability in self._abilities.items():
            table.add_row(
                ability_type.value,
                Text(str(ability.score), justify="center"),
                key=ability_type.name,
            )

    def _render_step_alignment(self, container: Vertical) -> None:
        container.mount(Static("Choose an alignment:", classes="gold-heading"))
        radio_set = RadioSet(id="alignment-radio")
        container.mount(radio_set)
        for alignment in Alignment:
            radio_set.mount(
                RadioButton(
                    alignment.value,
                    name=alignment.name,
                    value=(alignment == self._alignment),
                )
            )

    def _render_step_hp(self, container: Vertical) -> None:
        if self._class_type is None:
            container.mount(
                Static("Please go back and select a class.", classes="gold-heading")
            )
            return
        from osrlib.character_classes import class_levels

        hit_die = class_levels[self._class_type][1].hit_dice
        con_mod = self._abilities[AbilityType.CONSTITUTION].modifiers.get(
            __import__("osrlib.enums", fromlist=["ModifierType"]).ModifierType.HP, 0
        )
        hp_roll = roll_dice(hit_die, con_mod)
        self._hp = max(hp_roll.total_with_modifier, 1)
        container.mount(
            Static(
                f"Hit die: {hit_die}  CON modifier: {con_mod:+d}\n"
                f"Rolled: {hp_roll.total}  Final HP: {self._hp}",
                classes="gold-heading",
            )
        )
        container.mount(Button("Reroll HP", id="btn-reroll-hp"))

    def _render_step_name(self, container: Vertical) -> None:
        container.mount(
            Static("Enter a name for your character:", classes="gold-heading")
        )
        container.mount(
            Input(placeholder="Character name", id="char-name-input", value=self._name)
        )

    def _render_step_equipment(self, container: Vertical) -> None:
        if self._gold == 0:
            gold_roll = roll_dice("3d6")
            self._gold = gold_roll.total * 10
        container.mount(
            Static(
                f"Gold: {self._gold} GP  |  Select items to buy",
                id="gold-display",
                classes="gold-heading",
            )
        )
        table = DataTable(id="shop-table", cursor_type="row")
        container.mount(table)
        table.add_columns("Item", "Type", "Cost (GP)")
        self._shop_items = []

        # Armor
        for name, info in armor_data.items():
            if self._class_type and self._class_type not in info["usable_by"]:
                continue
            self._shop_items.append(
                {"name": name, "type": "Armor", "gp_value": info["gp_value"]}
            )
            table.add_row(
                name,
                "Armor",
                Text(str(info["gp_value"]), justify="right"),
                key=f"armor_{name}",
            )

        # Weapons
        for name, info in weapon_data.items():
            if self._class_type and self._class_type not in info["usable_by"]:
                continue
            self._shop_items.append(
                {"name": name, "type": "Weapon", "gp_value": info["gp_value"]}
            )
            table.add_row(
                name,
                "Weapon",
                Text(str(info["gp_value"]), justify="right"),
                key=f"weapon_{name}",
            )

        # Equipment
        for name, gp_value in equipment_data.items():
            self._shop_items.append(
                {"name": name, "type": "Equipment", "gp_value": gp_value}
            )
            table.add_row(
                name,
                "Equipment",
                Text(str(gp_value), justify="right"),
                key=f"equip_{name}",
            )

        # Show purchased items
        if self._purchased_items:
            container.mount(
                Static(
                    f"Purchased: {', '.join(self._purchased_items)}",
                    id="purchased-list",
                )
            )

    # --- Event handlers ---

    @on(Button.Pressed, "#btn-reroll")
    def reroll_abilities(self) -> None:
        self._roll_abilities()
        self._render_step()

    @on(Button.Pressed, "#btn-toggle-method")
    def toggle_roll_method(self) -> None:
        self._use_3d6 = not self._use_3d6
        self._roll_abilities()
        self._render_step()

    @on(Button.Pressed, "#btn-reroll-hp")
    def reroll_hp(self) -> None:
        self._render_step()

    @on(RadioSet.Changed, "#class-radio")
    def class_selected(self, event: RadioSet.Changed) -> None:
        if event.pressed and event.pressed.name:
            self._class_type = CharacterClassType[event.pressed.name]

    @on(RadioSet.Changed, "#alignment-radio")
    def alignment_selected(self, event: RadioSet.Changed) -> None:
        if event.pressed and event.pressed.name:
            self._alignment = Alignment[event.pressed.name]

    @on(Input.Changed, "#char-name-input")
    def name_changed(self, event: Input.Changed) -> None:
        self._name = event.value.strip()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Buy an item from the shop table."""
        if self.step != 6:
            return
        event.stop()
        row_idx = event.cursor_row
        if row_idx < 0 or row_idx >= len(self._shop_items):
            return
        item = self._shop_items[row_idx]
        cost = item["gp_value"]
        if cost > self._gold:
            self.notify("Not enough gold!", severity="warning")
            return
        self._gold -= cost
        self._purchased_items.append(item["name"])
        # Update gold display
        gold_display = self.query_one("#gold-display", Static)
        gold_display.update(f"Gold: {self._gold} GP  |  Select items to buy")
        # Update purchased list
        purchased = self.query("#purchased-list")
        if purchased:
            purchased.first().update(f"Purchased: {', '.join(self._purchased_items)}")
        else:
            content = self.query_one("#step-content", Vertical)
            content.mount(
                Static(
                    f"Purchased: {', '.join(self._purchased_items)}",
                    id="purchased-list",
                )
            )

    # --- Validation ---

    def _check_step_complete(self) -> bool:
        if self.step == 1 and self._class_type is None:
            self.notify("Please select a class.", severity="warning")
            return False
        if self.step == 5 and not self._name:
            self.notify("Please enter a name.", severity="warning")
            return False
        return True

    # --- Finish ---

    def _finish(self) -> None:
        """Create the PlayerCharacter and dismiss with it."""
        pc = PlayerCharacter(
            name=self._name,
            character_class_type=self._class_type,
            level=1,
            alignment=self._alignment,
        )
        # Override the auto-rolled abilities with the ones we rolled in the wizard
        pc.abilities = dict(self._abilities)
        # Re-set class to pick up the correct abilities for XP adjustment
        pc.set_character_class(self._class_type, 1)
        # Override HP with the player's roll
        pc.character_class.max_hp = self._hp
        pc.character_class.hp = self._hp

        # Add purchased items to inventory
        for item_name in self._purchased_items:
            try:
                if item_name in armor_data:
                    item = ArmorFactory.create_armor(item_name)
                elif item_name in weapon_data:
                    item = WeaponFactory.create_weapon(item_name)
                elif item_name in equipment_data:
                    item = EquipmentFactory.create_item(item_name)
                else:
                    continue
                pc.inventory.add_item(item)
            except Exception:
                pass  # Skip items that can't be created

        # Auto-equip the first weapon and armor
        for item in pc.inventory.all_items:
            if hasattr(item, "damage_die") and not any(
                i.is_equipped for i in pc.inventory.weapons
            ):
                try:
                    pc.inventory.equip_item(item)
                except Exception:
                    pass
            elif hasattr(item, "ac_modifier") and item.ac_modifier != 0:
                try:
                    pc.inventory.equip_item(item)
                except Exception:
                    pass

        self.dismiss(pc)

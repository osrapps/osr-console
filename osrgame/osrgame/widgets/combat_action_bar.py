"""Two-level combat action bar for per-character turn selection."""

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Button, Label

from osrlib.combat.events import ActionChoice, NeedAction
from osrlib.combat.intents import ActionIntent, FleeIntent
from osrlib.combat.spells import SPELL_CATALOG


class CombatActionChosen(Message):
    """Posted when the player selects a complete action (intent ready to submit)."""

    def __init__(self, intent: ActionIntent) -> None:
        super().__init__()
        self.intent = intent


class CombatActionBar(Widget):
    """Two-level action menu: category buttons → target/spell selection.

    Modes:

    - **category**: Show action category buttons (Attack, Ranged, Cast spell, etc.)
    - **target**: Show individual target buttons for the selected category
    - **spell_pick**: Show available spells to pick from
    - **spell_target**: Show individual targets for a single-target spell
    - **item_pick**: Show throwable items to choose from
    - **item_target**: Show individual targets for a selected item
    - **idle**: No active PC turn — bar is hidden

    Turn Undead fires immediately from the category bar (no target selection).
    """

    DEFAULT_CSS = """
    CombatActionBar {
        height: auto;
        padding: 0 1;
    }

    CombatActionBar .action-row {
        height: auto;
        width: 100%;
    }

    CombatActionBar .action-row Button {
        margin: 0 1 0 0;
        min-width: 12;
    }

    CombatActionBar #turn-label {
        text-style: bold;
        color: #ffd700;
        padding: 0 1 0 0;
        width: 100%;
    }
    """

    mode: reactive[str] = reactive("idle")

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._need_action: NeedAction | None = None
        self._pc_name: str = ""
        # Categorized choices
        self._melee_choices: list[ActionChoice] = []
        self._ranged_choices: list[ActionChoice] = []
        self._spell_choices: list[ActionChoice] = []  # all cast_spell choices
        self._has_flee: bool = False
        self._turn_undead_choices: list[ActionChoice] = []
        self._item_choices: list[ActionChoice] = []  # all use_item choices
        # Pending spell for target selection
        self._pending_spell_id: str | None = None
        self._pending_spell_choices: list[ActionChoice] = []
        # Pending item for target selection
        self._pending_item_name: str | None = None
        self._pending_item_choices: list[ActionChoice] = []

    def compose(self) -> ComposeResult:
        yield Label("", id="turn-label")
        yield Horizontal(id="action-buttons", classes="action-row")

    def set_need_action(self, need_action: NeedAction) -> None:
        """Configure the bar for a new PC turn."""
        self._need_action = need_action
        cid = need_action.combatant_id
        self._pc_name = cid.split(":", 1)[1] if ":" in cid else cid

        # Categorize choices
        self._melee_choices = [
            c for c in need_action.available if c.ui_key == "attack_target"
        ]
        self._ranged_choices = [
            c for c in need_action.available if c.ui_key == "ranged_attack_target"
        ]
        self._spell_choices = [
            c for c in need_action.available if c.ui_key == "cast_spell"
        ]
        self._has_flee = any(c.ui_key == "flee" for c in need_action.available)
        self._turn_undead_choices = [
            c for c in need_action.available if c.ui_key == "turn_undead"
        ]
        self._item_choices = [
            c for c in need_action.available if c.ui_key == "use_item"
        ]

        self.mode = "category"

    def clear_action(self) -> None:
        """Clear the bar (combat ended or waiting for monsters)."""
        self._need_action = None
        self._pc_name = ""
        self._melee_choices = []
        self._ranged_choices = []
        self._spell_choices = []
        self._pending_spell_id = None
        self._pending_spell_choices = []
        self._turn_undead_choices = []
        self._item_choices = []
        self._pending_item_name = None
        self._pending_item_choices = []
        self.mode = "idle"

    async def watch_mode(self, new_mode: str) -> None:
        """Rebuild buttons when mode changes."""
        label = self.query_one("#turn-label", Label)
        container = self.query_one("#action-buttons", Horizontal)
        await container.remove_children()

        if new_mode == "idle":
            label.update("")
            self.display = False
            return

        self.display = True

        if new_mode == "category":
            label.update(f"{self._pc_name}'s turn")
            self._build_category_buttons(container)
        elif new_mode == "target":
            label.update(f"{self._pc_name} — select target")
            self._build_target_buttons(container, self._melee_choices)
        elif new_mode == "ranged_target":
            label.update(f"{self._pc_name} — ranged target")
            self._build_target_buttons(container, self._ranged_choices)
        elif new_mode == "spell_pick":
            label.update(f"{self._pc_name} — select spell")
            self._build_spell_pick_buttons(container)
        elif new_mode == "spell_target":
            label.update(f"{self._pc_name} — spell target")
            self._build_target_buttons(container, self._pending_spell_choices)
        elif new_mode == "item_pick":
            label.update(f"{self._pc_name} — select item")
            self._build_item_pick_buttons(container)
        elif new_mode == "item_target":
            label.update(f"{self._pc_name} — item target")
            self._build_target_buttons(container, self._pending_item_choices)

    def _build_category_buttons(self, container: Horizontal) -> None:
        """Build the top-level action category buttons."""
        container.mount(
            Button("Attack", id="cat-attack", disabled=not self._melee_choices)
        )
        container.mount(
            Button("Ranged", id="cat-ranged", disabled=not self._ranged_choices)
        )
        container.mount(
            Button("Cast spell", id="cat-spell", disabled=not self._spell_choices)
        )
        if self._turn_undead_choices:
            container.mount(Button("Turn undead", id="cat-turn-undead"))
        if self._item_choices:
            container.mount(Button("Use item", id="cat-item"))
        container.mount(Button("Flee", id="cat-flee", disabled=not self._has_flee))

    def _build_target_buttons(
        self, container: Horizontal, choices: list[ActionChoice]
    ) -> None:
        """Build one button per individual target from the action choices."""
        for i, choice in enumerate(choices):
            target_name = choice.ui_args.get("target_name", "???")
            label = self._target_label(target_name, choice)
            container.mount(Button(label, id=f"target-{i}", classes="target-btn"))
        container.mount(Button("Back", id="btn-back", variant="default"))

    @staticmethod
    def _target_label(target_name: str, choice: ActionChoice) -> str:
        """Return an enriched label for group targets that have dice info."""
        if target_name == "enemy group":
            spell_id = choice.ui_args.get("spell_id", "")
            spell_def = SPELL_CATALOG.get(spell_id) if spell_id else None
            if spell_def and spell_def.group_target_dice:
                return f"Enemy group ({spell_def.group_target_dice})"
            return "Enemy group"
        return target_name

    def _build_spell_pick_buttons(self, container: Horizontal) -> None:
        """Build buttons for each available spell."""
        seen_spells: set[str] = set()
        for choice in self._spell_choices:
            spell_id = choice.ui_args.get("spell_id", "")
            if spell_id in seen_spells:
                continue
            seen_spells.add(spell_id)
            spell_name = choice.ui_args.get("spell_name", spell_id)
            container.mount(Button(spell_name, id=f"spell-{spell_id}", classes="spell-btn"))
        container.mount(Button("Back", id="btn-back", variant="default"))

    def _build_item_pick_buttons(self, container: Horizontal) -> None:
        """Build one button per unique throwable item."""
        seen_items: set[str] = set()
        for choice in self._item_choices:
            item_name = choice.ui_args.get("item_name", "")
            if item_name in seen_items:
                continue
            seen_items.add(item_name)
            safe_id = item_name.lower().replace(" ", "-")
            container.mount(Button(item_name, id=f"item-{safe_id}", classes="item-btn"))
        container.mount(Button("Back", id="btn-back", variant="default"))

    @on(Button.Pressed, "#cat-attack")
    def _on_attack(self) -> None:
        self.mode = "target"

    @on(Button.Pressed, "#cat-ranged")
    def _on_ranged(self) -> None:
        self.mode = "ranged_target"

    @on(Button.Pressed, "#cat-spell")
    def _on_spell(self) -> None:
        self.mode = "spell_pick"

    @on(Button.Pressed, "#cat-turn-undead")
    def _on_turn_undead(self) -> None:
        if self._turn_undead_choices and self._need_action:
            self.post_message(CombatActionChosen(self._turn_undead_choices[0].intent))

    @on(Button.Pressed, "#cat-item")
    def _on_item(self) -> None:
        self.mode = "item_pick"

    @on(Button.Pressed, ".item-btn")
    def _on_item_selected(self, event: Button.Pressed) -> None:
        """Handle item selection — filter targets for the chosen item."""
        raw_id = (event.button.id or "").replace("item-", "")
        if not raw_id:
            return
        # Match back to item_name by comparing sanitized names
        for choice in self._item_choices:
            item_name = choice.ui_args.get("item_name", "")
            if item_name.lower().replace(" ", "-") == raw_id:
                self._pending_item_name = item_name
                break
        else:
            return
        self._pending_item_choices = [
            c
            for c in self._item_choices
            if c.ui_args.get("item_name") == self._pending_item_name
        ]
        self.mode = "item_target"

    @on(Button.Pressed, "#cat-flee")
    def _on_flee(self) -> None:
        if self._need_action:
            cid = self._need_action.combatant_id
            self.post_message(CombatActionChosen(FleeIntent(actor_id=cid)))

    @on(Button.Pressed, "#btn-back")
    def _on_back(self) -> None:
        self.mode = "category"

    @on(Button.Pressed, ".target-btn")
    def _on_target_selected(self, event: Button.Pressed) -> None:
        """Handle individual target selection in target or spell_target mode."""
        idx_str = event.button.id.replace("target-", "") if event.button.id else ""
        if not idx_str.isdigit():
            return

        idx = int(idx_str)

        if self.mode == "target":
            choices = self._melee_choices
        elif self.mode == "ranged_target":
            choices = self._ranged_choices
        elif self.mode == "spell_target":
            choices = self._pending_spell_choices
        elif self.mode == "item_target":
            choices = self._pending_item_choices
        else:
            return

        if idx >= len(choices):
            return

        self.post_message(CombatActionChosen(choices[idx].intent))

    @on(Button.Pressed, ".spell-btn")
    def _on_spell_selected(self, event: Button.Pressed) -> None:
        """Handle spell selection — either auto-target (AoE) or show target picker."""
        spell_id = (event.button.id or "").replace("spell-", "")
        if not spell_id:
            return

        # Find all choices for this spell
        spell_choices = [
            c for c in self._spell_choices if c.ui_args.get("spell_id") == spell_id
        ]
        if not spell_choices:
            return

        # Check if AoE (num_targets == -1)
        spell_def = SPELL_CATALOG.get(spell_id)
        if spell_def and spell_def.num_targets == -1:
            # AoE — auto-select immediately
            self.post_message(CombatActionChosen(spell_choices[0].intent))
            return

        # Single-target — show target picker
        self._pending_spell_id = spell_id
        self._pending_spell_choices = spell_choices
        self.mode = "spell_target"

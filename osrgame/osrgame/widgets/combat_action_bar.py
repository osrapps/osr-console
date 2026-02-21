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

    - **category**: Show action category buttons (Attack, Ranged, Cast spell, Flee)
    - **target**: Show individual target buttons for the selected category
    - **spell_pick**: Show available spells to pick from
    - **spell_target**: Show individual targets for a single-target spell
    - **idle**: No active PC turn — bar is hidden
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
        # Pending spell for target selection
        self._pending_spell_id: str | None = None
        self._pending_spell_choices: list[ActionChoice] = []

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

        self.mode = "category"

    def clear_action(self) -> None:
        """Clear the bar (combat ended or waiting for monsters)."""
        self._need_action = None
        self._pc_name = ""
        self._melee_choices = []
        self._ranged_choices = []
        self._spell_choices = []
        self.mode = "idle"

    def watch_mode(self, new_mode: str) -> None:
        """Rebuild buttons when mode changes."""
        label = self.query_one("#turn-label", Label)
        container = self.query_one("#action-buttons", Horizontal)
        container.remove_children()

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
        container.mount(Button("Flee", id="cat-flee", disabled=not self._has_flee))

    def _build_target_buttons(
        self, container: Horizontal, choices: list[ActionChoice]
    ) -> None:
        """Build one button per individual target from the action choices."""
        for i, choice in enumerate(choices):
            label = choice.ui_args.get("target_name", "???")
            container.mount(Button(label, id=f"target-{i}"))
        container.mount(Button("Back", id="btn-back", variant="default"))

    def _build_spell_pick_buttons(self, container: Horizontal) -> None:
        """Build buttons for each available spell."""
        seen_spells: set[str] = set()
        for choice in self._spell_choices:
            spell_id = choice.ui_args.get("spell_id", "")
            if spell_id in seen_spells:
                continue
            seen_spells.add(spell_id)
            spell_name = choice.ui_args.get("spell_name", spell_id)
            container.mount(Button(spell_name, id=f"spell-{spell_id}"))
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

    @on(Button.Pressed, "#cat-flee")
    def _on_flee(self) -> None:
        if self._need_action:
            cid = self._need_action.combatant_id
            self.post_message(CombatActionChosen(FleeIntent(actor_id=cid)))

    @on(Button.Pressed, "#btn-back")
    def _on_back(self) -> None:
        self.mode = "category"

    @on(Button.Pressed, "[id^='target-']")
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
        else:
            return

        if idx >= len(choices):
            return

        self.post_message(CombatActionChosen(choices[idx].intent))

    @on(Button.Pressed, "[id^='spell-']")
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

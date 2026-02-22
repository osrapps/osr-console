"""Tests for CombatActionBar choice categorization, routing, and labels."""

from types import MappingProxyType
from unittest.mock import MagicMock

from osrlib.combat.events import ActionChoice, NeedAction
from osrlib.combat.intents import (
    CastSpellIntent,
    FleeIntent,
    MeleeAttackIntent,
    TurnUndeadIntent,
    UseItemIntent,
)
from osrlib.combat.spells import SPELL_CATALOG
from osrgame.widgets.combat_action_bar import CombatActionBar, CombatActionChosen


# ---------------------------------------------------------------------------
# Helpers — synthetic ActionChoice / NeedAction builders
# ---------------------------------------------------------------------------


def _melee_choice(actor: str = "pc:Fighter", target: str = "monster:Goblin #1") -> ActionChoice:
    tname = target.split(":", 1)[1] if ":" in target else target
    return ActionChoice(
        ui_key="attack_target",
        ui_args=MappingProxyType({"target_id": target, "target_name": tname}),
        intent=MeleeAttackIntent(actor_id=actor, target_id=target),
    )


def _flee_choice(actor: str = "pc:Fighter") -> ActionChoice:
    return ActionChoice(
        ui_key="flee",
        ui_args=MappingProxyType({}),
        intent=FleeIntent(actor_id=actor),
    )


def _turn_undead_choice(actor: str = "pc:Cleric") -> ActionChoice:
    return ActionChoice(
        ui_key="turn_undead",
        ui_args=MappingProxyType({}),
        intent=TurnUndeadIntent(actor_id=actor),
    )


def _use_item_choice(
    actor: str = "pc:Fighter",
    item_name: str = "Flask of Oil",
    target: str = "monster:Goblin #1",
) -> ActionChoice:
    tname = target.split(":", 1)[1] if ":" in target else target
    return ActionChoice(
        ui_key="use_item",
        ui_args=MappingProxyType(
            {"item_name": item_name, "target_id": target, "target_name": tname}
        ),
        intent=UseItemIntent(actor_id=actor, item_name=item_name, target_ids=(target,)),
    )


def _cast_spell_choice(
    actor: str = "pc:Cleric",
    spell_id: str = "hold_person",
    spell_name: str = "Hold Person",
    target: str = "monster:Goblin #1",
    target_ids: tuple[str, ...] | None = None,
) -> ActionChoice:
    tname = target.split(":", 1)[1] if ":" in target else target
    tids = target_ids or (target,)
    return ActionChoice(
        ui_key="cast_spell",
        ui_args=MappingProxyType(
            {"spell_id": spell_id, "spell_name": spell_name, "target_name": tname}
        ),
        intent=CastSpellIntent(
            actor_id=actor, spell_id=spell_id, slot_level=2, target_ids=tids
        ),
    )


def _need_action(combatant_id: str, choices: list[ActionChoice]) -> NeedAction:
    return NeedAction(combatant_id=combatant_id, available=tuple(choices))


# ---------------------------------------------------------------------------
# Choice categorization tests
# ---------------------------------------------------------------------------


class TestChoiceCategorization:
    """Verify set_need_action sorts choices into the correct internal lists."""

    def test_categorizes_turn_undead(self):
        bar = CombatActionBar()
        na = _need_action("pc:Cleric", [_melee_choice("pc:Cleric"), _turn_undead_choice()])
        bar.set_need_action(na)
        assert len(bar._turn_undead_choices) == 1
        assert isinstance(bar._turn_undead_choices[0].intent, TurnUndeadIntent)

    def test_categorizes_use_item(self):
        bar = CombatActionBar()
        choices = [
            _use_item_choice(target="monster:Goblin #1"),
            _use_item_choice(target="monster:Goblin #2"),
        ]
        na = _need_action("pc:Fighter", choices)
        bar.set_need_action(na)
        assert len(bar._item_choices) == 2

    def test_clear_resets_new_lists(self):
        bar = CombatActionBar()
        na = _need_action(
            "pc:Cleric",
            [
                _turn_undead_choice(),
                _use_item_choice(actor="pc:Cleric"),
            ],
        )
        bar.set_need_action(na)
        assert bar._turn_undead_choices
        assert bar._item_choices

        bar.clear_action()
        assert bar._turn_undead_choices == []
        assert bar._item_choices == []
        assert bar._pending_item_name is None
        assert bar._pending_item_choices == []
        assert bar.mode == "idle"


# ---------------------------------------------------------------------------
# Target label tests
# ---------------------------------------------------------------------------


class TestTargetLabel:
    """Verify _target_label enriches 'enemy group' with dice info."""

    def test_group_target_label_shows_dice(self):
        """Hold Person's 'enemy group' choice should show '(1d4)'."""
        assert "hold_person" in SPELL_CATALOG, "hold_person must be in SPELL_CATALOG"
        choice = _cast_spell_choice(
            target="enemy group",
            target_ids=("monster:Goblin #1", "monster:Goblin #2"),
        )
        label = CombatActionBar._target_label("enemy group", choice)
        assert label == "Enemy group (1d4)"

    def test_group_target_label_plain_for_regular_spell(self):
        """A spell without group_target_dice keeps the plain target name."""
        choice = _cast_spell_choice(
            spell_id="magic_missile",
            spell_name="Magic Missile",
            target="Goblin #1",
        )
        label = CombatActionBar._target_label("Goblin #1", choice)
        assert label == "Goblin #1"

    def test_non_group_target_unchanged(self):
        """Normal monster names pass through unchanged."""
        choice = _melee_choice()
        label = CombatActionBar._target_label("Goblin #1", choice)
        assert label == "Goblin #1"


# ---------------------------------------------------------------------------
# Category button visibility (logic-level)
# ---------------------------------------------------------------------------


class TestCategoryButtonVisibility:
    """Verify that _build_category_buttons conditionally mounts turn undead/item buttons."""

    def _get_mounted_ids(self, bar: CombatActionBar) -> list[str]:
        """Call _build_category_buttons with a mock container, return button ids."""
        container = MagicMock()
        mounted_buttons = []
        container.mount = lambda btn: mounted_buttons.append(btn)
        bar._build_category_buttons(container)
        return [b.id for b in mounted_buttons]

    def test_turn_undead_not_shown_without_choices(self):
        bar = CombatActionBar()
        na = _need_action("pc:Fighter", [_melee_choice(), _flee_choice()])
        bar.set_need_action(na)
        ids = self._get_mounted_ids(bar)
        assert "cat-turn-undead" not in ids

    def test_turn_undead_shown_with_choices(self):
        bar = CombatActionBar()
        na = _need_action(
            "pc:Cleric",
            [_melee_choice("pc:Cleric"), _turn_undead_choice(), _flee_choice("pc:Cleric")],
        )
        bar.set_need_action(na)
        ids = self._get_mounted_ids(bar)
        assert "cat-turn-undead" in ids

    def test_use_item_not_shown_without_choices(self):
        bar = CombatActionBar()
        na = _need_action("pc:Fighter", [_melee_choice(), _flee_choice()])
        bar.set_need_action(na)
        ids = self._get_mounted_ids(bar)
        assert "cat-item" not in ids

    def test_use_item_shown_with_choices(self):
        bar = CombatActionBar()
        na = _need_action(
            "pc:Fighter",
            [_melee_choice(), _use_item_choice(), _flee_choice()],
        )
        bar.set_need_action(na)
        ids = self._get_mounted_ids(bar)
        assert "cat-item" in ids


# ---------------------------------------------------------------------------
# Item pick deduplication
# ---------------------------------------------------------------------------


class TestItemPickDeduplication:
    """Verify _build_item_pick_buttons deduplicates by item name."""

    def test_item_pick_deduplicates_by_name(self):
        """2 items x 2 targets = 4 choices but only 2 item buttons."""
        bar = CombatActionBar()
        choices = [
            _use_item_choice(item_name="Flask of Oil", target="monster:Goblin #1"),
            _use_item_choice(item_name="Flask of Oil", target="monster:Goblin #2"),
            _use_item_choice(item_name="Holy Water", target="monster:Goblin #1"),
            _use_item_choice(item_name="Holy Water", target="monster:Goblin #2"),
        ]
        na = _need_action("pc:Fighter", choices)
        bar.set_need_action(na)

        container = MagicMock()
        mounted = []
        container.mount = lambda btn: mounted.append(btn)
        bar._build_item_pick_buttons(container)

        # 2 item buttons + 1 Back button
        item_btns = [b for b in mounted if hasattr(b, "id") and b.id and b.id.startswith("item-")]
        assert len(item_btns) == 2
        labels = {str(b.label) for b in item_btns}
        assert labels == {"Flask of Oil", "Holy Water"}


# ---------------------------------------------------------------------------
# Turn Undead handler
# ---------------------------------------------------------------------------


class TestTurnUndeadHandler:
    """Verify Turn Undead handler posts intent immediately."""

    def test_turn_undead_posts_intent(self):
        bar = CombatActionBar()
        messages: list[CombatActionChosen] = []
        bar.post_message = lambda msg: messages.append(msg)  # type: ignore[assignment]

        na = _need_action(
            "pc:Cleric",
            [_melee_choice("pc:Cleric"), _turn_undead_choice(), _flee_choice("pc:Cleric")],
        )
        bar.set_need_action(na)
        bar._on_turn_undead()

        assert len(messages) == 1
        assert isinstance(messages[0], CombatActionChosen)
        assert isinstance(messages[0].intent, TurnUndeadIntent)
        assert messages[0].intent.actor_id == "pc:Cleric"

    def test_turn_undead_no_op_without_choices(self):
        bar = CombatActionBar()
        messages: list[CombatActionChosen] = []
        bar.post_message = lambda msg: messages.append(msg)  # type: ignore[assignment]

        na = _need_action("pc:Fighter", [_melee_choice(), _flee_choice()])
        bar.set_need_action(na)
        bar._on_turn_undead()

        assert len(messages) == 0


# ---------------------------------------------------------------------------
# Item selection → target filtering
# ---------------------------------------------------------------------------


class TestItemTargetRouting:
    """Verify item selection filters targets for the chosen item."""

    def test_item_selected_filters_targets(self):
        bar = CombatActionBar()
        choices = [
            _use_item_choice(item_name="Flask of Oil", target="monster:Goblin #1"),
            _use_item_choice(item_name="Flask of Oil", target="monster:Goblin #2"),
            _use_item_choice(item_name="Holy Water", target="monster:Goblin #1"),
            _use_item_choice(item_name="Holy Water", target="monster:Goblin #2"),
        ]
        na = _need_action("pc:Fighter", choices)
        bar.set_need_action(na)

        # Simulate selecting "Flask of Oil" via the handler
        event = MagicMock()
        event.button.id = "item-flask-of-oil"
        bar._on_item_selected(event)

        assert bar._pending_item_name == "Flask of Oil"
        assert len(bar._pending_item_choices) == 2
        assert all(
            c.ui_args.get("item_name") == "Flask of Oil" for c in bar._pending_item_choices
        )
        assert bar.mode == "item_target"

    def test_target_selected_in_item_mode(self):
        bar = CombatActionBar()
        choices = [
            _use_item_choice(item_name="Flask of Oil", target="monster:Goblin #1"),
            _use_item_choice(item_name="Flask of Oil", target="monster:Goblin #2"),
        ]
        na = _need_action("pc:Fighter", choices)
        bar.set_need_action(na)

        # Set up item_target mode
        bar._pending_item_name = "Flask of Oil"
        bar._pending_item_choices = list(choices)
        bar.mode = "item_target"

        messages: list[CombatActionChosen] = []
        bar.post_message = lambda msg: messages.append(msg)  # type: ignore[assignment]

        # Simulate clicking target-0
        event = MagicMock()
        event.button.id = "target-0"
        bar._on_target_selected(event)

        assert len(messages) == 1
        assert isinstance(messages[0].intent, UseItemIntent)
        assert messages[0].intent.item_name == "Flask of Oil"
        assert messages[0].intent.target_ids == ("monster:Goblin #1",)

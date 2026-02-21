"""Tests for Phase 5: AoE targeting and thrown combat items."""

from osrlib.combat import (
    CombatEngine,
    CombatSide,
    EncounterState,
    NeedAction,
    RejectionCode,
    UseItemAction,
    UseItemIntent,
)
from osrlib.combat.effects import DamageEffect
from osrlib.combat.events import DamageApplied, ItemUsed
from osrlib.combat.actions import THROWABLE_ITEMS
from osrlib.enums import CharacterClassType
from osrlib.item_factories import EquipmentFactory

from conftest import find_events, find_pc_with_class


# ---------------------------------------------------------------------------
# UseItemAction: oil flask
# ---------------------------------------------------------------------------


def test_oil_flask_deals_damage(default_party, goblin_party):
    engine = CombatEngine(
        pc_party=default_party,
        monster_party=goblin_party,
        auto_resolve_intents=False,
    )

    fighter_cid, fighter_pc = find_pc_with_class(engine, CharacterClassType.FIGHTER)
    fighter_pc.inventory.add_item(EquipmentFactory.create_item("Flask of Oil"))
    monster_cid = engine._ctx.living(CombatSide.MONSTER)[0].id
    engine._ctx.current_combatant_id = fighter_cid

    action = UseItemAction(
        actor_id=fighter_cid,
        item_name="Flask of Oil",
        target_ids=(monster_cid,),
    )

    reasons = action.validate(engine._ctx)
    assert reasons == ()

    result = action.execute(engine._ctx)

    item_events = find_events(list(result.events), ItemUsed)
    assert len(item_events) == 1
    assert item_events[0].item_name == "Flask of Oil"

    damage_effects = [e for e in result.effects if isinstance(e, DamageEffect)]
    assert len(damage_effects) == 1
    assert damage_effects[0].amount > 0


def test_holy_water_deals_damage(default_party, goblin_party):
    engine = CombatEngine(
        pc_party=default_party,
        monster_party=goblin_party,
        auto_resolve_intents=False,
    )

    fighter_cid, fighter_pc = find_pc_with_class(engine, CharacterClassType.FIGHTER)
    fighter_pc.inventory.add_item(EquipmentFactory.create_item("Holy Water"))
    monster_cid = engine._ctx.living(CombatSide.MONSTER)[0].id
    engine._ctx.current_combatant_id = fighter_cid

    action = UseItemAction(
        actor_id=fighter_cid,
        item_name="Holy Water",
        target_ids=(monster_cid,),
    )
    reasons = action.validate(engine._ctx)
    assert reasons == ()

    result = action.execute(engine._ctx)
    damage_effects = [e for e in result.effects if isinstance(e, DamageEffect)]
    assert len(damage_effects) == 1


def test_unknown_throwable_rejected(default_party, goblin_party):
    engine = CombatEngine(
        pc_party=default_party,
        monster_party=goblin_party,
        auto_resolve_intents=False,
    )

    fighter_cid, _ = find_pc_with_class(engine, CharacterClassType.FIGHTER)
    monster_cid = engine._ctx.living(CombatSide.MONSTER)[0].id
    engine._ctx.current_combatant_id = fighter_cid

    action = UseItemAction(
        actor_id=fighter_cid,
        item_name="Mysterious Orb",
        target_ids=(monster_cid,),
    )
    reasons = action.validate(engine._ctx)
    assert len(reasons) == 1
    assert reasons[0].code == RejectionCode.ITEM_NOT_THROWABLE


def test_item_not_in_inventory_rejected(default_party, goblin_party):
    """Validate rejects UseItemAction when the actor doesn't have the item."""
    engine = CombatEngine(
        pc_party=default_party,
        monster_party=goblin_party,
        auto_resolve_intents=False,
    )

    fighter_cid, fighter_pc = find_pc_with_class(engine, CharacterClassType.FIGHTER)
    monster_cid = engine._ctx.living(CombatSide.MONSTER)[0].id
    engine._ctx.current_combatant_id = fighter_cid

    # Remove all oil flasks from inventory
    to_remove = [
        item for item in fighter_pc.inventory.equipment
        if item.name == "Flask of Oil"
    ]
    for item in to_remove:
        fighter_pc.inventory.remove_item(item)

    action = UseItemAction(
        actor_id=fighter_cid,
        item_name="Flask of Oil",
        target_ids=(monster_cid,),
    )
    reasons = action.validate(engine._ctx)
    assert len(reasons) == 1
    assert reasons[0].code == RejectionCode.ITEM_NOT_IN_INVENTORY


def test_item_consumed_after_throw(default_party, goblin_party):
    """Throwing an oil flask removes it from the actor's inventory."""
    engine = CombatEngine(
        pc_party=default_party,
        monster_party=goblin_party,
        auto_resolve_intents=False,
    )

    fighter_cid, fighter_pc = find_pc_with_class(engine, CharacterClassType.FIGHTER)
    fighter_pc.inventory.add_item(EquipmentFactory.create_item("Flask of Oil"))
    fighter_pc.inventory.add_item(EquipmentFactory.create_item("Flask of Oil"))
    monster_cid = engine._ctx.living(CombatSide.MONSTER)[0].id
    engine._ctx.current_combatant_id = fighter_cid

    oil_count_before = sum(
        1 for item in fighter_pc.inventory.equipment if item.name == "Flask of Oil"
    )
    assert oil_count_before == 2

    action = UseItemAction(
        actor_id=fighter_cid,
        item_name="Flask of Oil",
        target_ids=(monster_cid,),
    )
    result = action.execute(engine._ctx)

    # Apply effects through the engine to trigger ConsumeItemEffect
    engine._pending_effects = result.effects
    events = []
    engine._handle_apply_effects(events)

    oil_count_after = sum(
        1 for item in fighter_pc.inventory.equipment if item.name == "Flask of Oil"
    )
    assert oil_count_after == oil_count_before - 1


# ---------------------------------------------------------------------------
# UseItemIntent -> UseItemAction mapping
# ---------------------------------------------------------------------------


def test_use_item_intent_maps_to_action(default_party, goblin_party):
    engine = CombatEngine(
        pc_party=default_party,
        monster_party=goblin_party,
        auto_resolve_intents=False,
    )

    fighter_cid, _ = find_pc_with_class(engine, CharacterClassType.FIGHTER)
    monster_cid = engine._ctx.living(CombatSide.MONSTER)[0].id
    engine._ctx.current_combatant_id = fighter_cid

    intent = UseItemIntent(
        actor_id=fighter_cid,
        item_name="Flask of Oil",
        target_ids=(monster_cid,),
    )

    action = engine._action_for_intent(intent)
    assert isinstance(action, UseItemAction)
    assert action.item_name == "Flask of Oil"


# ---------------------------------------------------------------------------
# Choice generation includes throwable items
# ---------------------------------------------------------------------------


def test_choices_include_throwable_items(default_party, goblin_party):
    engine = CombatEngine(
        pc_party=default_party,
        monster_party=goblin_party,
        auto_resolve_intents=False,
    )

    fighter_cid, fighter_pc = find_pc_with_class(engine, CharacterClassType.FIGHTER)
    oil = EquipmentFactory.create_item("Flask of Oil")
    fighter_pc.inventory.add_item(oil)

    engine._ctx.turn_queue.clear()
    engine._ctx.turn_queue.append(fighter_cid)
    engine._state = EncounterState.TURN_START
    engine._ctx.round_number = 1

    result = engine.step()
    need_actions = find_events(list(result.events), NeedAction)
    assert len(need_actions) == 1

    item_choices = [c for c in need_actions[0].available if c.ui_key == "use_item"]
    assert len(item_choices) > 0

    oil_choices = [
        c for c in item_choices if c.ui_args.get("item_name") == "Flask of Oil"
    ]
    assert len(oil_choices) > 0
    assert isinstance(oil_choices[0].intent, UseItemIntent)


# ---------------------------------------------------------------------------
# Full pipeline: throw oil flask in combat
# ---------------------------------------------------------------------------


def test_throw_oil_flask_full_pipeline(default_party, goblin_party):
    engine = CombatEngine(
        pc_party=default_party,
        monster_party=goblin_party,
        auto_resolve_intents=False,
    )

    fighter_cid, fighter_pc = find_pc_with_class(engine, CharacterClassType.FIGHTER)
    fighter_pc.inventory.add_item(EquipmentFactory.create_item("Flask of Oil"))
    monster_cid = engine._ctx.living(CombatSide.MONSTER)[0].id

    engine._ctx.turn_queue.clear()
    engine._ctx.turn_queue.append(fighter_cid)
    engine._state = EncounterState.TURN_START
    engine._ctx.round_number = 1

    engine.step()

    intent = UseItemIntent(
        actor_id=fighter_cid,
        item_name="Flask of Oil",
        target_ids=(monster_cid,),
    )
    results = engine.step_until_decision(intent=intent)
    all_events = [e for r in results for e in r.events]

    item_events = find_events(all_events, ItemUsed)
    assert len(item_events) == 1

    damage_events = find_events(all_events, DamageApplied)
    assert len(damage_events) >= 1


# ---------------------------------------------------------------------------
# Throwable items data
# ---------------------------------------------------------------------------


def test_throwable_items_defined():
    assert "Flask of Oil" in THROWABLE_ITEMS
    assert THROWABLE_ITEMS["Flask of Oil"]["damage_die"] == "1d8"
    assert "Holy Water" in THROWABLE_ITEMS
    assert THROWABLE_ITEMS["Holy Water"]["damage_die"] == "1d8"

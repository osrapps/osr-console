"""Tests for Phase 5: AoE targeting and thrown combat items."""

import pytest

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
from osrlib.combat.events import ItemUsed
from osrlib.combat.actions import THROWABLE_ITEMS
from osrlib.enums import CharacterClassType
from osrlib.item_factories import equip_party, EquipmentFactory
from osrlib.monster import MonsterParty, MonsterStatsBlock
from osrlib.party import Party
from osrlib.player_character import Alignment, PlayerCharacter
from osrlib.treasure import TreasureType


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def default_party():
    party = Party.get_default_party()
    equip_party(party)
    return party


@pytest.fixture
def goblin_stats():
    return MonsterStatsBlock(
        name="Goblin",
        description="A small ugly humanoid.",
        armor_class=6,
        hit_dice="1d8",
        num_appearing="2",
        movement=60,
        num_special_abilities=0,
        attacks_per_round=1,
        damage_per_attack="1d6",
        save_as_class=CharacterClassType.FIGHTER,
        save_as_level=1,
        morale=7,
        treasure_type=TreasureType.NONE,
        alignment=Alignment.CHAOTIC,
    )


@pytest.fixture
def goblin_party(goblin_stats):
    return MonsterParty(goblin_stats)


def _find_events(events, event_type):
    return [e for e in events if isinstance(e, event_type)]


def _find_pc_with_class(engine, class_type):
    for cid, ref in engine._ctx.combatants.items():
        if ref.side == CombatSide.PC and isinstance(ref.entity, PlayerCharacter):
            if ref.entity.character_class.class_type == class_type:
                return cid, ref.entity
    pytest.skip(f"No {class_type.value} in party")


# ---------------------------------------------------------------------------
# UseItemAction: oil flask
# ---------------------------------------------------------------------------


def test_oil_flask_deals_damage(default_party, goblin_party):
    engine = CombatEngine(
        pc_party=default_party,
        monster_party=goblin_party,
        auto_resolve_intents=False,
    )

    fighter_cid, fighter_pc = _find_pc_with_class(engine, CharacterClassType.FIGHTER)
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

    # Should have ItemUsed event
    item_events = _find_events(list(result.events), ItemUsed)
    assert len(item_events) == 1
    assert item_events[0].item_name == "Flask of Oil"

    # Should have DamageEffect
    damage_effects = [e for e in result.effects if isinstance(e, DamageEffect)]
    assert len(damage_effects) == 1
    assert damage_effects[0].amount > 0


def test_holy_water_deals_damage(default_party, goblin_party):
    engine = CombatEngine(
        pc_party=default_party,
        monster_party=goblin_party,
        auto_resolve_intents=False,
    )

    fighter_cid, _ = _find_pc_with_class(engine, CharacterClassType.FIGHTER)
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

    fighter_cid, _ = _find_pc_with_class(engine, CharacterClassType.FIGHTER)
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


# ---------------------------------------------------------------------------
# UseItemIntent → UseItemAction mapping
# ---------------------------------------------------------------------------


def test_use_item_intent_maps_to_action(default_party, goblin_party):
    engine = CombatEngine(
        pc_party=default_party,
        monster_party=goblin_party,
        auto_resolve_intents=False,
    )

    fighter_cid, _ = _find_pc_with_class(engine, CharacterClassType.FIGHTER)
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

    # Find a fighter and give them a flask of oil
    fighter_cid, fighter_pc = _find_pc_with_class(engine, CharacterClassType.FIGHTER)
    oil = EquipmentFactory.create_item("Flask of Oil")
    fighter_pc.inventory.add_item(oil)

    engine._ctx.turn_queue.clear()
    engine._ctx.turn_queue.append(fighter_cid)
    engine._state = EncounterState.TURN_START
    engine._ctx.round_number = 1

    result = engine.step()
    need_actions = _find_events(list(result.events), NeedAction)
    assert len(need_actions) == 1

    item_choices = [c for c in need_actions[0].available if c.ui_key == "use_item"]
    assert len(item_choices) > 0

    # Verify it's an oil flask choice
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

    fighter_cid, _ = _find_pc_with_class(engine, CharacterClassType.FIGHTER)
    monster_cid = engine._ctx.living(CombatSide.MONSTER)[0].id

    # Force fighter's turn
    engine._ctx.turn_queue.clear()
    engine._ctx.turn_queue.append(fighter_cid)
    engine._state = EncounterState.TURN_START
    engine._ctx.round_number = 1

    # Step to get NeedAction
    engine.step()

    # Submit UseItemIntent
    intent = UseItemIntent(
        actor_id=fighter_cid,
        item_name="Flask of Oil",
        target_ids=(monster_cid,),
    )
    results = engine.step_until_decision(intent=intent)
    all_events = [e for r in results for e in r.events]

    # Should have ItemUsed event
    item_events = _find_events(all_events, ItemUsed)
    assert len(item_events) == 1

    from osrlib.combat.events import DamageApplied

    # Should have damage applied
    damage_events = _find_events(all_events, DamageApplied)
    assert len(damage_events) >= 1


# ---------------------------------------------------------------------------
# Throwable items data
# ---------------------------------------------------------------------------


def test_throwable_items_defined():
    assert "Flask of Oil" in THROWABLE_ITEMS
    assert THROWABLE_ITEMS["Flask of Oil"]["damage_die"] == "1d8"
    assert "Holy Water" in THROWABLE_ITEMS
    assert THROWABLE_ITEMS["Holy Water"]["damage_die"] == "1d8"

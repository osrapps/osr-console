"""Tests for Phase 2: healing spells and targeting modes."""

import pytest

from osrlib.combat import (
    CastSpellAction,
    CastSpellIntent,
    CombatEngine,
    CombatSide,
    EncounterState,
    NeedAction,
    RejectionCode,
)
from osrlib.combat.effects import HealEffect
from osrlib.combat.events import HealingApplied
from osrlib.combat.targeting import TargetMode
from osrlib.enums import CharacterClassType
from osrlib.item_factories import equip_party
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
    # Level up Cleric to level 2 so they get spell slots
    for pc in party.members:
        if pc.character_class.class_type == CharacterClassType.CLERIC:
            pc.grant_xp(1500)
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
# Cure Light Wounds heals ally
# ---------------------------------------------------------------------------


def test_cure_light_wounds_heals_ally(default_party, goblin_party):
    engine = CombatEngine(
        pc_party=default_party,
        monster_party=goblin_party,
        auto_resolve_intents=False,
    )

    cleric_cid, cleric_pc = _find_pc_with_class(engine, CharacterClassType.CLERIC)

    # Find a PC to heal (damage them first)
    fighter_cid, fighter_pc = _find_pc_with_class(engine, CharacterClassType.FIGHTER)
    original_hp = fighter_pc.hit_points
    damage = min(2, original_hp - 1)  # don't kill them
    fighter_pc.apply_damage(damage)
    assert fighter_pc.hit_points == original_hp - damage

    engine._ctx.current_combatant_id = cleric_cid

    action = CastSpellAction(
        actor_id=cleric_cid,
        spell_id="cure_light_wounds",
        slot_level=1,
        target_ids=(fighter_cid,),
    )

    # Validate — should pass (ally targeting)
    reasons = action.validate(engine._ctx)
    assert reasons == ()

    result = action.execute(engine._ctx)

    # Should have HealEffect
    heal_effects = [e for e in result.effects if isinstance(e, HealEffect)]
    assert len(heal_effects) == 1
    assert heal_effects[0].target_id == fighter_cid
    assert heal_effects[0].amount > 0

    # Apply via engine
    engine._pending_effects = result.effects
    events = []
    engine._handle_apply_effects(events)

    healing_events = _find_events(events, HealingApplied)
    assert len(healing_events) == 1
    assert healing_events[0].target_id == fighter_cid
    assert fighter_pc.hit_points > original_hp - damage


def test_cure_light_wounds_capped_at_max_hp(default_party, goblin_party):
    engine = CombatEngine(
        pc_party=default_party,
        monster_party=goblin_party,
        auto_resolve_intents=False,
    )

    cleric_cid, cleric_pc = _find_pc_with_class(engine, CharacterClassType.CLERIC)

    # Find a PC at full HP
    fighter_cid, fighter_pc = _find_pc_with_class(engine, CharacterClassType.FIGHTER)
    max_hp = fighter_pc.max_hit_points
    # Only do 1 damage
    fighter_pc.apply_damage(1)

    engine._ctx.current_combatant_id = cleric_cid

    action = CastSpellAction(
        actor_id=cleric_cid,
        spell_id="cure_light_wounds",
        slot_level=1,
        target_ids=(fighter_cid,),
    )
    result = action.execute(engine._ctx)

    # Apply healing
    engine._pending_effects = result.effects
    events = []
    engine._handle_apply_effects(events)

    # HP should not exceed max
    assert fighter_pc.hit_points <= max_hp


def test_heal_targeting_enemy_rejected(default_party, goblin_party):
    engine = CombatEngine(
        pc_party=default_party,
        monster_party=goblin_party,
        auto_resolve_intents=False,
    )

    cleric_cid, _ = _find_pc_with_class(engine, CharacterClassType.CLERIC)
    monster_cid = engine._ctx.living(CombatSide.MONSTER)[0].id

    engine._ctx.current_combatant_id = cleric_cid

    action = CastSpellAction(
        actor_id=cleric_cid,
        spell_id="cure_light_wounds",
        slot_level=1,
        target_ids=(monster_cid,),
    )
    reasons = action.validate(engine._ctx)
    assert len(reasons) == 1
    assert reasons[0].code == RejectionCode.TARGET_NOT_ALLY


def test_self_targeting_spell():
    """Verify SELF target_mode exists in TargetMode."""
    assert TargetMode.SELF is not None


def test_all_allies_targeting():
    """Verify ALL_ALLIES target_mode exists in TargetMode."""
    assert TargetMode.ALL_ALLIES is not None


# ---------------------------------------------------------------------------
# Choice generation includes ally spells
# ---------------------------------------------------------------------------


def test_choices_include_ally_spells(default_party, goblin_party):
    engine = CombatEngine(
        pc_party=default_party,
        monster_party=goblin_party,
        auto_resolve_intents=False,
    )

    cleric_cid, cleric_pc = _find_pc_with_class(engine, CharacterClassType.CLERIC)

    # Verify cleric has CLW in inventory
    known_spells = {s.name for s in cleric_pc.inventory.spells}
    assert "Cure Light Wounds" in known_spells

    engine._ctx.turn_queue.clear()
    engine._ctx.turn_queue.append(cleric_cid)
    engine._state = EncounterState.TURN_START
    engine._ctx.round_number = 1

    result = engine.step()
    need_actions = _find_events(list(result.events), NeedAction)
    assert len(need_actions) == 1

    spell_choices = [c for c in need_actions[0].available if c.ui_key == "cast_spell"]

    # Should have CLW targeting allies
    clw_choices = [
        c for c in spell_choices
        if c.ui_args.get("spell_name") == "Cure Light Wounds"
    ]
    assert len(clw_choices) > 0

    # CLW targets should be PCs (allies), not monsters
    for choice in clw_choices:
        intent = choice.intent
        assert isinstance(intent, CastSpellIntent)
        for tid in intent.target_ids:
            assert tid.startswith("pc:"), f"CLW target {tid} should be a PC"

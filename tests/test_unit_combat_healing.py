"""Tests for Phase 2: healing spells and targeting modes."""

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
from osrlib.enums import CharacterClassType

from conftest import find_events, find_pc_with_class


# ---------------------------------------------------------------------------
# Cure Light Wounds heals ally
# ---------------------------------------------------------------------------


def test_cure_light_wounds_heals_ally(default_party_with_cleric_spells, goblin_party):
    engine = CombatEngine(
        pc_party=default_party_with_cleric_spells,
        monster_party=goblin_party,
        auto_resolve_intents=False,
    )

    cleric_cid, _ = find_pc_with_class(engine, CharacterClassType.CLERIC)

    fighter_cid, fighter_pc = find_pc_with_class(engine, CharacterClassType.FIGHTER)
    original_hp = fighter_pc.hit_points
    damage = min(2, original_hp - 1)
    fighter_pc.apply_damage(damage)
    assert fighter_pc.hit_points == original_hp - damage

    engine._ctx.current_combatant_id = cleric_cid

    action = CastSpellAction(
        actor_id=cleric_cid,
        spell_id="cure_light_wounds",
        slot_level=1,
        target_ids=(fighter_cid,),
    )

    reasons = action.validate(engine._ctx)
    assert reasons == ()

    result = action.execute(engine._ctx)

    heal_effects = [e for e in result.effects if isinstance(e, HealEffect)]
    assert len(heal_effects) == 1
    assert heal_effects[0].target_id == fighter_cid
    assert heal_effects[0].amount > 0

    engine._pending_effects = result.effects
    events = []
    engine._handle_apply_effects(events)

    healing_events = find_events(events, HealingApplied)
    assert len(healing_events) == 1
    assert healing_events[0].target_id == fighter_cid
    assert fighter_pc.hit_points > original_hp - damage


def test_cure_light_wounds_capped_at_max_hp(default_party_with_cleric_spells, goblin_party):
    engine = CombatEngine(
        pc_party=default_party_with_cleric_spells,
        monster_party=goblin_party,
        auto_resolve_intents=False,
    )

    cleric_cid, _ = find_pc_with_class(engine, CharacterClassType.CLERIC)
    fighter_cid, fighter_pc = find_pc_with_class(engine, CharacterClassType.FIGHTER)
    max_hp = fighter_pc.max_hit_points
    fighter_pc.apply_damage(1)

    engine._ctx.current_combatant_id = cleric_cid

    action = CastSpellAction(
        actor_id=cleric_cid,
        spell_id="cure_light_wounds",
        slot_level=1,
        target_ids=(fighter_cid,),
    )
    result = action.execute(engine._ctx)

    engine._pending_effects = result.effects
    events = []
    engine._handle_apply_effects(events)

    assert fighter_pc.hit_points <= max_hp


def test_heal_targeting_enemy_rejected(default_party_with_cleric_spells, goblin_party):
    engine = CombatEngine(
        pc_party=default_party_with_cleric_spells,
        monster_party=goblin_party,
        auto_resolve_intents=False,
    )

    cleric_cid, _ = find_pc_with_class(engine, CharacterClassType.CLERIC)
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


# ---------------------------------------------------------------------------
# Choice generation includes ally spells
# ---------------------------------------------------------------------------


def test_choices_include_ally_spells(default_party_with_cleric_spells, goblin_party):
    engine = CombatEngine(
        pc_party=default_party_with_cleric_spells,
        monster_party=goblin_party,
        auto_resolve_intents=False,
    )

    cleric_cid, cleric_pc = find_pc_with_class(engine, CharacterClassType.CLERIC)

    known_spells = {s.name for s in cleric_pc.inventory.spells}
    assert "Cure Light Wounds" in known_spells

    engine._ctx.turn_queue.clear()
    engine._ctx.turn_queue.append(cleric_cid)
    engine._state = EncounterState.TURN_START
    engine._ctx.round_number = 1

    result = engine.step()
    need_actions = find_events(list(result.events), NeedAction)
    assert len(need_actions) == 1

    spell_choices = [c for c in need_actions[0].available if c.ui_key == "cast_spell"]

    clw_choices = [
        c for c in spell_choices
        if c.ui_args.get("spell_name") == "Cure Light Wounds"
    ]
    assert len(clw_choices) > 0

    for choice in clw_choices:
        intent = choice.intent
        assert isinstance(intent, CastSpellIntent)
        for tid in intent.target_ids:
            assert tid.startswith("pc:"), f"CLW target {tid} should be a PC"

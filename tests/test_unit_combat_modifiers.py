"""Tests for Phase 3: buff/debuff modifiers."""

from osrlib.combat import (
    CastSpellAction,
    CombatEngine,
    CombatSide,
    EncounterState,
    MeleeAttackAction,
)
from osrlib.combat.effects import ApplyModifierEffect
from osrlib.combat.events import AttackRolled, ModifierApplied, ModifierExpired
from osrlib.combat.modifiers import ActiveModifier, ModifiedStat, ModifierTracker
from osrlib.dice_roller import DiceRoll
from osrlib.enums import CharacterClassType

from conftest import find_events, find_pc_with_class


# ---------------------------------------------------------------------------
# ModifierTracker unit tests
# ---------------------------------------------------------------------------


class TestModifierTracker:
    def test_add_and_get_total(self):
        tracker = ModifierTracker()
        tracker.add(
            "pc:Alice",
            ActiveModifier("bless_atk", "pc:Cleric", ModifiedStat.ATTACK, 1, 6),
        )
        assert tracker.get_total("pc:Alice", ModifiedStat.ATTACK) == 1
        assert tracker.get_total("pc:Alice", ModifiedStat.ARMOR_CLASS) == 0

    def test_multiple_modifiers_stack(self):
        tracker = ModifierTracker()
        tracker.add(
            "pc:Alice",
            ActiveModifier("bless_atk", "pc:Cleric", ModifiedStat.ATTACK, 1, 6),
        )
        tracker.add(
            "pc:Alice",
            ActiveModifier("magic_atk", "pc:MU", ModifiedStat.ATTACK, 2, 3),
        )
        assert tracker.get_total("pc:Alice", ModifiedStat.ATTACK) == 3

    def test_tick_round_expires(self):
        tracker = ModifierTracker()
        tracker.add(
            "pc:Alice",
            ActiveModifier("shield_ac", "pc:MU", ModifiedStat.ARMOR_CLASS, -2, 1),
        )
        expired = tracker.tick_round()
        assert ("pc:Alice", "shield_ac") in expired
        assert tracker.get_total("pc:Alice", ModifiedStat.ARMOR_CLASS) == 0

    def test_tick_round_decrements(self):
        tracker = ModifierTracker()
        tracker.add(
            "pc:Alice",
            ActiveModifier("shield_ac", "pc:MU", ModifiedStat.ARMOR_CLASS, -2, 3),
        )
        expired = tracker.tick_round()
        assert len(expired) == 0
        assert tracker.get_total("pc:Alice", ModifiedStat.ARMOR_CLASS) == -2


# ---------------------------------------------------------------------------
# Engine integration: bless adds attack modifier
# ---------------------------------------------------------------------------


def test_bless_adds_attack_modifier(default_party, goblin_party):
    engine = CombatEngine(
        pc_party=default_party,
        monster_party=goblin_party,
        auto_resolve_intents=False,
    )

    cleric_cid, cleric_pc = find_pc_with_class(engine, CharacterClassType.CLERIC)
    cleric_pc.grant_xp(6000)

    pc_ids = tuple(ref.id for ref in engine._ctx.living(CombatSide.PC))

    engine._ctx.current_combatant_id = cleric_cid

    action = CastSpellAction(
        actor_id=cleric_cid,
        spell_id="bless",
        slot_level=2,
        target_ids=pc_ids,
    )

    result = action.execute(engine._ctx)

    mod_effects = [e for e in result.effects if isinstance(e, ApplyModifierEffect)]
    # Bless has 2 modifiers (atk + save), applied to each PC
    expected_count = len(pc_ids) * 2
    assert len(mod_effects) == expected_count

    engine._spell_slots_remaining_by_caster[cleric_cid] = {1: 2, 2: 1}
    engine._pending_effects = result.effects
    events = []
    engine._handle_apply_effects(events)

    applied = find_events(events, ModifierApplied)
    assert len(applied) == expected_count

    for pc_id in pc_ids:
        total = engine._ctx.modifiers.get_total(pc_id, ModifiedStat.ATTACK)
        assert total == 1, f"{pc_id} should have +1 attack from Bless"


def test_shield_reduces_ac(default_party, goblin_party):
    engine = CombatEngine(
        pc_party=default_party,
        monster_party=goblin_party,
        auto_resolve_intents=False,
    )

    mu_cid, _ = find_pc_with_class(engine, CharacterClassType.MAGIC_USER)
    engine._ctx.current_combatant_id = mu_cid

    engine._ctx.modifiers.add(
        mu_cid,
        ActiveModifier("shield_ac", mu_cid, ModifiedStat.ARMOR_CLASS, -2, 12),
    )

    ac_mod = engine._ctx.modifiers.get_total(mu_cid, ModifiedStat.ARMOR_CLASS)
    assert ac_mod == -2


def test_modifier_expires_after_duration(default_party, goblin_party):
    engine = CombatEngine(
        pc_party=default_party,
        monster_party=goblin_party,
        auto_resolve_intents=True,
    )

    pc_cid = engine._ctx.living(CombatSide.PC)[0].id

    engine._ctx.modifiers.add(
        pc_cid,
        ActiveModifier("shield_ac", "pc:MU", ModifiedStat.ARMOR_CLASS, -2, 2),
    )

    # Tick round 1: should still be active
    engine._ctx.round_number = 0
    engine._state = EncounterState.ROUND_START
    events_r1 = []
    engine._handle_round_start(events_r1)
    assert engine._ctx.modifiers.get_total(pc_cid, ModifiedStat.ARMOR_CLASS) == -2

    # Tick round 2: should expire
    engine._state = EncounterState.ROUND_START
    events_r2 = []
    engine._handle_round_start(events_r2)
    assert engine._ctx.modifiers.get_total(pc_cid, ModifiedStat.ARMOR_CLASS) == 0
    expired = find_events(events_r2, ModifierExpired)
    assert len(expired) == 1
    assert expired[0].modifier_id == "shield_ac"


def test_attack_modifier_affects_hit_roll(default_party, goblin_party):
    """A +1 attack modifier from Bless increases the effective attack total."""
    engine = CombatEngine(
        pc_party=default_party,
        monster_party=goblin_party,
        auto_resolve_intents=False,
    )

    fighter_cid, fighter_pc = find_pc_with_class(engine, CharacterClassType.FIGHTER)
    monster_cid = engine._ctx.living(CombatSide.MONSTER)[0].id

    engine._ctx.current_combatant_id = fighter_cid

    action = MeleeAttackAction(actor_id=fighter_cid, target_id=monster_cid)

    # Fix the attack roll to 10 with 0 modifier
    fighter_pc.get_attack_roll = lambda: DiceRoll(1, 20, 10, 0, 10, [10])
    fighter_pc.get_damage_roll = lambda: DiceRoll(1, 8, 5, 0, 5, [5])

    result_no_mod = action.execute(engine._ctx)
    atk_event_no_mod = find_events(list(result_no_mod.events), AttackRolled)[0]
    total_no_mod = atk_event_no_mod.total

    # Add +1 attack modifier
    engine._ctx.modifiers.add(
        fighter_cid,
        ActiveModifier("bless_atk", "pc:Cleric", ModifiedStat.ATTACK, 1, 6),
    )

    result_with_mod = action.execute(engine._ctx)
    atk_event_mod = find_events(list(result_with_mod.events), AttackRolled)[0]
    total_with_mod = atk_event_mod.total

    assert total_with_mod == total_no_mod + 1

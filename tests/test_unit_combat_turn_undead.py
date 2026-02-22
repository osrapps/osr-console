"""Tests for Part 3: Turn Undead class ability."""

import pytest

from osrlib.combat import (
    CombatEngine,
    CombatSide,
    EncounterState,
    NeedAction,
    TurnResult,
    TurnUndeadAction,
)
from osrlib.combat.effects import ApplyConditionEffect, DamageEffect, FleeEffect
from osrlib.combat.events import TurnUndeadAttempted, UndeadTurned
from osrlib.enums import CharacterClassType
from osrlib.monster import Monster, MonsterParty, MonsterStatsBlock
from osrlib.player_character import PlayerCharacter

from conftest import find_events, find_pc_with_class

from osrlib.enums import AbilityType, ModifierType


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _level_up_pc(pc: PlayerCharacter, target_level: int) -> None:
    """Set a PC to *target_level* by writing XP directly, bypassing prime requisite adjustment.

    ``grant_xp`` applies prime-requisite-based XP modifiers (up to -20% for
    low WIS), which makes tests that depend on specific cleric levels flaky.
    This helper sets ``character_class.xp`` to the exact threshold for each
    intermediate level and calls ``level_up`` one level at a time.
    """
    hp_mod = pc.abilities[AbilityType.CONSTITUTION].modifiers[ModifierType.HP]
    while pc.level < target_level:
        next_xp = pc.character_class.xp_needed_for_next_level
        pc.character_class.xp = next_xp
        leveled = pc.character_class.level_up(hp_mod)
        assert leveled, f"Failed to level {pc.name} to {pc.level + 1}"


def _skeleton_party(count: int = 2) -> MonsterParty:
    stats = MonsterStatsBlock(
        name="Skeleton",
        hit_dice="1d8",
        num_appearing=str(count),
        morale=12,
        is_undead=True,
    )
    return MonsterParty(stats)


def _zombie_party(count: int = 2) -> MonsterParty:
    stats = MonsterStatsBlock(
        name="Zombie",
        hit_dice="2d8",
        num_appearing=str(count),
        morale=12,
        is_undead=True,
    )
    return MonsterParty(stats)


# ---------------------------------------------------------------------------
# is_undead flag tests
# ---------------------------------------------------------------------------


class TestIsUndeadFlag:
    def test_is_undead_flag(self):
        stats = MonsterStatsBlock(
            name="Skeleton", hit_dice="1d8", num_appearing="1", is_undead=True
        )
        monster = Monster(stats)
        assert monster.is_undead is True

    def test_is_undead_default_false(self):
        stats = MonsterStatsBlock(name="Goblin", hit_dice="1d8", num_appearing="1")
        monster = Monster(stats)
        assert monster.is_undead is False

    def test_is_undead_serialization(self):
        stats = MonsterStatsBlock(
            name="Skeleton", hit_dice="1d8", num_appearing="1", is_undead=True
        )
        d = stats.to_dict()
        assert d["is_undead"] is True
        restored = MonsterStatsBlock.from_dict(d)
        assert restored.is_undead is True

    def test_is_undead_deserialization_default(self):
        """Old serialized data without is_undead should default to False."""
        stats = MonsterStatsBlock(name="Goblin", hit_dice="1d8", num_appearing="1")
        d = stats.to_dict()
        del d["is_undead"]
        restored = MonsterStatsBlock.from_dict(d)
        assert restored.is_undead is False


# ---------------------------------------------------------------------------
# Validation tests
# ---------------------------------------------------------------------------


def test_turn_undead_validate_non_cleric(default_party, goblin_party):
    """Non-clerics should be rejected."""
    engine = CombatEngine(
        pc_party=default_party,
        monster_party=goblin_party,
        auto_resolve_intents=False,
    )
    # Find a non-cleric
    for cid, ref in engine._ctx.combatants.items():
        if ref.side == CombatSide.PC and isinstance(ref.entity, PlayerCharacter):
            if ref.entity.character_class.class_type != CharacterClassType.CLERIC:
                engine._ctx.current_combatant_id = cid
                action = TurnUndeadAction(actor_id=cid)
                reasons = action.validate(engine._ctx)
                assert len(reasons) > 0
                assert any("Cleric" in r.message for r in reasons)
                return
    pytest.skip("No non-cleric in party")


def test_turn_undead_validate_no_undead(default_party, goblin_party):
    """Turn Undead should be rejected when no undead enemies present."""
    engine = CombatEngine(
        pc_party=default_party,
        monster_party=goblin_party,
        auto_resolve_intents=False,
    )
    cleric_cid, _ = find_pc_with_class(engine, CharacterClassType.CLERIC)
    engine._ctx.current_combatant_id = cleric_cid

    action = TurnUndeadAction(actor_id=cleric_cid)
    reasons = action.validate(engine._ctx)
    assert len(reasons) > 0
    assert any("undead" in r.message.lower() for r in reasons)


# ---------------------------------------------------------------------------
# Turn Undead execution tests
# ---------------------------------------------------------------------------


def test_turn_undead_impossible(default_party):
    """Level 1 cleric vs 3 HD Wight (tier 4): impossible."""
    stats = MonsterStatsBlock(
        name="Wight",
        hit_dice="3d8",
        num_appearing="1",
        morale=12,
        is_undead=True,
    )
    party = MonsterParty(stats)

    engine = CombatEngine(
        pc_party=default_party,
        monster_party=party,
        auto_resolve_intents=False,
    )

    cleric_cid, _ = find_pc_with_class(engine, CharacterClassType.CLERIC)
    engine._ctx.current_combatant_id = cleric_cid

    action = TurnUndeadAction(actor_id=cleric_cid)
    # Validate should pass (there are undead)
    assert action.validate(engine._ctx) == ()

    result = action.execute(engine._ctx)
    attempt_events = find_events(list(result.events), TurnUndeadAttempted)
    assert len(attempt_events) == 1
    assert attempt_events[0].result is TurnResult.IMPOSSIBLE


def test_turn_undead_success_roll(default_party):
    """Force a successful 2d6 roll against 1 HD skeletons (need 7)."""
    party = _skeleton_party(2)

    engine = CombatEngine(
        pc_party=default_party,
        monster_party=party,
        auto_resolve_intents=False,
    )

    cleric_cid, _ = find_pc_with_class(engine, CharacterClassType.CLERIC)
    engine._ctx.current_combatant_id = cleric_cid

    import osrlib.combat.actions as actions_mod

    original_roll = actions_mod.roll_dice

    call_idx = {"n": 0}

    def mock_roll_dice(expr, *args, **kwargs):
        call_idx["n"] += 1
        if expr == "2d6":
            from osrlib.dice_roller import DiceRoll

            if call_idx["n"] == 1:
                # Turn roll: succeed (7+ needed for level 1 vs tier 1)
                return DiceRoll(2, 6, 8, 0, 8, [4, 4])
            else:
                # HD pool roll
                return DiceRoll(2, 6, 12, 0, 12, [6, 6])
        return original_roll(expr, *args, **kwargs)

    actions_mod.roll_dice = mock_roll_dice
    try:
        action = TurnUndeadAction(actor_id=cleric_cid)
        result = action.execute(engine._ctx)
    finally:
        actions_mod.roll_dice = original_roll

    attempt_events = find_events(list(result.events), TurnUndeadAttempted)
    assert len(attempt_events) == 1
    assert attempt_events[0].result is TurnResult.TURNED

    turned_events = find_events(list(result.events), UndeadTurned)
    assert len(turned_events) > 0
    assert all(not t.destroyed for t in turned_events)


def test_turn_undead_failure_roll(default_party):
    """Force a failed 2d6 roll against 1 HD skeletons (need 7)."""
    party = _skeleton_party(2)

    engine = CombatEngine(
        pc_party=default_party,
        monster_party=party,
        auto_resolve_intents=False,
    )

    cleric_cid, _ = find_pc_with_class(engine, CharacterClassType.CLERIC)
    engine._ctx.current_combatant_id = cleric_cid

    import osrlib.combat.actions as actions_mod

    original_roll = actions_mod.roll_dice

    def mock_roll_dice(expr, *args, **kwargs):
        if expr == "2d6":
            from osrlib.dice_roller import DiceRoll

            return DiceRoll(2, 6, 3, 0, 3, [2, 1])
        return original_roll(expr, *args, **kwargs)

    actions_mod.roll_dice = mock_roll_dice
    try:
        action = TurnUndeadAction(actor_id=cleric_cid)
        result = action.execute(engine._ctx)
    finally:
        actions_mod.roll_dice = original_roll

    attempt_events = find_events(list(result.events), TurnUndeadAttempted)
    assert len(attempt_events) == 1
    assert attempt_events[0].result is TurnResult.FAILED

    turned_events = find_events(list(result.events), UndeadTurned)
    assert len(turned_events) == 0


def test_turn_undead_auto_turn(default_party):
    """Level 2 cleric vs 1 HD skeletons should auto-turn (T on table)."""
    party = _skeleton_party(2)

    engine = CombatEngine(
        pc_party=default_party,
        monster_party=party,
        auto_resolve_intents=False,
    )

    cleric_cid, cleric_pc = find_pc_with_class(engine, CharacterClassType.CLERIC)
    # Level 2: auto-turn (T) for tier 1 skeletons
    _level_up_pc(cleric_pc, 2)
    engine._ctx.current_combatant_id = cleric_cid

    import osrlib.combat.actions as actions_mod

    original_roll = actions_mod.roll_dice

    def mock_roll_dice(expr, *args, **kwargs):
        if expr == "2d6":
            from osrlib.dice_roller import DiceRoll

            # HD pool roll: enough for both
            return DiceRoll(2, 6, 12, 0, 12, [6, 6])
        return original_roll(expr, *args, **kwargs)

    actions_mod.roll_dice = mock_roll_dice
    try:
        action = TurnUndeadAction(actor_id=cleric_cid)
        result = action.execute(engine._ctx)
    finally:
        actions_mod.roll_dice = original_roll

    attempt_events = find_events(list(result.events), TurnUndeadAttempted)
    assert len(attempt_events) == 1
    assert attempt_events[0].result is TurnResult.TURNED

    # Should have flee effects for turned undead
    flee_effects = [e for e in result.effects if isinstance(e, FleeEffect)]
    assert len(flee_effects) > 0


def test_turn_undead_auto_destroy(default_party):
    """Level 4 cleric vs 1 HD skeletons should auto-destroy (D on table)."""
    party = _skeleton_party(2)

    engine = CombatEngine(
        pc_party=default_party,
        monster_party=party,
        auto_resolve_intents=False,
    )

    cleric_cid, cleric_pc = find_pc_with_class(engine, CharacterClassType.CLERIC)
    # Level 4: auto-destroy (D) for tier 1 skeletons
    _level_up_pc(cleric_pc, 4)
    engine._ctx.current_combatant_id = cleric_cid

    import osrlib.combat.actions as actions_mod

    original_roll = actions_mod.roll_dice

    def mock_roll_dice(expr, *args, **kwargs):
        if expr == "2d6":
            from osrlib.dice_roller import DiceRoll

            return DiceRoll(2, 6, 12, 0, 12, [6, 6])
        return original_roll(expr, *args, **kwargs)

    actions_mod.roll_dice = mock_roll_dice
    try:
        action = TurnUndeadAction(actor_id=cleric_cid)
        result = action.execute(engine._ctx)
    finally:
        actions_mod.roll_dice = original_roll

    attempt_events = find_events(list(result.events), TurnUndeadAttempted)
    assert len(attempt_events) == 1
    assert attempt_events[0].result is TurnResult.DESTROYED

    # Should have damage effects for destroyed undead (not flee)
    damage_effects = [e for e in result.effects if isinstance(e, DamageEffect)]
    assert len(damage_effects) > 0
    flee_effects = [e for e in result.effects if isinstance(e, FleeEffect)]
    assert len(flee_effects) == 0


def test_turn_undead_lowest_hd_first(default_party):
    """Multiple undead types, pool limited — should affect lowest HD first."""
    stats_1hd = MonsterStatsBlock(
        name="Skeleton", hit_dice="1d8", num_appearing="1", morale=12, is_undead=True
    )
    stats_3hd = MonsterStatsBlock(
        name="Wight", hit_dice="3d8", num_appearing="1", morale=12, is_undead=True
    )
    party = MonsterParty(stats_1hd)
    party.members = [Monster(stats_1hd), Monster(stats_3hd)]

    engine = CombatEngine(
        pc_party=default_party,
        monster_party=party,
        auto_resolve_intents=False,
    )

    cleric_cid, cleric_pc = find_pc_with_class(engine, CharacterClassType.CLERIC)
    # Level 3: auto-turn (T) on tier 1 skeletons, need 9 on tier 4 Wights
    _level_up_pc(cleric_pc, 3)
    engine._ctx.current_combatant_id = cleric_cid

    import osrlib.combat.actions as actions_mod

    original_roll = actions_mod.roll_dice

    call_idx = {"n": 0}

    def mock_roll_dice(expr, *args, **kwargs):
        call_idx["n"] += 1
        if expr == "2d6":
            from osrlib.dice_roller import DiceRoll

            # HD pool = 2 (only enough for the 1 HD skeleton, not the 3 HD)
            return DiceRoll(2, 6, 2, 0, 2, [1, 1])
        return original_roll(expr, *args, **kwargs)

    actions_mod.roll_dice = mock_roll_dice
    try:
        action = TurnUndeadAction(actor_id=cleric_cid)
        result = action.execute(engine._ctx)
    finally:
        actions_mod.roll_dice = original_roll

    turned_events = find_events(list(result.events), UndeadTurned)
    # Should affect at least 1 (the skeleton) but not the wight
    assert len(turned_events) >= 1
    # First affected should be the skeleton (lower HD)
    assert "Skeleton" in turned_events[0].target_id


def test_turn_undead_at_least_one(default_party):
    """Even low HD pool roll should affect at least 1 undead."""
    party = _zombie_party(2)

    engine = CombatEngine(
        pc_party=default_party,
        monster_party=party,
        auto_resolve_intents=False,
    )

    cleric_cid, cleric_pc = find_pc_with_class(engine, CharacterClassType.CLERIC)
    # Level 3: auto-turn (T) on tier 2 zombies
    _level_up_pc(cleric_pc, 3)
    engine._ctx.current_combatant_id = cleric_cid

    import osrlib.combat.actions as actions_mod

    original_roll = actions_mod.roll_dice

    call_idx = {"n": 0}

    def mock_roll_dice(expr, *args, **kwargs):
        call_idx["n"] += 1
        if expr == "2d6":
            from osrlib.dice_roller import DiceRoll

            # HD pool = 1 (less than zombie's 2 HD, but at least 1 should be affected)
            return DiceRoll(2, 6, 1, 0, 1, [1, 0])
        return original_roll(expr, *args, **kwargs)

    actions_mod.roll_dice = mock_roll_dice
    try:
        action = TurnUndeadAction(actor_id=cleric_cid)
        result = action.execute(engine._ctx)
    finally:
        actions_mod.roll_dice = original_roll

    turned_events = find_events(list(result.events), UndeadTurned)
    assert len(turned_events) >= 1


def test_turn_undead_flee_effect(default_party):
    """Turned undead should get FleeEffect (no separate condition — FleeEffect suffices)."""
    party = _skeleton_party(1)

    engine = CombatEngine(
        pc_party=default_party,
        monster_party=party,
        auto_resolve_intents=False,
    )

    cleric_cid, cleric_pc = find_pc_with_class(engine, CharacterClassType.CLERIC)
    _level_up_pc(cleric_pc, 2)  # auto-turn T for tier 1
    engine._ctx.current_combatant_id = cleric_cid

    import osrlib.combat.actions as actions_mod

    original_roll = actions_mod.roll_dice

    def mock_roll_dice(expr, *args, **kwargs):
        if expr == "2d6":
            from osrlib.dice_roller import DiceRoll

            return DiceRoll(2, 6, 12, 0, 12, [6, 6])
        return original_roll(expr, *args, **kwargs)

    actions_mod.roll_dice = mock_roll_dice
    try:
        action = TurnUndeadAction(actor_id=cleric_cid)
        result = action.execute(engine._ctx)
    finally:
        actions_mod.roll_dice = original_roll

    flee_effects = [e for e in result.effects if isinstance(e, FleeEffect)]
    assert len(flee_effects) == 1
    # No ApplyConditionEffect — FleeEffect alone handles turned undead
    condition_effects = [
        e for e in result.effects if isinstance(e, ApplyConditionEffect)
    ]
    assert len(condition_effects) == 0


def test_turn_undead_destroy_effect(default_party):
    """Destroyed undead should get DamageEffect equal to their HP."""
    party = _skeleton_party(1)

    engine = CombatEngine(
        pc_party=default_party,
        monster_party=party,
        auto_resolve_intents=False,
    )

    cleric_cid, cleric_pc = find_pc_with_class(engine, CharacterClassType.CLERIC)
    _level_up_pc(cleric_pc, 4)  # auto-destroy D for tier 1
    engine._ctx.current_combatant_id = cleric_cid

    monster_ref = engine._ctx.living(CombatSide.MONSTER)[0]
    monster_hp = monster_ref.entity.hit_points

    import osrlib.combat.actions as actions_mod

    original_roll = actions_mod.roll_dice

    def mock_roll_dice(expr, *args, **kwargs):
        if expr == "2d6":
            from osrlib.dice_roller import DiceRoll

            return DiceRoll(2, 6, 12, 0, 12, [6, 6])
        return original_roll(expr, *args, **kwargs)

    actions_mod.roll_dice = mock_roll_dice
    try:
        action = TurnUndeadAction(actor_id=cleric_cid)
        result = action.execute(engine._ctx)
    finally:
        actions_mod.roll_dice = original_roll

    damage_effects = [e for e in result.effects if isinstance(e, DamageEffect)]
    assert len(damage_effects) == 1
    assert damage_effects[0].amount == monster_hp


# ---------------------------------------------------------------------------
# Engine integration: choices
# ---------------------------------------------------------------------------


def test_turn_undead_choice_for_cleric(default_party):
    """Cleric should see a Turn Undead choice when undead enemies present."""
    party = _skeleton_party(2)

    engine = CombatEngine(
        pc_party=default_party,
        monster_party=party,
        auto_resolve_intents=False,
    )

    cleric_cid, _ = find_pc_with_class(engine, CharacterClassType.CLERIC)

    engine._ctx.turn_queue.clear()
    engine._ctx.turn_queue.append(cleric_cid)
    engine._state = EncounterState.TURN_START
    engine._ctx.round_number = 1

    result = engine.step()
    need_actions = find_events(list(result.events), NeedAction)
    assert len(need_actions) == 1

    turn_choices = [c for c in need_actions[0].available if c.ui_key == "turn_undead"]
    assert len(turn_choices) == 1


def test_turn_undead_no_choice_without_undead(default_party, goblin_party):
    """Turn Undead choice should NOT appear when no undead enemies."""
    engine = CombatEngine(
        pc_party=default_party,
        monster_party=goblin_party,
        auto_resolve_intents=False,
    )

    cleric_cid, _ = find_pc_with_class(engine, CharacterClassType.CLERIC)

    engine._ctx.turn_queue.clear()
    engine._ctx.turn_queue.append(cleric_cid)
    engine._state = EncounterState.TURN_START
    engine._ctx.round_number = 1

    result = engine.step()
    need_actions = find_events(list(result.events), NeedAction)
    assert len(need_actions) == 1

    turn_choices = [c for c in need_actions[0].available if c.ui_key == "turn_undead"]
    assert len(turn_choices) == 0


# ---------------------------------------------------------------------------
# Per-tier turn checks (BUG-6 regression tests)
# ---------------------------------------------------------------------------


def test_turn_undead_mixed_tiers_high_tier_impossible(default_party):
    """Level 2 cleric vs Skeleton (tier 1) + Vampire (tier 8): skeleton turned, vampire unaffected."""
    stats_skel = MonsterStatsBlock(
        name="Skeleton", hit_dice="1d8", num_appearing="1", morale=12, is_undead=True
    )
    stats_vamp = MonsterStatsBlock(
        name="Vampire", hit_dice="8d8", num_appearing="1", morale=12, is_undead=True
    )
    party = MonsterParty(stats_skel)
    party.members = [Monster(stats_skel), Monster(stats_vamp)]

    engine = CombatEngine(
        pc_party=default_party,
        monster_party=party,
        auto_resolve_intents=False,
    )

    cleric_cid, cleric_pc = find_pc_with_class(engine, CharacterClassType.CLERIC)
    _level_up_pc(cleric_pc, 2)
    engine._ctx.current_combatant_id = cleric_cid

    import osrlib.combat.actions as actions_mod

    original_roll = actions_mod.roll_dice

    def mock_roll_dice(expr, *args, **kwargs):
        if expr == "2d6":
            from osrlib.dice_roller import DiceRoll

            # HD pool = 12 (plenty for both if eligible)
            return DiceRoll(2, 6, 12, 0, 12, [6, 6])
        return original_roll(expr, *args, **kwargs)

    actions_mod.roll_dice = mock_roll_dice
    try:
        action = TurnUndeadAction(actor_id=cleric_cid)
        result = action.execute(engine._ctx)
    finally:
        actions_mod.roll_dice = original_roll

    # Should succeed overall (skeleton is tier 1, auto-turn for level 2)
    attempt_events = find_events(list(result.events), TurnUndeadAttempted)
    assert len(attempt_events) == 1
    assert attempt_events[0].result is TurnResult.TURNED

    turned_events = find_events(list(result.events), UndeadTurned)
    # Only skeleton should be affected — vampire tier 8 is impossible at level 2
    assert len(turned_events) == 1
    assert "Skeleton" in turned_events[0].target_id

"""Tests for Part 2: ENEMY_GROUP random targeting (Hold Person)."""

import pytest

from osrlib.combat import (
    CastSpellAction,
    CombatEngine,
    CombatSide,
    EncounterState,
    NeedAction,
)
from osrlib.combat.effects import ApplyConditionEffect
from osrlib.combat.events import GroupTargetsResolved, SavingThrowRolled
from osrlib.combat.spells import get_spell
from osrlib.combat.targeting import resolve_random_group
from osrlib.enums import AbilityType, CharacterClassType, ModifierType
from osrlib.monster import Monster, MonsterParty, MonsterStatsBlock
from osrlib.player_character import Alignment, PlayerCharacter
from osrlib.treasure import TreasureType

from conftest import find_events, find_pc_with_class


# ---------------------------------------------------------------------------
# Pure function tests: resolve_random_group
# ---------------------------------------------------------------------------


class TestResolveRandomGroup:
    def test_basic(self):
        candidates = ("a", "b", "c", "d")
        result = resolve_random_group(candidates, 2)
        assert len(result) == 2
        assert all(r in candidates for r in result)

    def test_capped(self):
        """Count exceeds candidates — returns all."""
        candidates = ("a", "b")
        result = resolve_random_group(candidates, 10)
        assert set(result) == {"a", "b"}

    def test_zero(self):
        result = resolve_random_group(("a", "b"), 0)
        assert result == ()

    def test_empty_candidates(self):
        result = resolve_random_group((), 5)
        assert result == ()


# ---------------------------------------------------------------------------
# Hold Person: single-target penalty
# ---------------------------------------------------------------------------


def test_hold_person_single_mode_penalty(default_party, goblin_party):
    """Single-target Hold Person should apply -2 penalty (raises effective threshold)."""
    engine = CombatEngine(
        pc_party=default_party,
        monster_party=goblin_party,
        auto_resolve_intents=False,
    )

    cleric_cid, _ = find_pc_with_class(engine, CharacterClassType.CLERIC)
    monster_cid = engine._ctx.living(CombatSide.MONSTER)[0].id
    engine._ctx.current_combatant_id = cleric_cid

    import osrlib.combat.actions as actions_mod
    original_roll = actions_mod.roll_dice

    def mock_roll_dice(expr, *args, **kwargs):
        if expr == "1d20":
            from osrlib.dice_roller import DiceRoll
            return DiceRoll(1, 20, 10, 0, 10, [10])
        return original_roll(expr, *args, **kwargs)

    actions_mod.roll_dice = mock_roll_dice
    try:
        action = CastSpellAction(
            actor_id=cleric_cid,
            spell_id="hold_person",
            slot_level=2,
            target_ids=(monster_cid,),
        )
        result = action.execute(engine._ctx)
    finally:
        actions_mod.roll_dice = original_roll

    save_events = find_events(list(result.events), SavingThrowRolled)
    assert len(save_events) == 1
    # Penalty is -2, so the effective target number should be base + 2
    assert save_events[0].penalty == -2


def test_hold_person_group_mode_random(default_party, goblin_party):
    """Group-mode Hold Person should emit GroupTargetsResolved."""
    engine = CombatEngine(
        pc_party=default_party,
        monster_party=goblin_party,
        auto_resolve_intents=False,
    )

    cleric_cid, _ = find_pc_with_class(engine, CharacterClassType.CLERIC)
    monster_ids = tuple(m.id for m in engine._ctx.living(CombatSide.MONSTER))
    engine._ctx.current_combatant_id = cleric_cid

    import osrlib.combat.actions as actions_mod
    original_roll = actions_mod.roll_dice

    call_count = {"n": 0}

    def mock_roll_dice(expr, *args, **kwargs):
        call_count["n"] += 1
        if expr == "1d4":
            # Force 1d4 = 1 target in group mode
            from osrlib.dice_roller import DiceRoll
            return DiceRoll(1, 4, 1, 0, 1, [1])
        if expr == "1d20":
            # Force save failure
            from osrlib.dice_roller import DiceRoll
            return DiceRoll(1, 20, 1, 0, 1, [1])
        return original_roll(expr, *args, **kwargs)

    actions_mod.roll_dice = mock_roll_dice
    try:
        action = CastSpellAction(
            actor_id=cleric_cid,
            spell_id="hold_person",
            slot_level=2,
            target_ids=monster_ids,  # >1 target = group mode
        )
        result = action.execute(engine._ctx)
    finally:
        actions_mod.roll_dice = original_roll

    group_events = find_events(list(result.events), GroupTargetsResolved)
    assert len(group_events) == 1
    assert group_events[0].pool_roll == 1


def test_hold_person_group_mode_no_penalty(default_party, goblin_party):
    """Group-mode Hold Person should have penalty=0 on saving throws."""
    engine = CombatEngine(
        pc_party=default_party,
        monster_party=goblin_party,
        auto_resolve_intents=False,
    )

    cleric_cid, _ = find_pc_with_class(engine, CharacterClassType.CLERIC)
    monster_ids = tuple(m.id for m in engine._ctx.living(CombatSide.MONSTER))
    engine._ctx.current_combatant_id = cleric_cid

    import osrlib.combat.actions as actions_mod
    original_roll = actions_mod.roll_dice

    def mock_roll_dice(expr, *args, **kwargs):
        if expr == "1d4":
            from osrlib.dice_roller import DiceRoll
            return DiceRoll(1, 4, 2, 0, 2, [2])
        if expr == "1d20":
            from osrlib.dice_roller import DiceRoll
            return DiceRoll(1, 20, 10, 0, 10, [10])
        return original_roll(expr, *args, **kwargs)

    actions_mod.roll_dice = mock_roll_dice
    try:
        action = CastSpellAction(
            actor_id=cleric_cid,
            spell_id="hold_person",
            slot_level=2,
            target_ids=monster_ids,
        )
        result = action.execute(engine._ctx)
    finally:
        actions_mod.roll_dice = original_roll

    save_events = find_events(list(result.events), SavingThrowRolled)
    for se in save_events:
        assert se.penalty == 0


def test_hold_person_hd_cap(default_party):
    """Monsters with 5+ HD should be excluded by Hold Person's max_target_hd=4."""
    stats = MonsterStatsBlock(
        name="Ogre",
        hit_dice="5d8",
        num_appearing="1",
        morale=10,
    )
    party = MonsterParty(stats)

    engine = CombatEngine(
        pc_party=default_party,
        monster_party=party,
        auto_resolve_intents=False,
    )

    cleric_cid, _ = find_pc_with_class(engine, CharacterClassType.CLERIC)
    monster_cid = engine._ctx.living(CombatSide.MONSTER)[0].id
    engine._ctx.current_combatant_id = cleric_cid

    action = CastSpellAction(
        actor_id=cleric_cid,
        spell_id="hold_person",
        slot_level=2,
        target_ids=(monster_cid,),
    )
    result = action.execute(engine._ctx)

    # No condition should be applied — target HD exceeds max
    condition_effects = [e for e in result.effects if isinstance(e, ApplyConditionEffect)]
    assert len(condition_effects) == 0

    # No saving throw rolled either — target was filtered out
    save_events = find_events(list(result.events), SavingThrowRolled)
    assert len(save_events) == 0


def test_engine_dual_mode_choices(default_party, goblin_party):
    """Hold Person should generate N per-enemy + 1 group choice when >1 enemy."""
    engine = CombatEngine(
        pc_party=default_party,
        monster_party=goblin_party,
        auto_resolve_intents=False,
    )

    # Advance engine to the cleric's NeedAction
    cleric_cid, cleric_pc = find_pc_with_class(engine, CharacterClassType.CLERIC)
    # Level up to 4+ so the cleric has level 2 spell slots for Hold Person
    hp_mod = cleric_pc.abilities[AbilityType.CONSTITUTION].modifiers[ModifierType.HP]
    while cleric_pc.level < 4:
        cleric_pc.character_class.xp = cleric_pc.character_class.xp_needed_for_next_level
        cleric_pc.character_class.level_up(hp_mod)
    # Add Hold Person to known spells
    from osrlib.item import Spell
    cleric_pc.inventory.add_item(Spell("Hold Person", 2))

    # Manually set up the turn for the cleric
    engine._ctx.turn_queue.clear()
    engine._ctx.turn_queue.append(cleric_cid)
    engine._state = EncounterState.TURN_START
    engine._ctx.round_number = 1

    result = engine.step()
    need_actions = find_events(list(result.events), NeedAction)
    assert len(need_actions) == 1

    hold_choices = [
        c for c in need_actions[0].available
        if c.ui_key == "cast_spell"
        and c.ui_args.get("spell_id") == "hold_person"
    ]

    num_enemies = len(engine._ctx.living(CombatSide.MONSTER))
    # Should have one choice per enemy (single mode) + 1 group choice
    assert len(hold_choices) == num_enemies + 1

    # The group choice has target_name "enemy group"
    group_choices = [c for c in hold_choices if c.ui_args.get("target_name") == "enemy group"]
    assert len(group_choices) == 1


def test_saving_throw_penalty_backward_compat(default_party, goblin_party):
    """Existing spells that don't set single_save_penalty should emit penalty=0."""
    engine = CombatEngine(
        pc_party=default_party,
        monster_party=goblin_party,
        auto_resolve_intents=False,
    )

    # Use Fireball which has save_type=DRAGON_BREATH but no single_save_penalty
    caster_cid, _ = find_pc_with_class(engine, CharacterClassType.MAGIC_USER)
    monster_cid = engine._ctx.living(CombatSide.MONSTER)[0].id
    engine._ctx.current_combatant_id = caster_cid

    action = CastSpellAction(
        actor_id=caster_cid,
        spell_id="fireball",
        slot_level=3,
        target_ids=(monster_cid,),
    )
    result = action.execute(engine._ctx)

    save_events = find_events(list(result.events), SavingThrowRolled)
    assert len(save_events) >= 1, "Fireball should trigger at least one saving throw"
    for se in save_events:
        assert se.penalty == 0

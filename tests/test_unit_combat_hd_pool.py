"""Tests for Part 1: HD-pool targeting (Sleep)."""

from osrlib.combat import (
    CastSpellAction,
    CombatEngine,
    CombatSide,
)
from osrlib.combat.effects import ApplyConditionEffect
from osrlib.combat.events import GroupTargetsResolved, SavingThrowRolled
from osrlib.combat.spells import get_spell
from osrlib.combat.targeting import TargetMode, get_combatant_hd, resolve_hd_pool
from osrlib.enums import CharacterClassType
from osrlib.monster import Monster, MonsterStatsBlock

from conftest import find_events, find_pc_with_class


# ---------------------------------------------------------------------------
# Pure function tests: resolve_hd_pool
# ---------------------------------------------------------------------------


class TestResolveHdPool:
    def test_basic(self):
        """Pool=4, candidates HD 1/2/3 -> selects 1+2, not 3."""
        candidates = (("a", 1), ("b", 2), ("c", 3))
        result = resolve_hd_pool(candidates, 4)
        assert result == ("a", "b")

    def test_minimum_hd_one(self):
        """HD 0 counts as 1."""
        candidates = (("a", 0), ("b", 1))
        result = resolve_hd_pool(candidates, 2)
        assert result == ("a", "b")

    def test_empty(self):
        result = resolve_hd_pool((), 10)
        assert result == ()

    def test_zero_budget(self):
        candidates = (("a", 1),)
        result = resolve_hd_pool(candidates, 0)
        assert result == ()

    def test_sorts_by_hd(self):
        """Lowest HD are selected first regardless of input order."""
        candidates = (("c", 3), ("a", 1), ("b", 2))
        result = resolve_hd_pool(candidates, 3)
        assert result == ("a", "b")

    def test_exact_budget(self):
        """Pool exactly equals total HD of all candidates."""
        candidates = (("a", 2), ("b", 3))
        result = resolve_hd_pool(candidates, 5)
        assert set(result) == {"a", "b"}

    def test_large_pool(self):
        """Pool larger than total HD selects all candidates."""
        candidates = (("a", 1), ("b", 1), ("c", 1))
        result = resolve_hd_pool(candidates, 100)
        assert set(result) == {"a", "b", "c"}


# ---------------------------------------------------------------------------
# Pure function tests: get_combatant_hd
# ---------------------------------------------------------------------------


class TestGetCombatantHd:
    def test_monster(self):
        stats = MonsterStatsBlock(name="Test", hit_dice="3d8", num_appearing="1")
        monster = Monster(stats)
        assert get_combatant_hd(monster) == 3

    def test_monster_minimum_one(self):
        stats = MonsterStatsBlock(name="Test", hit_dice="1d4", num_appearing="1")
        monster = Monster(stats)
        assert get_combatant_hd(monster) >= 1

    def test_pc(self, default_party):
        pc = default_party.members[0]
        assert get_combatant_hd(pc) >= 1


# ---------------------------------------------------------------------------
# SpellDefinition field tests
# ---------------------------------------------------------------------------


def test_sleep_uses_hd_pool_mode():
    spell = get_spell("sleep")
    assert spell is not None
    assert spell.target_mode == TargetMode.HD_POOL
    assert spell.hd_pool_dice == "2d8"


# ---------------------------------------------------------------------------
# Engine integration: Sleep with HD-pool
# ---------------------------------------------------------------------------


def test_sleep_execute_filters_by_hd_pool(default_party, goblin_party):
    """Mock dice to force pool=2, verify only subset gets ApplyConditionEffect."""
    engine = CombatEngine(
        pc_party=default_party,
        monster_party=goblin_party,
        auto_resolve_intents=False,
    )

    caster_cid, _ = find_pc_with_class(engine, CharacterClassType.MAGIC_USER)
    monster_ids = tuple(m.id for m in engine._ctx.living(CombatSide.MONSTER))
    engine._ctx.current_combatant_id = caster_cid

    import osrlib.combat.actions as actions_mod

    original_roll = actions_mod.roll_dice

    def mock_roll_dice(expr, *args, **kwargs):
        if expr == "2d8":
            # Force pool = 1, so only 1 goblin (1 HD each) is affected
            from osrlib.dice_roller import DiceRoll

            return DiceRoll(2, 8, 1, 0, 1, [1, 0])
        return original_roll(expr, *args, **kwargs)

    actions_mod.roll_dice = mock_roll_dice
    try:
        action = CastSpellAction(
            actor_id=caster_cid,
            spell_id="sleep",
            slot_level=1,
            target_ids=monster_ids,
        )
        result = action.execute(engine._ctx)
    finally:
        actions_mod.roll_dice = original_roll

    # GroupTargetsResolved should be emitted
    group_events = find_events(list(result.events), GroupTargetsResolved)
    assert len(group_events) == 1
    assert group_events[0].pool_roll == 1

    # Only 1 condition effect (pool=1, each goblin is 1 HD)
    condition_effects = [
        e for e in result.effects if isinstance(e, ApplyConditionEffect)
    ]
    assert len(condition_effects) == 1


def test_sleep_lowest_hd_first(default_party):
    """HD 1/2/4, pool=3 -> only 1+2 affected."""
    from osrlib.monster import MonsterParty

    # Create mixed-HD monster party manually
    stats_1hd = MonsterStatsBlock(name="Rat", hit_dice="1d8", num_appearing="1")
    stats_2hd = MonsterStatsBlock(name="Zombie", hit_dice="2d8", num_appearing="1")
    stats_4hd = MonsterStatsBlock(name="Ogre", hit_dice="4d8", num_appearing="1")

    # Build a party manually with all three
    party = MonsterParty(stats_1hd)
    party.members = [Monster(stats_1hd), Monster(stats_2hd), Monster(stats_4hd)]

    engine = CombatEngine(
        pc_party=default_party,
        monster_party=party,
        auto_resolve_intents=False,
    )

    caster_cid, _ = find_pc_with_class(engine, CharacterClassType.MAGIC_USER)
    monster_ids = tuple(m.id for m in engine._ctx.living(CombatSide.MONSTER))
    engine._ctx.current_combatant_id = caster_cid

    import osrlib.combat.actions as actions_mod

    original_roll = actions_mod.roll_dice

    def mock_roll_dice(expr, *args, **kwargs):
        if expr == "2d8":
            from osrlib.dice_roller import DiceRoll

            return DiceRoll(2, 8, 3, 0, 3, [2, 1])
        return original_roll(expr, *args, **kwargs)

    actions_mod.roll_dice = mock_roll_dice
    try:
        action = CastSpellAction(
            actor_id=caster_cid,
            spell_id="sleep",
            slot_level=1,
            target_ids=monster_ids,
        )
        result = action.execute(engine._ctx)
    finally:
        actions_mod.roll_dice = original_roll

    condition_effects = [
        e for e in result.effects if isinstance(e, ApplyConditionEffect)
    ]
    # Pool=3: 1 HD rat + 2 HD zombie = 3, ogre (4 HD) excluded
    assert len(condition_effects) == 2

    group_events = find_events(list(result.events), GroupTargetsResolved)
    assert len(group_events) == 1
    assert len(group_events[0].resolved_target_ids) == 2


def test_sleep_no_saving_throw(default_party, goblin_party):
    """Sleep has no saving throw — no SavingThrowRolled events emitted."""
    engine = CombatEngine(
        pc_party=default_party,
        monster_party=goblin_party,
        auto_resolve_intents=False,
    )

    caster_cid, _ = find_pc_with_class(engine, CharacterClassType.MAGIC_USER)
    monster_ids = tuple(m.id for m in engine._ctx.living(CombatSide.MONSTER))
    engine._ctx.current_combatant_id = caster_cid

    action = CastSpellAction(
        actor_id=caster_cid,
        spell_id="sleep",
        slot_level=1,
        target_ids=monster_ids,
    )
    result = action.execute(engine._ctx)

    save_events = find_events(list(result.events), SavingThrowRolled)
    assert len(save_events) == 0


# ---------------------------------------------------------------------------
# BUG-3 / ISSUE-3 regression tests: Sleep HD cap and undead immunity
# ---------------------------------------------------------------------------


def test_sleep_excludes_high_hd(default_party):
    """Monsters with 5+ HD should be excluded from Sleep (max_target_hd=4)."""
    from osrlib.monster import MonsterParty

    stats_5hd = MonsterStatsBlock(name="Ogre", hit_dice="5d8", num_appearing="1")
    party = MonsterParty(stats_5hd)

    engine = CombatEngine(
        pc_party=default_party,
        monster_party=party,
        auto_resolve_intents=False,
    )

    caster_cid, _ = find_pc_with_class(engine, CharacterClassType.MAGIC_USER)
    monster_ids = tuple(m.id for m in engine._ctx.living(CombatSide.MONSTER))
    engine._ctx.current_combatant_id = caster_cid

    action = CastSpellAction(
        actor_id=caster_cid,
        spell_id="sleep",
        slot_level=1,
        target_ids=monster_ids,
    )
    result = action.execute(engine._ctx)

    # GroupTargetsResolved should show zero resolved targets
    group_events = find_events(list(result.events), GroupTargetsResolved)
    assert len(group_events) == 1
    assert len(group_events[0].resolved_target_ids) == 0

    # No condition effects applied
    condition_effects = [
        e for e in result.effects if isinstance(e, ApplyConditionEffect)
    ]
    assert len(condition_effects) == 0


def test_sleep_excludes_undead(default_party):
    """Undead monsters should be immune to Sleep even if HD <= 4."""
    from osrlib.monster import MonsterParty

    stats_undead = MonsterStatsBlock(
        name="Skeleton", hit_dice="1d8", num_appearing="2", is_undead=True
    )
    party = MonsterParty(stats_undead)

    engine = CombatEngine(
        pc_party=default_party,
        monster_party=party,
        auto_resolve_intents=False,
    )

    caster_cid, _ = find_pc_with_class(engine, CharacterClassType.MAGIC_USER)
    monster_ids = tuple(m.id for m in engine._ctx.living(CombatSide.MONSTER))
    engine._ctx.current_combatant_id = caster_cid

    action = CastSpellAction(
        actor_id=caster_cid,
        spell_id="sleep",
        slot_level=1,
        target_ids=monster_ids,
    )
    result = action.execute(engine._ctx)

    # GroupTargetsResolved should show zero resolved targets (undead filtered)
    group_events = find_events(list(result.events), GroupTargetsResolved)
    assert len(group_events) == 1
    assert len(group_events[0].resolved_target_ids) == 0

    # No condition effects applied
    condition_effects = [
        e for e in result.effects if isinstance(e, ApplyConditionEffect)
    ]
    assert len(condition_effects) == 0

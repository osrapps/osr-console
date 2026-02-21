"""Tests for Phase 1: condition tracker, saving throws, and turn-skipping."""

import pytest

from osrlib.combat import (
    CastSpellAction,
    CastSpellIntent,
    CombatEngine,
    CombatSide,
    ConditionApplied,
    ConditionExpired,
    EncounterState,
    NeedAction,
    TurnSkipped,
)
from osrlib.combat.conditions import ActiveCondition, ConditionTracker, CONDITION_REGISTRY
from osrlib.combat.effects import ApplyConditionEffect, DamageEffect
from osrlib.combat.events import SavingThrowRolled
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
# ConditionTracker unit tests
# ---------------------------------------------------------------------------


class TestConditionTracker:
    def test_add_and_has(self):
        tracker = ConditionTracker()
        cond = ActiveCondition(
            condition_id="held",
            source_id="pc:Alice",
            remaining_rounds=9,
            skip_turn=True,
            break_on_damage=False,
        )
        tracker.add("monster:Goblin:0", cond)
        assert tracker.has("monster:Goblin:0", "held")
        assert not tracker.has("monster:Goblin:0", "asleep")
        assert not tracker.has("monster:Goblin:1", "held")

    def test_remove(self):
        tracker = ConditionTracker()
        cond = ActiveCondition(
            condition_id="held",
            source_id="pc:Alice",
            remaining_rounds=9,
            skip_turn=True,
            break_on_damage=False,
        )
        tracker.add("monster:Goblin:0", cond)
        removed = tracker.remove("monster:Goblin:0", "held")
        assert removed is not None
        assert removed.condition_id == "held"
        assert not tracker.has("monster:Goblin:0", "held")

    def test_remove_nonexistent(self):
        tracker = ConditionTracker()
        assert tracker.remove("monster:Goblin:0", "held") is None

    def test_should_skip_turn(self):
        tracker = ConditionTracker()
        tracker.add(
            "monster:Goblin:0",
            ActiveCondition("held", "pc:Alice", 9, skip_turn=True, break_on_damage=False),
        )
        assert tracker.should_skip_turn("monster:Goblin:0")
        assert not tracker.should_skip_turn("monster:Goblin:1")

    def test_skip_reason(self):
        tracker = ConditionTracker()
        tracker.add(
            "m:0",
            ActiveCondition("asleep", "pc:A", None, skip_turn=True, break_on_damage=True),
        )
        assert tracker.skip_reason("m:0") == "asleep"
        assert tracker.skip_reason("m:1") is None

    def test_tick_round_expires_condition(self):
        tracker = ConditionTracker()
        tracker.add(
            "m:0",
            ActiveCondition("held", "pc:A", remaining_rounds=1, skip_turn=True, break_on_damage=False),
        )
        expired = tracker.tick_round()
        assert ("m:0", "held") in expired
        assert not tracker.has("m:0", "held")

    def test_tick_round_decrements_but_does_not_expire(self):
        tracker = ConditionTracker()
        tracker.add(
            "m:0",
            ActiveCondition("held", "pc:A", remaining_rounds=3, skip_turn=True, break_on_damage=False),
        )
        expired = tracker.tick_round()
        assert len(expired) == 0
        assert tracker.has("m:0", "held")

    def test_permanent_condition_never_expires(self):
        tracker = ConditionTracker()
        tracker.add(
            "m:0",
            ActiveCondition("asleep", "pc:A", remaining_rounds=None, skip_turn=True, break_on_damage=True),
        )
        for _ in range(100):
            expired = tracker.tick_round()
            assert len(expired) == 0
        assert tracker.has("m:0", "asleep")

    def test_remove_break_on_damage(self):
        tracker = ConditionTracker()
        tracker.add(
            "m:0",
            ActiveCondition("asleep", "pc:A", None, skip_turn=True, break_on_damage=True),
        )
        tracker.add(
            "m:0",
            ActiveCondition("held", "pc:A", 9, skip_turn=True, break_on_damage=False),
        )
        removed = tracker.remove_break_on_damage("m:0")
        assert "asleep" in removed
        assert "held" not in removed
        assert not tracker.has("m:0", "asleep")
        assert tracker.has("m:0", "held")

    def test_get_all(self):
        tracker = ConditionTracker()
        tracker.add(
            "m:0",
            ActiveCondition("asleep", "pc:A", None, skip_turn=True, break_on_damage=True),
        )
        tracker.add(
            "m:0",
            ActiveCondition("held", "pc:B", 9, skip_turn=True, break_on_damage=False),
        )
        all_conds = tracker.get_all("m:0")
        assert len(all_conds) == 2
        assert {c.condition_id for c in all_conds} == {"asleep", "held"}

    def test_multiple_conditions_on_same_target(self):
        tracker = ConditionTracker()
        tracker.add(
            "m:0",
            ActiveCondition("asleep", "pc:A", None, skip_turn=True, break_on_damage=True),
        )
        tracker.add(
            "m:0",
            ActiveCondition("blinded", "pc:B", 12, skip_turn=False, break_on_damage=False),
        )
        assert tracker.has("m:0", "asleep")
        assert tracker.has("m:0", "blinded")
        assert tracker.should_skip_turn("m:0")  # asleep causes skip


# ---------------------------------------------------------------------------
# Engine integration: conditions skip turns
# ---------------------------------------------------------------------------


def test_held_creature_skips_turn(default_party, goblin_party):
    engine = CombatEngine(
        pc_party=default_party,
        monster_party=goblin_party,
        auto_resolve_intents=True,
    )

    # Find a monster and apply "held" condition
    monster_cid = None
    for cid, ref in engine._ctx.combatants.items():
        if ref.side == CombatSide.MONSTER and ref.is_alive:
            monster_cid = cid
            break
    assert monster_cid is not None

    engine._ctx.conditions.add(
        monster_cid,
        ActiveCondition("held", "pc:Test", remaining_rounds=9, skip_turn=True, break_on_damage=False),
    )

    # Force the monster's turn
    engine._ctx.turn_queue.clear()
    engine._ctx.turn_queue.append(monster_cid)
    engine._state = EncounterState.TURN_START
    engine._ctx.round_number = 1

    result = engine.step()
    skipped = _find_events(list(result.events), TurnSkipped)
    assert len(skipped) == 1
    assert skipped[0].combatant_id == monster_cid
    assert skipped[0].reason == "held"


def test_asleep_creature_skips_turn(default_party, goblin_party):
    engine = CombatEngine(
        pc_party=default_party,
        monster_party=goblin_party,
        auto_resolve_intents=True,
    )

    monster_cid = None
    for cid, ref in engine._ctx.combatants.items():
        if ref.side == CombatSide.MONSTER and ref.is_alive:
            monster_cid = cid
            break
    assert monster_cid is not None

    engine._ctx.conditions.add(
        monster_cid,
        ActiveCondition("asleep", "pc:Test", remaining_rounds=None, skip_turn=True, break_on_damage=True),
    )

    engine._ctx.turn_queue.clear()
    engine._ctx.turn_queue.append(monster_cid)
    engine._state = EncounterState.TURN_START
    engine._ctx.round_number = 1

    result = engine.step()
    skipped = _find_events(list(result.events), TurnSkipped)
    assert len(skipped) == 1
    assert skipped[0].reason == "asleep"


def test_asleep_creature_wakes_on_damage(default_party, goblin_party):
    engine = CombatEngine(
        pc_party=default_party,
        monster_party=goblin_party,
        auto_resolve_intents=True,
    )

    monster_cid = None
    for cid, ref in engine._ctx.combatants.items():
        if ref.side == CombatSide.MONSTER and ref.is_alive:
            monster_cid = cid
            break
    assert monster_cid is not None

    # Apply asleep condition
    engine._ctx.conditions.add(
        monster_cid,
        ActiveCondition("asleep", "pc:Test", remaining_rounds=None, skip_turn=True, break_on_damage=True),
    )
    assert engine._ctx.conditions.has(monster_cid, "asleep")

    # Simulate damage via the effect pipeline
    pc_cid = None
    for cid, ref in engine._ctx.combatants.items():
        if ref.side == CombatSide.PC:
            pc_cid = cid
            break

    engine._pending_effects = (
        DamageEffect(source_id=pc_cid, target_id=monster_cid, amount=1),
    )
    events = []
    engine._handle_apply_effects(events)

    # Asleep should be removed
    assert not engine._ctx.conditions.has(monster_cid, "asleep")
    expired_events = _find_events(events, ConditionExpired)
    assert len(expired_events) == 1
    assert expired_events[0].condition_id == "asleep"
    assert expired_events[0].reason == "damage"


def test_condition_expires_after_duration(default_party, goblin_party):
    engine = CombatEngine(
        pc_party=default_party,
        monster_party=goblin_party,
        auto_resolve_intents=True,
    )

    monster_cid = None
    for cid, ref in engine._ctx.combatants.items():
        if ref.side == CombatSide.MONSTER and ref.is_alive:
            monster_cid = cid
            break
    assert monster_cid is not None

    # Apply held with 2 rounds remaining
    engine._ctx.conditions.add(
        monster_cid,
        ActiveCondition("held", "pc:Test", remaining_rounds=2, skip_turn=True, break_on_damage=False),
    )

    # Simulate 2 round starts
    engine._ctx.round_number = 0
    engine._state = EncounterState.ROUND_START

    # Round 1: tick, should not expire
    events_r1 = []
    engine._handle_round_start(events_r1)
    assert engine._ctx.conditions.has(monster_cid, "held")
    assert len(_find_events(events_r1, ConditionExpired)) == 0

    # Round 2: tick, should expire
    engine._state = EncounterState.ROUND_START
    events_r2 = []
    engine._handle_round_start(events_r2)
    assert not engine._ctx.conditions.has(monster_cid, "held")
    expired = _find_events(events_r2, ConditionExpired)
    assert len(expired) == 1
    assert expired[0].condition_id == "held"
    assert expired[0].reason == "duration"


# ---------------------------------------------------------------------------
# Engine integration: ApplyConditionEffect stores in tracker
# ---------------------------------------------------------------------------


def test_apply_condition_effect_stores_in_tracker(default_party, goblin_party):
    engine = CombatEngine(
        pc_party=default_party,
        monster_party=goblin_party,
        auto_resolve_intents=True,
    )

    monster_cid = None
    pc_cid = None
    for cid, ref in engine._ctx.combatants.items():
        if ref.side == CombatSide.MONSTER and ref.is_alive and monster_cid is None:
            monster_cid = cid
        if ref.side == CombatSide.PC and pc_cid is None:
            pc_cid = cid

    engine._pending_effects = (
        ApplyConditionEffect(
            source_id=pc_cid,
            target_id=monster_cid,
            condition_id="held",
            duration=9,
        ),
    )
    events = []
    engine._handle_apply_effects(events)

    assert engine._ctx.conditions.has(monster_cid, "held")
    cond = engine._ctx.conditions.get_all(monster_cid)[0]
    assert cond.skip_turn is True
    assert cond.remaining_rounds == 9


# ---------------------------------------------------------------------------
# Saving throws
# ---------------------------------------------------------------------------


def test_saving_throw_negates_hold_person(default_party, goblin_party):
    """Force a high save roll so Hold Person is negated."""
    engine = CombatEngine(
        pc_party=default_party,
        monster_party=goblin_party,
        auto_resolve_intents=False,
    )

    cleric_cid, cleric_pc = _find_pc_with_class(engine, CharacterClassType.CLERIC)
    monster_cid = engine._ctx.living(CombatSide.MONSTER)[0].id
    engine._ctx.current_combatant_id = cleric_cid

    action = CastSpellAction(
        actor_id=cleric_cid,
        spell_id="hold_person",
        slot_level=2,
        target_ids=(monster_cid,),
    )

    # Monkey-patch roll_dice so the save roll always succeeds (20)
    import osrlib.combat.actions as actions_mod
    original_roll = actions_mod.roll_dice

    call_count = [0]

    def mock_roll_dice(expr, *args, **kwargs):
        call_count[0] += 1
        result = original_roll(expr, *args, **kwargs)
        # The save roll is the "1d20" call
        if expr == "1d20":
            # Return a roll that always succeeds (20)
            from osrlib.dice_roller import DiceRoll
            return DiceRoll(1, 20, 20, 0, 20, [20])
        return result

    actions_mod.roll_dice = mock_roll_dice
    try:
        result = action.execute(engine._ctx)
    finally:
        actions_mod.roll_dice = original_roll

    # Should have SavingThrowRolled with success=True
    save_events = _find_events(list(result.events), SavingThrowRolled)
    assert len(save_events) == 1
    assert save_events[0].success is True

    # Should NOT have ApplyConditionEffect (save negates)
    condition_effects = [
        e for e in result.effects if isinstance(e, ApplyConditionEffect)
    ]
    assert len(condition_effects) == 0


def test_saving_throw_fails_hold_person(default_party, goblin_party):
    """Force a low save roll so Hold Person applies."""
    engine = CombatEngine(
        pc_party=default_party,
        monster_party=goblin_party,
        auto_resolve_intents=False,
    )

    cleric_cid, cleric_pc = _find_pc_with_class(engine, CharacterClassType.CLERIC)
    monster_cid = engine._ctx.living(CombatSide.MONSTER)[0].id
    engine._ctx.current_combatant_id = cleric_cid

    action = CastSpellAction(
        actor_id=cleric_cid,
        spell_id="hold_person",
        slot_level=2,
        target_ids=(monster_cid,),
    )

    # Monkey-patch roll_dice so the save roll always fails (1)
    import osrlib.combat.actions as actions_mod
    original_roll = actions_mod.roll_dice

    def mock_roll_dice(expr, *args, **kwargs):
        result = original_roll(expr, *args, **kwargs)
        if expr == "1d20":
            from osrlib.dice_roller import DiceRoll
            return DiceRoll(1, 20, 1, 0, 1, [1])
        return result

    actions_mod.roll_dice = mock_roll_dice
    try:
        result = action.execute(engine._ctx)
    finally:
        actions_mod.roll_dice = original_roll

    # Should have SavingThrowRolled with success=False
    save_events = _find_events(list(result.events), SavingThrowRolled)
    assert len(save_events) == 1
    assert save_events[0].success is False

    # Should have ApplyConditionEffect (save failed)
    condition_effects = [
        e for e in result.effects if isinstance(e, ApplyConditionEffect)
    ]
    assert len(condition_effects) == 1
    assert condition_effects[0].condition_id == "held"


def test_magic_missile_no_save(default_party, goblin_party):
    """Magic Missile has no saving throw — no SavingThrowRolled event emitted."""
    engine = CombatEngine(
        pc_party=default_party,
        monster_party=goblin_party,
        auto_resolve_intents=False,
    )

    caster_cid = None
    for cid, ref in engine._ctx.combatants.items():
        if ref.side == CombatSide.PC and isinstance(ref.entity, PlayerCharacter):
            ct = ref.entity.character_class.class_type
            if ct in (CharacterClassType.MAGIC_USER, CharacterClassType.ELF):
                caster_cid = cid
                break
    if caster_cid is None:
        pytest.skip("No caster in party")

    monster_cid = engine._ctx.living(CombatSide.MONSTER)[0].id
    engine._ctx.current_combatant_id = caster_cid

    action = CastSpellAction(
        actor_id=caster_cid,
        spell_id="magic_missile",
        slot_level=1,
        target_ids=(monster_cid,),
    )
    result = action.execute(engine._ctx)

    save_events = _find_events(list(result.events), SavingThrowRolled)
    assert len(save_events) == 0

    # Should still have damage effect
    damage_effects = [e for e in result.effects if isinstance(e, DamageEffect)]
    assert len(damage_effects) == 1


def test_sleep_no_save(default_party, goblin_party):
    """Sleep has no saving throw — no SavingThrowRolled event emitted."""
    engine = CombatEngine(
        pc_party=default_party,
        monster_party=goblin_party,
        auto_resolve_intents=False,
    )

    caster_cid = None
    for cid, ref in engine._ctx.combatants.items():
        if ref.side == CombatSide.PC and isinstance(ref.entity, PlayerCharacter):
            ct = ref.entity.character_class.class_type
            if ct in (CharacterClassType.MAGIC_USER, CharacterClassType.ELF):
                caster_cid = cid
                break
    if caster_cid is None:
        pytest.skip("No caster in party")

    monster_ids = tuple(
        m.id for m in engine._ctx.living(CombatSide.MONSTER)
    )
    engine._ctx.current_combatant_id = caster_cid

    action = CastSpellAction(
        actor_id=caster_cid,
        spell_id="sleep",
        slot_level=1,
        target_ids=monster_ids,
    )
    result = action.execute(engine._ctx)

    save_events = _find_events(list(result.events), SavingThrowRolled)
    assert len(save_events) == 0

    # Should have condition effects for all targets
    condition_effects = [
        e for e in result.effects if isinstance(e, ApplyConditionEffect)
    ]
    assert len(condition_effects) == len(monster_ids)


# ---------------------------------------------------------------------------
# View includes conditions
# ---------------------------------------------------------------------------


def test_view_includes_conditions(default_party, goblin_party):
    engine = CombatEngine(
        pc_party=default_party,
        monster_party=goblin_party,
        auto_resolve_intents=True,
    )

    monster_cid = None
    for cid, ref in engine._ctx.combatants.items():
        if ref.side == CombatSide.MONSTER and ref.is_alive:
            monster_cid = cid
            break

    engine._ctx.conditions.add(
        monster_cid,
        ActiveCondition("held", "pc:Test", 9, skip_turn=True, break_on_damage=False),
    )

    view = engine.get_view()
    monster_view = next(cv for cv in view.combatants if cv.id == monster_cid)
    assert "held" in monster_view.conditions

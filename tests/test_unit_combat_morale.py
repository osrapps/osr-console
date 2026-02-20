"""Tests for Phase 5: B/X morale checks and monster flee."""

import pytest

from osrlib.combat import (
    CombatEngine,
    CombatSide,
    EncounterOutcome,
    EncounterState,
    EntityFled,
    EventFormatter,
    FixedDiceService,
    FleeIntent,
    ForcedIntentApplied,
    ForcedIntentQueued,
    MoraleChecked,
    TurnSkipped,
    VictoryDetermined,
)
from osrlib.combat.context import CombatContext
from osrlib.encounter import Encounter
from osrlib.monster import MonsterParty, MonsterStatsBlock
from osrlib.party import Party
from osrlib.player_character import Alignment
from osrlib.treasure import TreasureType
from osrlib.enums import CharacterClassType


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def default_party():
    return Party.get_default_party()


def _make_monster_stats(
    morale: int = 7, num_appearing: str = "3", name: str = "Goblin"
):
    return MonsterStatsBlock(
        name=name,
        description="Test monster.",
        armor_class=9,
        hit_dice="1",
        num_appearing=num_appearing,
        movement=60,
        num_special_abilities=0,
        attacks_per_round=1,
        damage_per_attack="1d4",
        save_as_class=CharacterClassType.FIGHTER,
        save_as_level=1,
        morale=morale,
        treasure_type=TreasureType.NONE,
        alignment=Alignment.CHAOTIC,
    )


@pytest.fixture
def low_morale_stats():
    return _make_monster_stats(morale=6, num_appearing="3")


@pytest.fixture
def low_morale_party(low_morale_stats):
    return MonsterParty(low_morale_stats)


@pytest.fixture
def morale_12_stats():
    return _make_monster_stats(morale=12, num_appearing="2")


@pytest.fixture
def morale_12_party(morale_12_stats):
    return MonsterParty(morale_12_stats)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _events_of_type(events, event_type):
    return [e for e in events if isinstance(e, event_type)]


def _advance_past_init(engine):
    """Step the engine past INIT (consuming surprise rolls) to ROUND_START."""
    events = []
    for _ in range(5):
        result = engine.step()
        events.extend(result.events)
        if engine.state == EncounterState.ROUND_START:
            return events
    raise RuntimeError("Failed to reach ROUND_START")


def _kill_monster_by_index(ctx, idx=0):
    """Kill the nth monster in the context by zeroing HP."""
    monster_refs = [
        (cid, ref)
        for cid, ref in ctx.combatants.items()
        if ref.side == CombatSide.MONSTER
    ]
    cid, ref = monster_refs[idx]
    ref.entity.hit_points = 0
    # Mark death as announced so CHECK_DEATHS doesn't interfere
    ctx.announced_deaths.add(cid)
    return cid


def _run_to_end(engine, max_steps=500):
    """Run engine to completion, collecting all events."""
    all_events = []
    for _ in range(max_steps):
        result = engine.step()
        all_events.extend(result.events)
        if engine.state == EncounterState.ENDED:
            return all_events
    raise RuntimeError("Engine did not reach ENDED")


def _step_to_check_morale(engine):
    """Step engine until it reaches CHECK_MORALE, collecting events."""
    events = []
    for _ in range(200):
        result = engine.step()
        events.extend(result.events)
        if engine.state == EncounterState.CHECK_MORALE:
            return events
    raise RuntimeError("Failed to reach CHECK_MORALE")


# ---------------------------------------------------------------------------
# Test 1: First death + 2d6 > morale → MoraleChecked(passed=False), FleeIntents queued
# ---------------------------------------------------------------------------


class TestMoraleCheckFirstDeathFail:
    def test_morale_check_first_death_fail(self, default_party, low_morale_party):
        # Dice: surprise (2 calls), then morale roll = 12 (> 6 → fail)
        dice = FixedDiceService([1, 1, 12])
        engine = CombatEngine(
            pc_party=default_party,
            monster_party=low_morale_party,
            dice=dice,
        )
        _advance_past_init(engine)

        # Kill one monster manually
        _kill_monster_by_index(engine._ctx, 0)

        # Force engine into CHECK_MORALE state and step
        engine._state = EncounterState.CHECK_MORALE
        result = engine.step()

        morale_events = _events_of_type(result.events, MoraleChecked)
        assert len(morale_events) == 1
        mc = morale_events[0]
        assert mc.passed is False
        assert mc.trigger == "first_death"
        assert mc.monster_morale == 6
        assert mc.roll == 12

        # ForcedIntentQueued events are deferred — they appear on the NEXT step
        result2 = engine.step()
        flee_queued = _events_of_type(result2.events, ForcedIntentQueued)
        assert len(flee_queued) >= 1
        assert all("morale" in fq.reason for fq in flee_queued)


# ---------------------------------------------------------------------------
# Test 2: First death + 2d6 ≤ morale → pass, no flee
# ---------------------------------------------------------------------------


class TestMoraleCheckFirstDeathPass:
    def test_morale_check_first_death_pass(self, default_party):
        stats = _make_monster_stats(morale=10, num_appearing="3")
        monsters = MonsterParty(stats)
        # Dice: surprise (2), morale roll = 5 (≤ 10 → pass)
        dice = FixedDiceService([1, 1, 5])
        engine = CombatEngine(
            pc_party=default_party,
            monster_party=monsters,
            dice=dice,
        )
        _advance_past_init(engine)

        _kill_monster_by_index(engine._ctx, 0)
        engine._state = EncounterState.CHECK_MORALE
        events = []
        result = engine.step()
        events.extend(result.events)

        morale_events = _events_of_type(events, MoraleChecked)
        assert len(morale_events) == 1
        assert morale_events[0].passed is True

        flee_queued = [
            e
            for e in events
            if isinstance(e, ForcedIntentQueued) and "morale" in e.reason
        ]
        assert len(flee_queued) == 0


# ---------------------------------------------------------------------------
# Test 3: Half incapacitated → morale fail → flee
# ---------------------------------------------------------------------------


class TestMoraleCheckHalfDeadFail:
    def test_morale_check_half_dead_fail(self, default_party):
        stats = _make_monster_stats(morale=8, num_appearing="4")
        monsters = MonsterParty(stats)
        # Dice: surprise (2), first-death morale pass (4 ≤ 8), half-dead morale fail (12 > 8)
        dice = FixedDiceService([1, 1, 4, 12])
        engine = CombatEngine(
            pc_party=default_party,
            monster_party=monsters,
            dice=dice,
        )
        _advance_past_init(engine)

        # Kill monster #1 → triggers first_death
        _kill_monster_by_index(engine._ctx, 0)
        engine._state = EncounterState.CHECK_MORALE
        result = engine.step()  # processes first_death, passes
        assert _events_of_type(result.events, MoraleChecked)[0].passed is True

        # Kill monster #2 → now 2/4 incapacitated → half_incapacitated trigger
        _kill_monster_by_index(engine._ctx, 1)
        engine._state = EncounterState.CHECK_MORALE
        events = []
        result = engine.step()
        events.extend(result.events)

        half_checks = [
            m
            for m in _events_of_type(events, MoraleChecked)
            if m.trigger == "half_incapacitated"
        ]
        assert len(half_checks) == 1
        assert half_checks[0].passed is False


# ---------------------------------------------------------------------------
# Test 4: Half incapacitated → morale pass
# ---------------------------------------------------------------------------


class TestMoraleCheckHalfDeadPass:
    def test_morale_check_half_dead_pass(self, default_party):
        stats = _make_monster_stats(morale=10, num_appearing="4")
        monsters = MonsterParty(stats)
        # Dice: surprise (2), first-death pass (3 ≤ 10), half-dead pass (5 ≤ 10)
        dice = FixedDiceService([1, 1, 3, 5])
        engine = CombatEngine(
            pc_party=default_party,
            monster_party=monsters,
            dice=dice,
        )
        _advance_past_init(engine)

        _kill_monster_by_index(engine._ctx, 0)
        engine._state = EncounterState.CHECK_MORALE
        engine.step()  # first_death pass

        _kill_monster_by_index(engine._ctx, 1)
        engine._state = EncounterState.CHECK_MORALE
        events = []
        result = engine.step()
        events.extend(result.events)

        half_checks = [
            m
            for m in _events_of_type(events, MoraleChecked)
            if m.trigger == "half_incapacitated"
        ]
        assert len(half_checks) == 1
        assert half_checks[0].passed is True


# ---------------------------------------------------------------------------
# Test 5: Two passes → is_immune=True, no further checks
# ---------------------------------------------------------------------------


class TestTwoPassImmunity:
    def test_two_pass_immunity(self, default_party):
        stats = _make_monster_stats(morale=10, num_appearing="4")
        monsters = MonsterParty(stats)
        # Dice: surprise (2), first-death pass (2 ≤ 10), half-dead pass (2 ≤ 10)
        dice = FixedDiceService([1, 1, 2, 2])
        engine = CombatEngine(
            pc_party=default_party,
            monster_party=monsters,
            dice=dice,
        )
        _advance_past_init(engine)

        _kill_monster_by_index(engine._ctx, 0)
        engine._state = EncounterState.CHECK_MORALE
        result = engine.step()  # pass #1
        mc1 = _events_of_type(result.events, MoraleChecked)[0]
        assert mc1.checks_passed_total == 1
        assert mc1.now_immune is False

        _kill_monster_by_index(engine._ctx, 1)
        engine._state = EncounterState.CHECK_MORALE
        result = engine.step()  # pass #2 → immune
        mc2 = _events_of_type(result.events, MoraleChecked)[0]
        assert mc2.checks_passed_total == 2
        assert mc2.now_immune is True
        assert engine._ctx.morale.is_immune is True


# ---------------------------------------------------------------------------
# Test 6: Morale 12 → never checks
# ---------------------------------------------------------------------------


class TestMorale12NeverChecks:
    def test_morale_12_never_checks(self, default_party, morale_12_party):
        dice = FixedDiceService([1, 1])
        engine = CombatEngine(
            pc_party=default_party,
            monster_party=morale_12_party,
            dice=dice,
        )
        assert engine._ctx.morale.is_immune is True

        _advance_past_init(engine)

        # Kill a monster
        _kill_monster_by_index(engine._ctx, 0)
        engine._state = EncounterState.CHECK_MORALE
        result = engine.step()

        morale_events = _events_of_type(result.events, MoraleChecked)
        assert len(morale_events) == 0


# ---------------------------------------------------------------------------
# Test 7: Fled monster gets TurnSkipped(reason="fled")
# ---------------------------------------------------------------------------


class TestFledMonsterSkipsTurn:
    def test_fled_monster_skips_turn(self, default_party):
        # Use tough monsters so PCs don't kill them in round 1
        stats = _make_monster_stats(morale=6, num_appearing="3")
        monsters = MonsterParty(stats)
        # Give monsters lots of HP so they survive
        for m in monsters.members:
            m.hit_points = 100
            m.max_hit_points = 100

        dice = FixedDiceService([1, 1])
        engine = CombatEngine(
            pc_party=default_party,
            monster_party=monsters,
            dice=dice,
        )
        _advance_past_init(engine)

        # Build the turn queue (monster is still active)
        engine.step()

        # Mark first monster as fled AFTER it's in the queue
        monster_ids = [
            cid
            for cid, ref in engine._ctx.combatants.items()
            if ref.side == CombatSide.MONSTER
        ]
        engine._ctx.combatants[monster_ids[0]].has_fled = True

        # Run through the round — fled monster should get TurnSkipped
        events = []
        for _ in range(200):
            result = engine.step()
            events.extend(result.events)
            # Stop after first round completes
            if engine._ctx.round_number >= 2:
                break
            if engine.state == EncounterState.ENDED:
                break

        skip_events = _events_of_type(events, TurnSkipped)
        fled_skips = [s for s in skip_events if s.reason == "fled"]
        assert len(fled_skips) >= 1
        assert fled_skips[0].combatant_id == monster_ids[0]


# ---------------------------------------------------------------------------
# Test 8: living(MONSTER) excludes fled
# ---------------------------------------------------------------------------


class TestFledExcludedFromTargeting:
    def test_fled_monster_excluded_from_targeting(
        self, default_party, low_morale_party
    ):
        ctx = CombatContext.build(default_party, low_morale_party)
        monster_ids = [
            cid for cid, ref in ctx.combatants.items() if ref.side == CombatSide.MONSTER
        ]
        initial_living = len(ctx.living(CombatSide.MONSTER))

        ctx.combatants[monster_ids[0]].has_fled = True
        assert len(ctx.living(CombatSide.MONSTER)) == initial_living - 1


# ---------------------------------------------------------------------------
# Test 9: All monsters fled → PARTY_VICTORY
# ---------------------------------------------------------------------------


class TestAllMonstersFledIsPartyVictory:
    def test_all_monsters_fled_is_party_victory(self, default_party, low_morale_party):
        dice = FixedDiceService([1, 1])
        engine = CombatEngine(
            pc_party=default_party,
            monster_party=low_morale_party,
            dice=dice,
        )
        _advance_past_init(engine)

        # Mark all monsters as fled
        for cid, ref in engine._ctx.combatants.items():
            if ref.side == CombatSide.MONSTER:
                ref.has_fled = True

        events = _run_to_end(engine)
        victory_events = _events_of_type(events, VictoryDetermined)
        assert len(victory_events) == 1
        assert victory_events[0].outcome == EncounterOutcome.PARTY_VICTORY
        assert engine.outcome == EncounterOutcome.PARTY_VICTORY


# ---------------------------------------------------------------------------
# Test 10: Fled monsters not in initiative/turn queue
# ---------------------------------------------------------------------------


class TestFledExcludedFromInitiative:
    def test_fled_excluded_from_initiative(self, default_party, low_morale_party):
        dice = FixedDiceService([1, 1])
        engine = CombatEngine(
            pc_party=default_party,
            monster_party=low_morale_party,
            dice=dice,
        )
        _advance_past_init(engine)

        # Mark all monsters as fled
        monster_ids = []
        for cid, ref in engine._ctx.combatants.items():
            if ref.side == CombatSide.MONSTER:
                ref.has_fled = True
                monster_ids.append(cid)

        # Step ROUND_START to build initiative
        engine._state = EncounterState.ROUND_START
        engine.step()

        for mid in monster_ids:
            assert mid not in engine._ctx.turn_queue


# ---------------------------------------------------------------------------
# Test 11: FleeIntent → FleeAction → FleeEffect → EntityFled, has_fled=True
# ---------------------------------------------------------------------------


class TestFleeIntentFullPipeline:
    def test_flee_intent_full_pipeline(self, default_party, low_morale_party):
        dice = FixedDiceService([1, 1])
        engine = CombatEngine(
            pc_party=default_party,
            monster_party=low_morale_party,
            dice=dice,
        )
        # Give monsters high HP so PCs can't kill them before their turn
        for cid, ref in engine._ctx.combatants.items():
            if ref.side == CombatSide.MONSTER:
                ref.entity.hit_points = 100
                ref.entity.max_hit_points = 100
        _advance_past_init(engine)

        # Step through ROUND_START to build turn queue
        engine.step()

        # Find a monster in the turn queue and queue a flee intent for it
        monster_id = None
        for cid in list(engine._ctx.turn_queue):
            if engine._ctx.combatants[cid].side == CombatSide.MONSTER:
                monster_id = cid
                break

        if monster_id is None:
            pytest.skip("No monster in turn queue")

        flee_intent = FleeIntent(actor_id=monster_id)
        engine.queue_forced_intent(monster_id, flee_intent, "morale failure")

        # Step through turns until the monster's FleeIntent is processed
        all_events = []
        for _ in range(200):
            result = engine.step()
            all_events.extend(result.events)
            # Stop once we see the EntityFled event for our monster
            if any(
                isinstance(e, EntityFled) and e.entity_id == monster_id
                for e in result.events
            ):
                break
            if engine.state == EncounterState.ENDED:
                break

        # Verify the full pipeline: ForcedIntentApplied → EntityFled
        forced_applied = _events_of_type(all_events, ForcedIntentApplied)
        assert any(fa.combatant_id == monster_id for fa in forced_applied)

        fled_events = _events_of_type(all_events, EntityFled)
        assert any(e.entity_id == monster_id for e in fled_events)

        assert engine._ctx.combatants[monster_id].has_fled is True


# ---------------------------------------------------------------------------
# Test 12: No deaths → pass-through, no morale roll
# ---------------------------------------------------------------------------


class TestMoraleNoCheckWithoutTrigger:
    def test_morale_no_check_without_trigger(self, default_party, low_morale_party):
        dice = FixedDiceService([1, 1])
        engine = CombatEngine(
            pc_party=default_party,
            monster_party=low_morale_party,
            dice=dice,
        )
        _advance_past_init(engine)

        # No monsters killed — go directly to CHECK_MORALE
        engine._state = EncounterState.CHECK_MORALE
        result = engine.step()

        morale_events = _events_of_type(result.events, MoraleChecked)
        assert len(morale_events) == 0
        # Should pass through to CHECK_VICTORY
        assert engine.state == EncounterState.CHECK_VICTORY


# ---------------------------------------------------------------------------
# Test 13: First death trigger fires only once
# ---------------------------------------------------------------------------


class TestFirstDeathTriggerOnlyFiresOnce:
    def test_first_death_trigger_only_fires_once(self, default_party):
        stats = _make_monster_stats(morale=10, num_appearing="4")
        monsters = MonsterParty(stats)
        # Dice: surprise (2), first-death pass, then subsequent won't trigger first_death
        dice = FixedDiceService([1, 1, 3])
        engine = CombatEngine(
            pc_party=default_party,
            monster_party=monsters,
            dice=dice,
        )
        _advance_past_init(engine)

        # Kill first monster → first_death trigger
        _kill_monster_by_index(engine._ctx, 0)
        engine._state = EncounterState.CHECK_MORALE
        result = engine.step()
        morale = _events_of_type(result.events, MoraleChecked)
        assert len(morale) == 1
        assert morale[0].trigger == "first_death"

        # Kill second monster → should NOT trigger first_death again
        # (only half_incapacitated if applicable, which requires 2/4)
        _kill_monster_by_index(engine._ctx, 1)
        engine._state = EncounterState.CHECK_MORALE
        result = engine.step()
        morale = _events_of_type(result.events, MoraleChecked)

        # 2/4 dead = half incapacitated, so this triggers half_incapacitated
        assert len(morale) == 1
        assert morale[0].trigger == "half_incapacitated"


# ---------------------------------------------------------------------------
# Test 14: Half dead trigger fires only once
# ---------------------------------------------------------------------------


class TestHalfDeadTriggerOnlyFiresOnce:
    def test_half_dead_trigger_only_fires_once(self, default_party):
        stats = _make_monster_stats(morale=10, num_appearing="4")
        monsters = MonsterParty(stats)
        # Dice: surprise (2), first-death pass, half-dead pass, no more rolls needed
        dice = FixedDiceService([1, 1, 3, 3])
        engine = CombatEngine(
            pc_party=default_party,
            monster_party=monsters,
            dice=dice,
        )
        _advance_past_init(engine)

        # Kill #1 → first_death
        _kill_monster_by_index(engine._ctx, 0)
        engine._state = EncounterState.CHECK_MORALE
        engine.step()

        # Kill #2 → half_incapacitated (2/4)
        _kill_monster_by_index(engine._ctx, 1)
        engine._state = EncounterState.CHECK_MORALE
        engine.step()

        # Kill #3 → should NOT trigger half again (already checked)
        _kill_monster_by_index(engine._ctx, 2)
        engine._state = EncounterState.CHECK_MORALE
        result = engine.step()
        morale = _events_of_type(result.events, MoraleChecked)
        assert len(morale) == 0


# ---------------------------------------------------------------------------
# Test 15: Formatter output for MoraleChecked and EntityFled
# ---------------------------------------------------------------------------


class TestFormatterMoraleAndFled:
    def test_formatter_morale_checked(self):
        fmt = EventFormatter()
        event = MoraleChecked(
            monster_morale=7,
            roll=9,
            modifier=0,
            passed=False,
            trigger="first_death",
            checks_passed_total=0,
            now_immune=False,
        )
        text = fmt.format(event)
        assert "Morale check" in text
        assert "first death" in text
        assert "9" in text
        assert "7" in text
        assert "failed" in text

    def test_formatter_morale_passed(self):
        fmt = EventFormatter()
        event = MoraleChecked(
            monster_morale=10,
            roll=5,
            modifier=0,
            passed=True,
            trigger="half_incapacitated",
            checks_passed_total=1,
            now_immune=False,
        )
        text = fmt.format(event)
        assert "passed" in text
        assert "half incapacitated" in text

    def test_formatter_entity_fled(self):
        fmt = EventFormatter()
        event = EntityFled(entity_id="monster:Goblin:0")
        text = fmt.format(event)
        assert "Goblin #1" in text
        assert "flees" in text


# ---------------------------------------------------------------------------
# Test 16: CombatantView reflects fled status
# ---------------------------------------------------------------------------


class TestViewIncludesHasFled:
    def test_view_includes_has_fled(self, default_party, low_morale_party):
        dice = FixedDiceService([1, 1])
        engine = CombatEngine(
            pc_party=default_party,
            monster_party=low_morale_party,
            dice=dice,
        )
        _advance_past_init(engine)

        monster_ids = [
            cid
            for cid, ref in engine._ctx.combatants.items()
            if ref.side == CombatSide.MONSTER
        ]
        engine._ctx.combatants[monster_ids[0]].has_fled = True

        view = engine.get_view()
        fled_views = [c for c in view.combatants if c.has_fled]
        assert len(fled_views) == 1
        assert fled_views[0].id == monster_ids[0]


# ---------------------------------------------------------------------------
# Test 17: Encounter.end_encounter() awards XP when engine outcome = PARTY_VICTORY
#          but monsters are still alive (routed)
# ---------------------------------------------------------------------------


class TestEncounterXPAwardedOnRout:
    def test_encounter_xp_awarded_on_rout(self, default_party, low_morale_party):
        encounter = Encounter(
            name="Morale test",
            description="Test encounter",
            monster_party=low_morale_party,
        )
        encounter.pc_party = default_party

        # Simulate: engine completed with PARTY_VICTORY but monsters still alive (fled)
        engine = CombatEngine(
            pc_party=default_party,
            monster_party=low_morale_party,
            dice=FixedDiceService([1, 1]),
        )
        engine._outcome = EncounterOutcome.PARTY_VICTORY
        engine._state = EncounterState.ENDED
        encounter.engine = engine

        initial_xp = sum(pc.xp for pc in default_party.members)
        encounter.end_encounter()

        final_xp = sum(pc.xp for pc in default_party.members)
        assert final_xp > initial_xp


# ---------------------------------------------------------------------------
# Test 18: End-to-end: low-morale monsters, morale fail → EntityFled events
# ---------------------------------------------------------------------------


class TestFullEncounterMoraleFailure:
    def test_full_encounter_morale_failure(self, default_party):
        # Morale 2 — any 2d6 roll > 2 fails. Use tough monsters so PCs can't kill them.
        stats = _make_monster_stats(morale=2, num_appearing="3")
        monsters = MonsterParty(stats)
        for m in monsters.members:
            m.hit_points = 100
            m.max_hit_points = 100

        # Dice: surprise (1,1), morale check roll = 7 (> 2 → fail)
        dice = FixedDiceService([1, 1, 7])
        engine = CombatEngine(
            pc_party=default_party,
            monster_party=monsters,
            dice=dice,
        )

        # Run through INIT and build turn queue
        _advance_past_init(engine)
        engine.step()  # ROUND_START

        # Kill one monster manually to trigger first_death morale
        _kill_monster_by_index(engine._ctx, 0)

        # Set engine to CHECK_MORALE and step
        engine._state = EncounterState.CHECK_MORALE
        result = engine.step()

        morale_events = _events_of_type(result.events, MoraleChecked)
        assert len(morale_events) == 1
        assert morale_events[0].passed is False

        # Run to completion — deferred ForcedIntentQueued events and then
        # FleeIntents produce EntityFled events on monster turns
        all_events = list(result.events)
        remaining = _run_to_end(engine)
        all_events.extend(remaining)

        # ForcedIntentQueued events appear in deferred batch
        flee_queued = _events_of_type(all_events, ForcedIntentQueued)
        assert len(flee_queued) >= 1

        fled_events = _events_of_type(all_events, EntityFled)
        assert len(fled_events) >= 1

        victory_events = _events_of_type(all_events, VictoryDetermined)
        assert len(victory_events) == 1
        assert victory_events[0].outcome == EncounterOutcome.PARTY_VICTORY

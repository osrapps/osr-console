"""Tests for the TUI combat screen controller logic.

These tests exercise the manual-mode combat loop that the CombatScreen uses:
monster turns auto-resolved by the engine's tactical provider, PC turns pausing for input.
"""

import pytest

from osrlib.combat import (
    CombatEngine,
    CombatSide,
    EncounterState,
    EventFormatter,
    NeedAction,
    VictoryDetermined,
)
from osrlib.dice_roller import DiceRoll
from osrlib.combat.intents import (
    CastSpellIntent,
    FleeIntent,
    MeleeAttackIntent,
    RangedAttackIntent,
)
from osrlib.combat.state import EncounterOutcome
from osrlib.encounter import Encounter
from osrlib.enums import CharacterClassType
from osrlib.monster import MonsterParty, MonsterStatsBlock
from osrlib.party import Party
from osrlib.treasure import TreasureType


@pytest.fixture
def default_party():
    return Party.get_default_party()


@pytest.fixture
def goblin_stats():
    return MonsterStatsBlock(
        name="Goblin",
        description="A small, nasty creature.",
        armor_class=6,
        hit_dice="1d8",
        num_appearing="2d4",
        attacks_per_round=1,
        damage_per_attack="1d6",
        movement=60,
        save_as_class=CharacterClassType.FIGHTER,
        save_as_level=1,
        morale=7,
        treasure_type=TreasureType.NONE,
        alignment="Chaotic",
    )


@pytest.fixture
def goblin_party(goblin_stats):
    return MonsterParty(goblin_stats)


@pytest.fixture
def weak_goblin_stats():
    """Goblin with 1 HP for easy-kill testing."""
    return MonsterStatsBlock(
        name="Goblin",
        description="A weak goblin.",
        armor_class=9,
        hit_dice="1d1",
        num_appearing="1d1",
        attacks_per_round=1,
        damage_per_attack="1d4",
        movement=60,
        save_as_class=CharacterClassType.FIGHTER,
        save_as_level=1,
        morale=7,
        treasure_type=TreasureType.NONE,
        alignment="Chaotic",
    )


@pytest.fixture
def weak_goblin_party(weak_goblin_stats):
    return MonsterParty(weak_goblin_stats)


@pytest.fixture
def weak_goblin_gang_stats():
    """Multiple weak goblins with enough total XP (5 * 8 = 40)."""
    return MonsterStatsBlock(
        name="Goblin",
        description="A weak goblin.",
        armor_class=9,
        hit_dice="1d1",
        num_appearing="8",
        attacks_per_round=1,
        damage_per_attack="1d4",
        movement=60,
        save_as_class=CharacterClassType.FIGHTER,
        save_as_level=1,
        morale=7,
        treasure_type=TreasureType.NONE,
        alignment="Chaotic",
    )


@pytest.fixture
def weak_goblin_gang(weak_goblin_gang_stats):
    return MonsterParty(weak_goblin_gang_stats)


def _simulate_combat_loop(engine: CombatEngine, max_iterations: int = 200) -> list:
    """Simulate the TUI combat loop: monsters auto-resolved by engine provider, PCs pick first choice.

    Returns all events collected during the encounter.
    """
    all_events = []

    # Initial advance
    results = engine.step_until_decision()
    for r in results:
        all_events.extend(r.events)

    iterations = 0
    while engine.state != EncounterState.ENDED and iterations < max_iterations:
        iterations += 1
        last = results[-1]

        if not last.needs_intent:
            break

        # Find the NeedAction event (only emitted for PC turns)
        need_action = None
        for r in results:
            for event in r.events:
                if isinstance(event, NeedAction):
                    need_action = event

        if need_action is None:
            break

        choices = need_action.available
        if not choices:
            break

        # Pick the first available choice (deterministic)
        chosen = choices[0]
        results = engine.step_until_decision(intent=chosen.intent)
        for r in results:
            all_events.extend(r.events)

    return all_events


class TestManualModeCombatLoop:
    """Tests for the manual-mode combat loop used by CombatScreen."""

    def test_engine_pauses_at_await_intent(self, default_party, goblin_party):
        """In manual mode, the engine should pause at AWAIT_INTENT on the first combatant's turn."""
        engine = CombatEngine(
            pc_party=default_party,
            monster_party=goblin_party,
            auto_resolve_intents=False,
        )
        results = engine.step_until_decision()

        # Should stop at AWAIT_INTENT
        assert engine.state == EncounterState.AWAIT_INTENT
        last = results[-1]
        assert last.needs_intent is True
        assert last.pending_combatant_id is not None

    def test_need_action_has_available_choices(self, default_party, goblin_party):
        """NeedAction events should include available ActionChoice targets."""
        engine = CombatEngine(
            pc_party=default_party,
            monster_party=goblin_party,
            auto_resolve_intents=False,
        )
        results = engine.step_until_decision()

        # Find NeedAction event
        need_actions = [
            event
            for r in results
            for event in r.events
            if isinstance(event, NeedAction)
        ]
        assert len(need_actions) == 1
        need_action = need_actions[0]
        assert len(need_action.available) > 0

        # Each choice should have a label and a valid intent type
        for choice in need_action.available:
            assert choice.label
            assert isinstance(
                choice.intent,
                (MeleeAttackIntent, RangedAttackIntent, CastSpellIntent, FleeIntent),
            )

    def test_monster_turns_auto_resolved_by_engine(self, default_party, goblin_party):
        """In manual mode, monster turns are resolved by the engine's tactical provider.

        NeedAction should only be emitted for PC combatants.
        """
        engine = CombatEngine(
            pc_party=default_party,
            monster_party=goblin_party,
            auto_resolve_intents=False,
        )
        results = engine.step_until_decision()
        last = results[-1]

        # The engine should pause only for PC turns
        if last.needs_intent:
            cid = last.pending_combatant_id
            ref = engine._ctx.combatants[cid]
            assert ref.side == CombatSide.PC, (
                "NeedAction should only be emitted for PCs"
            )

    def test_pc_turn_choices_are_monster_targets(self, default_party, goblin_party):
        """When a PC's turn comes up, available choices should target monsters."""
        engine = CombatEngine(
            pc_party=default_party,
            monster_party=goblin_party,
            auto_resolve_intents=False,
        )

        # In manual mode, step_until_decision pauses only for PC turns
        results = engine.step_until_decision()
        last = results[-1]

        if last.needs_intent:
            need_action = next(
                (
                    event
                    for r in results
                    for event in r.events
                    if isinstance(event, NeedAction)
                ),
                None,
            )
            assert need_action is not None
            # All choices should target monsters (melee/ranged have target_id, spells have target_ids)
            for choice in need_action.available:
                intent = choice.intent
                if hasattr(intent, "target_id"):
                    assert intent.target_id.startswith("monster:")
                elif hasattr(intent, "target_ids"):
                    assert all(tid.startswith("monster:") for tid in intent.target_ids)

    def test_full_encounter_completes(self, default_party, goblin_party):
        """A full encounter should run to completion via the manual mode loop."""
        engine = CombatEngine(
            pc_party=default_party,
            monster_party=goblin_party,
            auto_resolve_intents=False,
        )
        all_events = _simulate_combat_loop(engine)

        assert engine.state == EncounterState.ENDED
        assert engine.outcome in (
            EncounterOutcome.PARTY_VICTORY,
            EncounterOutcome.OPPOSITION_VICTORY,
        )

        # Should have VictoryDetermined event
        victories = [e for e in all_events if isinstance(e, VictoryDetermined)]
        assert len(victories) == 1

    def test_full_encounter_with_weak_monsters(self, default_party, weak_goblin_party):
        """Full encounter with weak monsters should result in party victory."""
        engine = CombatEngine(
            pc_party=default_party,
            monster_party=weak_goblin_party,
            auto_resolve_intents=False,
        )
        _simulate_combat_loop(engine)

        assert engine.state == EncounterState.ENDED
        # Weak goblins (1 HP) should almost always lose to a full default party
        assert engine.outcome == EncounterOutcome.PARTY_VICTORY

    def test_encounter_end_encounter_works_after_manual_combat(
        self, default_party, weak_goblin_party
    ):
        """Encounter.end_encounter() should work correctly after manual-mode combat.

        This mirrors the real CombatScreen flow: pc_party is set by the screen's
        on_mount(), not by start_encounter().
        """
        encounter = Encounter(
            name="Test",
            description="Test encounter",
            monster_party=weak_goblin_party,
        )
        # pc_party is NOT set here — the test verifies the production code path
        # where CombatScreen.on_mount() sets it.

        engine = CombatEngine(
            pc_party=default_party,
            monster_party=weak_goblin_party,
            auto_resolve_intents=False,
        )

        # Mirror what CombatScreen.on_mount() does:
        encounter.pc_party = default_party
        encounter.engine = engine

        _simulate_combat_loop(engine)

        # Now call end_encounter as the TUI callback would
        encounter.end_encounter()

        assert encounter.is_ended is True
        assert encounter.is_started is False

    def test_xp_awarded_after_manual_combat_victory(
        self, default_party, weak_goblin_gang
    ):
        """XP should be awarded when end_encounter() is called after a party victory.

        Regression test: without setting encounter.pc_party in the combat screen,
        end_encounter() silently skips XP awards because of its
        ``if self.pc_party and self.monster_party`` guard.

        Uses deterministic attack stubs so outcome is always party victory and
        total XP (40) exceeds party size for nonzero per-member share.
        """
        encounter = Encounter(
            name="Test",
            description="Test encounter",
            monster_party=weak_goblin_gang,
        )

        engine = CombatEngine(
            pc_party=default_party,
            monster_party=weak_goblin_gang,
            auto_resolve_intents=False,
        )

        # Mirror CombatScreen.on_mount() — this is the fix for the XP bug
        encounter.pc_party = default_party
        encounter.engine = engine

        # Make this test deterministic:
        # - PCs always hit hard enough to one-shot goblins.
        # - Monsters always miss.
        for cid, ref in engine._ctx.combatants.items():
            if cid.startswith("pc:"):
                ref.entity.get_attack_roll = lambda: DiceRoll(1, 20, 20, 0, 20, [20])
                ref.entity.get_damage_roll = lambda: DiceRoll(1, 6, 6, 0, 6, [6])
            elif cid.startswith("monster:"):
                ref.entity.get_to_hit_target_ac = lambda _: 99
                ref.entity.get_attack_rolls = lambda: [DiceRoll(1, 20, 1, 0, 1, [1])]
                ref.entity.get_damage_roll = lambda: DiceRoll(1, 4, 1, 0, 1, [1])

        xp_before = sum(pc.xp for pc in default_party.members)

        _simulate_combat_loop(engine)

        assert engine.outcome == EncounterOutcome.PARTY_VICTORY
        encounter.end_encounter()

        xp_after = sum(pc.xp for pc in default_party.members)
        assert xp_after > xp_before, "Party should have gained XP after victory"

    def test_xp_not_awarded_without_pc_party(self, default_party, weak_goblin_gang):
        """Without pc_party set, end_encounter() must not award XP.

        This test documents the failure mode that the CombatScreen fix prevents.
        """
        encounter = Encounter(
            name="Test",
            description="Test encounter",
            monster_party=weak_goblin_gang,
        )
        # Deliberately do NOT set encounter.pc_party

        engine = CombatEngine(
            pc_party=default_party,
            monster_party=weak_goblin_gang,
            auto_resolve_intents=False,
        )
        encounter.engine = engine

        xp_before = sum(pc.xp for pc in default_party.members)

        _simulate_combat_loop(engine)

        encounter.end_encounter()

        xp_after = sum(pc.xp for pc in default_party.members)
        assert xp_after == xp_before, "XP should not change without pc_party set"

    def test_encounter_log_populated_during_manual_combat(
        self, default_party, weak_goblin_party
    ):
        """The encounter log should accumulate formatted events during manual combat."""
        encounter = Encounter(
            name="Test",
            description="Test encounter",
            monster_party=weak_goblin_party,
        )

        engine = CombatEngine(
            pc_party=default_party,
            monster_party=weak_goblin_party,
            auto_resolve_intents=False,
        )
        formatter = EventFormatter()

        # Simulate what CombatScreen._write_log does
        results = engine.step_until_decision()
        for r in results:
            for event in r.events:
                encounter.log_mesg(formatter.format(event))

        log = encounter.get_encounter_log()
        assert len(log) > 0
        assert "Encounter" in log or "round" in log.lower()

    def test_no_need_action_emitted_for_monsters(self, default_party, goblin_party):
        """NeedAction should never be emitted for monster combatants in manual mode."""
        engine = CombatEngine(
            pc_party=default_party,
            monster_party=goblin_party,
            auto_resolve_intents=False,
        )
        all_events = _simulate_combat_loop(engine)

        need_actions = [e for e in all_events if isinstance(e, NeedAction)]
        for na in need_actions:
            assert na.combatant_id.startswith("pc:"), (
                f"NeedAction emitted for non-PC: {na.combatant_id}"
            )

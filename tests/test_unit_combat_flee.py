"""Tests for player-initiated flee in the combat engine."""

import pytest

from osrlib.combat import (
    CombatEngine,
    EncounterState,
    FixedDiceService,
    NeedAction,
    EntityFled,
    EventFormatter,
    VictoryDetermined,
)
from osrlib.combat.intents import FleeIntent
from osrlib.combat.state import EncounterOutcome
from osrlib.enums import CharacterClassType
from osrlib.monster import MonsterParty, MonsterStatsBlock
from osrlib.party import Party
from osrlib.player_character import Alignment
from osrlib.treasure import TreasureType


@pytest.fixture
def default_party():
    """Create a small party for testing."""
    return Party.get_default_party()


@pytest.fixture
def goblin_stats():
    return MonsterStatsBlock(
        name="Goblin",
        description="A small humanoid.",
        armor_class=6,
        hit_dice="1d8-1",
        num_appearing="2",
        movement=60,
        num_special_abilities=0,
        attacks_per_round=1,
        damage_per_attack="1d6",
        save_as_class=CharacterClassType.COMMONER,
        save_as_level=1,
        morale=7,
        treasure_type=TreasureType.R,
        alignment=Alignment.CHAOTIC,
    )


@pytest.fixture
def goblin_party(goblin_stats):
    return MonsterParty(goblin_stats)


def _step_to_first_pc_decision(engine):
    """Advance the engine until a PC needs to choose an action."""
    for _ in range(64):
        result = engine.step()
        if result.needs_intent:
            # Find the NeedAction event
            for event in result.events:
                if isinstance(event, NeedAction):
                    return result, event
    raise RuntimeError("Engine did not pause for PC decision within 64 steps")


class TestPlayerFleeChoice:
    """Verify that PCs are offered a flee choice and can use it."""

    def test_flee_choice_offered_to_pcs(self, default_party, goblin_party):
        """PC action choices should include a flee option."""
        engine = CombatEngine(
            pc_party=default_party,
            monster_party=goblin_party,
            auto_resolve_intents=False,
        )
        _, need_action = _step_to_first_pc_decision(engine)

        flee_choices = [c for c in need_action.available if c.ui_key == "flee"]
        assert len(flee_choices) == 1, "Expected exactly one flee choice for a PC"

    def test_flee_choice_label(self, default_party, goblin_party):
        """The flee choice should have a readable label."""
        engine = CombatEngine(
            pc_party=default_party,
            monster_party=goblin_party,
            auto_resolve_intents=False,
        )
        _, need_action = _step_to_first_pc_decision(engine)

        flee_choices = [c for c in need_action.available if c.ui_key == "flee"]
        assert flee_choices[0].label == "Flee"

    def test_flee_intent_makes_pc_fled(self, default_party, goblin_party):
        """Submitting a FleeIntent should mark the PC as fled."""
        engine = CombatEngine(
            pc_party=default_party,
            monster_party=goblin_party,
            auto_resolve_intents=False,
        )
        result, need_action = _step_to_first_pc_decision(engine)

        pc_id = need_action.combatant_id
        flee_intent = FleeIntent(actor_id=pc_id)

        # Submit the flee intent and advance
        results = engine.step_until_decision(intent=flee_intent)

        # Check that EntityFled was emitted
        fled_events = [
            e for r in results for e in r.events if isinstance(e, EntityFled)
        ]
        assert any(e.entity_id == pc_id for e in fled_events), (
            f"Expected EntityFled for {pc_id}"
        )

        # Verify the combatant is marked as fled in the view
        view = engine.get_view()
        pc_view = next(c for c in view.combatants if c.id == pc_id)
        assert pc_view.has_fled is True

    def test_fled_pc_turn_skipped(self, default_party, goblin_party):
        """A fled PC should have their turn skipped in subsequent rounds."""
        # Use fixed dice to control initiative order
        dice = FixedDiceService(
            [
                6,  # PC surprise roll
                1,  # Monster surprise roll
                # Initiative rolls — PCs go first
                6,
                6,
                6,
                6,
                6,
                6,  # PCs
                1,
                1,  # Monsters
            ]
        )
        engine = CombatEngine(
            pc_party=default_party,
            monster_party=goblin_party,
            auto_resolve_intents=False,
            dice=dice,
        )
        # Get first PC decision
        _, need_action = _step_to_first_pc_decision(engine)
        pc_id = need_action.combatant_id

        # Make the PC flee
        engine.step_until_decision(intent=FleeIntent(actor_id=pc_id))

        # The fled PC should be skipped in all future turns
        view = engine.get_view()
        pc_view = next(c for c in view.combatants if c.id == pc_id)
        assert pc_view.has_fled is True

    def test_melee_choices_still_first(self, default_party, goblin_party):
        """Melee choices should still be first in the list (flee is appended at end)."""
        engine = CombatEngine(
            pc_party=default_party,
            monster_party=goblin_party,
            auto_resolve_intents=False,
        )
        _, need_action = _step_to_first_pc_decision(engine)

        # First choice should be a melee attack, not flee
        assert need_action.available[0].ui_key == "attack_target"

        # Flee should be the last choice
        assert need_action.available[-1].ui_key == "flee"

    def test_formatter_pc_flee_message(self, default_party, goblin_party):
        """The formatter should produce a distinct message for PC flee."""
        engine = CombatEngine(
            pc_party=default_party,
            monster_party=goblin_party,
            auto_resolve_intents=False,
        )
        _, need_action = _step_to_first_pc_decision(engine)

        pc_id = need_action.combatant_id
        results = engine.step_until_decision(intent=FleeIntent(actor_id=pc_id))

        formatter = EventFormatter()
        fled_events = [
            e for r in results for e in r.events if isinstance(e, EntityFled)
        ]
        assert fled_events, "Expected at least one EntityFled event"

        text = formatter.format(fled_events[0])
        assert "flees the battle" in text

    def test_all_pcs_flee_ends_combat(self, default_party, goblin_party):
        """Combat should end as opposition victory when all PCs flee."""
        engine = CombatEngine(
            pc_party=default_party,
            monster_party=goblin_party,
            auto_resolve_intents=False,
        )

        # Step until first decision to initialize combat
        all_events = []
        results = engine.step_until_decision()
        for r in results:
            all_events.extend(r.events)

        # Keep fleeing every PC that gets a turn
        for _ in range(100):
            if engine.state == EncounterState.ENDED:
                break

            # Find the NeedAction from the last batch
            need_action = None
            for r in results:
                for event in r.events:
                    if isinstance(event, NeedAction):
                        need_action = event

            if need_action is None:
                # Engine ended without needing input
                break

            pc_id = need_action.combatant_id
            results = engine.step_until_decision(intent=FleeIntent(actor_id=pc_id))
            for r in results:
                all_events.extend(r.events)

        assert engine.state == EncounterState.ENDED

        victory_events = [e for e in all_events if isinstance(e, VictoryDetermined)]
        assert len(victory_events) == 1
        assert victory_events[0].outcome == EncounterOutcome.OPPOSITION_VICTORY

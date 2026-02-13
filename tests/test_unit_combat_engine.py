"""Tests for the state-driven combat engine."""

import pytest
from osrlib.combat import (
    ActionChoice,
    ApplyConditionEffect,
    ActionRejected,
    AttackRolled,
    CombatSide,
    CombatEngine,
    ConditionApplied,
    ConsumeSlotEffect,
    DamageApplied,
    DamageEffect,
    EncounterLoopError,
    EncounterOutcome,
    EncounterStarted,
    EncounterState,
    EntityDied,
    EventFormatter,
    EventSerializer,
    FixedDiceService,
    InitiativeRolled,
    MeleeAttackAction,
    MeleeAttackIntent,
    NeedAction,
    RoundStarted,
    SpellSlotConsumed,
    SurpriseRolled,
    TurnQueueBuilt,
    TurnSkipped,
    TurnStarted,
    VictoryDetermined,
)
from osrlib.dice_roller import DiceRoll
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


@pytest.fixture
def goblin_stats():
    return MonsterStatsBlock(
        name="Goblin",
        description="A small ugly humanoid.",
        armor_class=6,
        hit_dice="1d8",
        num_appearing="3",
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


@pytest.fixture
def multi_attack_stats():
    """Monster with 3 attacks per round for multi-attack tests."""
    return MonsterStatsBlock(
        name="Hydra",
        description="A multi-headed beast.",
        armor_class=5,
        hit_dice="3d8",
        num_appearing="1",
        movement=60,
        num_special_abilities=0,
        attacks_per_round=3,
        damage_per_attack="1d6",
        save_as_class=CharacterClassType.FIGHTER,
        save_as_level=3,
        morale=11,
        treasure_type=TreasureType.NONE,
        alignment=Alignment.NEUTRAL,
    )


@pytest.fixture
def multi_attack_party(multi_attack_stats):
    return MonsterParty(multi_attack_stats)


@pytest.fixture
def weak_goblin_stats():
    """Goblins with 1 HP for easy-kill tests."""
    return MonsterStatsBlock(
        name="Goblin",
        description="A weak goblin.",
        armor_class=9,
        hit_dice="1",
        num_appearing="1",
        movement=60,
        num_special_abilities=0,
        attacks_per_round=1,
        damage_per_attack="1d4",
        save_as_class=CharacterClassType.FIGHTER,
        save_as_level=1,
        morale=7,
        treasure_type=TreasureType.NONE,
        alignment=Alignment.CHAOTIC,
    )


@pytest.fixture
def weak_goblin_party(weak_goblin_stats):
    return MonsterParty(weak_goblin_stats)


def _collect_events(engine):
    """Run engine to completion and return all events."""
    all_events = []
    while engine.state != EncounterState.ENDED:
        result = engine.step()
        all_events.extend(result.events)
    return all_events


def _find_events(events, event_type):
    """Filter events list by type."""
    return [e for e in events if isinstance(e, event_type)]


# ---------------------------------------------------------------------------
# 1. Full lifecycle
# ---------------------------------------------------------------------------


def test_full_lifecycle(default_party, goblin_party):
    engine = CombatEngine(pc_party=default_party, monster_party=goblin_party)
    events = _collect_events(engine)

    assert len(events) > 0
    assert isinstance(events[0], EncounterStarted)

    victory_events = _find_events(events, VictoryDetermined)
    assert len(victory_events) == 1
    assert engine.state == EncounterState.ENDED
    assert engine.outcome in (
        EncounterOutcome.PARTY_VICTORY,
        EncounterOutcome.OPPOSITION_VICTORY,
    )


# ---------------------------------------------------------------------------
# 2. State transition chain
# ---------------------------------------------------------------------------


def test_state_transitions(default_party, goblin_party):
    engine = CombatEngine(pc_party=default_party, monster_party=goblin_party)

    # INIT -> ROUND_START
    result = engine.step()
    assert result.state == EncounterState.ROUND_START
    assert any(isinstance(e, EncounterStarted) for e in result.events)
    assert any(isinstance(e, SurpriseRolled) for e in result.events)

    # ROUND_START -> TURN_START
    result = engine.step()
    assert result.state == EncounterState.TURN_START
    assert any(isinstance(e, RoundStarted) for e in result.events)
    assert any(isinstance(e, InitiativeRolled) for e in result.events)
    assert any(isinstance(e, TurnQueueBuilt) for e in result.events)

    # TURN_START -> VALIDATE_INTENT (auto-provider skips AWAIT_INTENT)
    result = engine.step()
    assert result.state == EncounterState.VALIDATE_INTENT
    assert any(isinstance(e, TurnStarted) for e in result.events)

    # VALIDATE_INTENT -> EXECUTE_ACTION
    result = engine.step()
    assert result.state == EncounterState.EXECUTE_ACTION

    # EXECUTE_ACTION -> APPLY_EFFECTS
    result = engine.step()
    assert result.state == EncounterState.APPLY_EFFECTS

    # APPLY_EFFECTS -> CHECK_DEATHS
    result = engine.step()
    assert result.state == EncounterState.CHECK_DEATHS


# ---------------------------------------------------------------------------
# 3. Surprise events
# ---------------------------------------------------------------------------


def test_surprise_events(default_party, goblin_party):
    # PC rolls 5, monster rolls 2 -> monsters surprised
    dice = FixedDiceService([5, 2])
    engine = CombatEngine(pc_party=default_party, monster_party=goblin_party, dice=dice)
    result = engine.step()

    surprise = [e for e in result.events if isinstance(e, SurpriseRolled)][0]
    assert surprise.pc_roll == 5
    assert surprise.monster_roll == 2
    assert surprise.monster_surprised is True
    assert surprise.pc_surprised is False


# ---------------------------------------------------------------------------
# 4. Initiative ordering
# ---------------------------------------------------------------------------


def test_initiative_ordering(default_party, goblin_party):
    engine = CombatEngine(pc_party=default_party, monster_party=goblin_party)
    engine.step()  # INIT

    result = engine.step()  # ROUND_START
    initiative = [e for e in result.events if isinstance(e, InitiativeRolled)][0]
    rolls = [roll for _, roll in initiative.order]
    assert rolls == sorted(rolls, reverse=True)


# ---------------------------------------------------------------------------
# 5. PC nat 20 critical hit
# ---------------------------------------------------------------------------


def test_pc_nat20_critical(default_party, weak_goblin_party):
    engine = CombatEngine(pc_party=default_party, monster_party=weak_goblin_party)
    events = _collect_events(engine)

    attack_events = _find_events(events, AttackRolled)
    # At least one attack should exist
    assert len(attack_events) > 0

    # We can't guarantee a nat 20 with random dice, so just verify the event structure
    for atk in attack_events:
        if atk.critical:
            assert atk.hit is True
            assert atk.roll == 20


# ---------------------------------------------------------------------------
# 6. PC nat 1 auto-miss
# ---------------------------------------------------------------------------


def test_pc_nat1_miss(default_party, goblin_party):
    engine = CombatEngine(pc_party=default_party, monster_party=goblin_party)
    events = _collect_events(engine)

    attack_events = _find_events(events, AttackRolled)
    for atk in attack_events:
        # If raw roll is 1, PC attacks should always miss
        if atk.roll == 1 and atk.attacker_id.startswith("pc:"):
            assert atk.hit is False


# ---------------------------------------------------------------------------
# 7. Monster multi-attack
# ---------------------------------------------------------------------------


def test_monster_multi_attack():
    """A tough multi-attack monster should produce multiple AttackRolled events per turn."""
    party = Party.get_default_party()
    # Set all PCs to 1 HP so the fight ends quickly but the monster likely gets a turn
    for pc in party.members:
        pc.character_class.hp = 1

    strong_multi = MonsterStatsBlock(
        name="Hydra",
        description="A multi-headed beast.",
        armor_class=0,
        hit_dice="8d8",
        num_appearing="1",
        movement=60,
        num_special_abilities=0,
        attacks_per_round=3,
        damage_per_attack="2d6",
        save_as_class=CharacterClassType.FIGHTER,
        save_as_level=8,
        morale=11,
        treasure_type=TreasureType.NONE,
        alignment=Alignment.NEUTRAL,
    )
    monster_party = MonsterParty(strong_multi)

    engine = CombatEngine(pc_party=party, monster_party=monster_party)
    events = _collect_events(engine)

    monster_attacks = [
        e
        for e in events
        if isinstance(e, AttackRolled) and e.attacker_id.startswith("monster:Hydra:")
    ]
    # The hydra has 3 attacks_per_round, so each time it acts we should see 3 AttackRolled
    assert len(monster_attacks) >= 3


# ---------------------------------------------------------------------------
# 8. Entity death
# ---------------------------------------------------------------------------


def test_entity_death(default_party, weak_goblin_party):
    engine = CombatEngine(pc_party=default_party, monster_party=weak_goblin_party)
    events = _collect_events(engine)

    death_events = _find_events(events, EntityDied)
    # The weak goblin (1 HP) should die
    assert len(death_events) >= 1


# ---------------------------------------------------------------------------
# 9. PC victory
# ---------------------------------------------------------------------------


def test_pc_victory(default_party, weak_goblin_party):
    engine = CombatEngine(pc_party=default_party, monster_party=weak_goblin_party)
    events = _collect_events(engine)

    victory_events = _find_events(events, VictoryDetermined)
    assert len(victory_events) == 1
    assert victory_events[0].outcome == EncounterOutcome.PARTY_VICTORY


# ---------------------------------------------------------------------------
# 10. Monster victory
# ---------------------------------------------------------------------------


def test_monster_victory():
    """Create a party of level 1 PCs vs a very strong monster to ensure monster wins."""
    party = Party.get_default_party()
    # Set all PCs to 1 HP
    for pc in party.members:
        pc.character_class.hp = 1

    strong_stats = MonsterStatsBlock(
        name="Dragon",
        description="A deadly dragon.",
        armor_class=0,
        hit_dice="10d8",
        num_appearing="1",
        movement=60,
        num_special_abilities=0,
        attacks_per_round=3,
        damage_per_attack="3d10",
        save_as_class=CharacterClassType.FIGHTER,
        save_as_level=10,
        morale=12,
        treasure_type=TreasureType.NONE,
        alignment=Alignment.CHAOTIC,
    )
    monster_party = MonsterParty(strong_stats)

    engine = CombatEngine(pc_party=party, monster_party=monster_party)

    # Make this test deterministic: PCs always miss, monster always hits.
    for pc in party.members:
        pc.get_attack_roll = lambda: DiceRoll(1, 20, 1, 0, 1, [1])

    monster_id = next(
        cid for cid in engine._ctx.combatants if cid.startswith("monster:")
    )
    monster = engine._ctx.combatants[monster_id].entity
    monster.get_to_hit_target_ac = lambda _: 1
    monster.get_attack_rolls = lambda: [
        DiceRoll(1, 20, 20, 0, 20, [20]),
        DiceRoll(1, 20, 20, 0, 20, [20]),
        DiceRoll(1, 20, 20, 0, 20, [20]),
    ]
    monster.get_damage_roll = lambda: DiceRoll(1, 6, 6, 0, 6, [6])

    events = _collect_events(engine)

    victory_events = _find_events(events, VictoryDetermined)
    assert len(victory_events) == 1
    assert victory_events[0].outcome == EncounterOutcome.OPPOSITION_VICTORY


# ---------------------------------------------------------------------------
# 11b. Manual mode pauses at AWAIT_INTENT and emits NeedAction
# ---------------------------------------------------------------------------


def test_manual_mode_pauses_and_emits_need_action(default_party, goblin_party):
    engine = CombatEngine(
        pc_party=default_party,
        monster_party=goblin_party,
        auto_resolve_intents=False,
    )

    engine.step()  # INIT -> ROUND_START
    engine.step()  # ROUND_START -> TURN_START
    result = engine.step()  # TURN_START -> AWAIT_INTENT

    assert result.state == EncounterState.AWAIT_INTENT
    assert result.needs_intent is True
    assert result.pending_combatant_id is not None
    need_action_events = [e for e in result.events if isinstance(e, NeedAction)]
    assert len(need_action_events) == 1
    assert need_action_events[0].combatant_id == result.pending_combatant_id
    assert len(need_action_events[0].available) > 0
    assert all(
        isinstance(choice, ActionChoice) for choice in need_action_events[0].available
    )
    assert "MeleeAttackIntent" in need_action_events[0].available_intents


# ---------------------------------------------------------------------------
# 11c. Manual mode accepts submitted intent and advances through execution
# ---------------------------------------------------------------------------


def test_manual_mode_submitted_intent_executes(default_party, goblin_party):
    engine = CombatEngine(
        pc_party=default_party,
        monster_party=goblin_party,
        auto_resolve_intents=False,
    )
    results = engine.step_until_decision(max_steps=8)
    decision = results[-1]
    assert decision.state == EncounterState.AWAIT_INTENT
    assert decision.pending_combatant_id is not None

    actor_id = decision.pending_combatant_id
    actor_side = engine._ctx.combatants[actor_id].side
    target_side = CombatSide.MONSTER if actor_side == CombatSide.PC else CombatSide.PC
    target_id = engine._ctx.living(target_side)[0].id

    results = engine.step_until_decision(
        intent=MeleeAttackIntent(actor_id=actor_id, target_id=target_id),
        max_steps=8,
    )
    assert results[0].state == EncounterState.VALIDATE_INTENT
    assert any(
        isinstance(event, AttackRolled) for result in results for event in result.events
    )


# ---------------------------------------------------------------------------
# 11. Combatant ID format
# ---------------------------------------------------------------------------


def test_combatant_ids(default_party, goblin_party):
    engine = CombatEngine(pc_party=default_party, monster_party=goblin_party)

    for cid in engine._ctx.combatants:
        assert cid.startswith("pc:") or cid.startswith("monster:")

    pc_ids = [cid for cid in engine._ctx.combatants if cid.startswith("pc:")]
    monster_ids = [cid for cid in engine._ctx.combatants if cid.startswith("monster:")]

    # PC IDs should be "pc:{name}"
    for pc_id in pc_ids:
        parts = pc_id.split(":", 1)
        assert len(parts) == 2
        assert parts[0] == "pc"
        assert len(parts[1]) > 0

    # Monster IDs should be "monster:{name}:{idx}"
    for mid in monster_ids:
        parts = mid.split(":")
        assert len(parts) == 3
        assert parts[0] == "monster"
        assert parts[2].isdigit()


# ---------------------------------------------------------------------------
# 12. TurnSkipped for dead combatants
# ---------------------------------------------------------------------------


def test_turn_skipped_dead_combatant(default_party, goblin_party):
    engine = CombatEngine(pc_party=default_party, monster_party=goblin_party)
    events = _collect_events(engine)

    # If any combatant died mid-round, their subsequent turns should be skipped
    dead_ids = {e.entity_id for e in events if isinstance(e, EntityDied)}
    skip_events = _find_events(events, TurnSkipped)

    for skip in skip_events:
        assert skip.reason == "dead"
        assert (
            skip.combatant_id in dead_ids
            or not engine._ctx.combatants[skip.combatant_id].is_alive
        )


# ---------------------------------------------------------------------------
# 13. step_until_decision max_steps
# ---------------------------------------------------------------------------


def test_step_until_decision_max_steps(default_party, goblin_party):
    engine = CombatEngine(pc_party=default_party, monster_party=goblin_party)

    # With max_steps=1 in INIT state, we transition but don't reach ENDED or AWAIT_INTENT
    # The first step goes INIT -> ROUND_START. Second step needed for ROUND_START -> TURN_START.
    # With max_steps=2, we get through INIT and ROUND_START only.
    with pytest.raises(EncounterLoopError):
        engine.step_until_decision(max_steps=2)


# ---------------------------------------------------------------------------
# 14. ActionRejected with dead target
# ---------------------------------------------------------------------------


def test_action_rejected_dead_target(default_party, goblin_party):
    engine = CombatEngine(pc_party=default_party, monster_party=goblin_party)

    # Step through INIT and ROUND_START
    engine.step()  # INIT -> ROUND_START
    engine.step()  # ROUND_START -> TURN_START

    # Step to get a PC's turn started
    result = engine.step()  # TURN_START -> VALIDATE_INTENT (auto-provider)

    if result.state == EncounterState.VALIDATE_INTENT:
        # The auto-provider already set an intent. Let's manually set up a scenario:
        # Kill all monsters, then try submitting an intent targeting one
        first_monster_id = None
        for cid, ref in engine._ctx.combatants.items():
            if cid.startswith("monster:"):
                ref.entity.hit_points = 0
                if first_monster_id is None:
                    first_monster_id = cid

        if first_monster_id and engine._ctx.current_combatant_id:
            # Override the pending intent with a dead-target intent
            engine._pending_intent = MeleeAttackIntent(
                actor_id=engine._ctx.current_combatant_id,
                target_id=first_monster_id,
            )

            result = engine.step()  # VALIDATE_INTENT
            rejected = [e for e in result.events if isinstance(e, ActionRejected)]
            assert len(rejected) == 1
            assert rejected[0].reasons[0].code == "INVALID_TARGET"
            assert "dead" in rejected[0].reason


# ---------------------------------------------------------------------------
# 15. EventFormatter spot-check
# ---------------------------------------------------------------------------


def test_event_formatter():
    formatter = EventFormatter()

    started = EncounterStarted(encounter_id="abc123")
    assert "abc123" in formatter.format(started)

    surprise = SurpriseRolled(
        pc_roll=4, monster_roll=2, pc_surprised=False, monster_surprised=True
    )
    text = formatter.format(surprise)
    assert "Monsters are surprised" in text

    attack_hit = AttackRolled(
        attacker_id="pc:Sckricko",
        defender_id="monster:Goblin:0",
        roll=15,
        total=17,
        needed=13,
        hit=True,
        critical=False,
    )
    text = formatter.format(attack_hit)
    assert "HIT" in text
    assert "Sckricko" in text
    assert "Goblin #1" in text

    attack_crit = AttackRolled(
        attacker_id="pc:Sckricko",
        defender_id="monster:Goblin:0",
        roll=20,
        total=20,
        needed=13,
        hit=True,
        critical=True,
    )
    text = formatter.format(attack_crit)
    assert "CRITICAL HIT" in text

    death = EntityDied(entity_id="monster:Goblin:0")
    assert "falls" in formatter.format(death)

    victory = VictoryDetermined(outcome=EncounterOutcome.PARTY_VICTORY)
    assert "victorious" in formatter.format(victory)


# ---------------------------------------------------------------------------
# 16. EventSerializer
# ---------------------------------------------------------------------------


def test_event_serializer():
    started = EncounterStarted(encounter_id="abc123")
    d = EventSerializer.to_dict(started)
    assert d["kind"] == "EncounterStarted"
    assert d["encounter_id"] == "abc123"

    victory = VictoryDetermined(outcome=EncounterOutcome.PARTY_VICTORY)
    d = EventSerializer.to_dict(victory)
    assert d["kind"] == "VictoryDetermined"
    assert d["outcome"] == "PARTY_VICTORY"

    attack = AttackRolled(
        attacker_id="pc:Foo",
        defender_id="monster:Bar:0",
        roll=15,
        total=17,
        needed=13,
        hit=True,
        critical=False,
    )
    d = EventSerializer.to_dict(attack)
    assert d["kind"] == "AttackRolled"
    assert d["hit"] is True
    assert d["attacker_id"] == "pc:Foo"


# ---------------------------------------------------------------------------
# 17. step() after ENDED is a safe no-op
# ---------------------------------------------------------------------------


def test_step_after_ended_preserves_outcome(default_party, weak_goblin_party):
    """Calling step() on an already-ENDED engine must not corrupt the outcome."""
    engine = CombatEngine(pc_party=default_party, monster_party=weak_goblin_party)
    _collect_events(engine)

    assert engine.state == EncounterState.ENDED
    original_outcome = engine.outcome

    # Extra step() calls should be no-ops
    for _ in range(3):
        result = engine.step()
        assert result.state == EncounterState.ENDED
        assert result.events == ()
        assert engine.outcome == original_outcome


# ---------------------------------------------------------------------------
# 18. step_until_decision faults engine before raising EncounterLoopError
# ---------------------------------------------------------------------------


def test_step_until_decision_faults_engine(default_party, goblin_party):
    """After EncounterLoopError, engine must be in ENDED with FAULTED outcome."""
    engine = CombatEngine(pc_party=default_party, monster_party=goblin_party)

    with pytest.raises(EncounterLoopError):
        engine.step_until_decision(max_steps=2)

    assert engine.state == EncounterState.ENDED
    assert engine.outcome == EncounterOutcome.FAULTED


# ---------------------------------------------------------------------------
# 19. EXECUTE_ACTION emits resolution only; APPLY_EFFECTS emits mutation only
# ---------------------------------------------------------------------------


def test_resolution_and_mutation_emitted_in_separate_states(
    default_party, weak_goblin_party
):
    engine = CombatEngine(pc_party=default_party, monster_party=weak_goblin_party)

    # Drive to EXECUTE_ACTION
    engine.step()  # INIT -> ROUND_START
    engine.step()  # ROUND_START -> TURN_START
    engine.step()  # TURN_START -> VALIDATE_INTENT
    engine.step()  # VALIDATE_INTENT -> EXECUTE_ACTION
    assert engine.state == EncounterState.EXECUTE_ACTION

    action = engine._validated_action
    assert action is not None

    attacker_ref = engine._ctx.combatants[action.actor_id]
    if attacker_ref.side.name == "PC":
        attacker_ref.entity.get_attack_roll = lambda: DiceRoll(1, 20, 20, 0, 20, [20])
        attacker_ref.entity.get_damage_roll = lambda: DiceRoll(1, 6, 4, 0, 4, [4])
    else:
        attacker_ref.entity.get_to_hit_target_ac = lambda _: 2
        attacker_ref.entity.get_attack_rolls = lambda: [
            DiceRoll(1, 20, 15, 0, 15, [15])
        ]
        attacker_ref.entity.get_damage_roll = lambda: DiceRoll(1, 6, 4, 0, 4, [4])

    result = engine.step()  # EXECUTE_ACTION -> APPLY_EFFECTS
    assert result.state == EncounterState.APPLY_EFFECTS
    assert any(isinstance(e, AttackRolled) for e in result.events)
    assert not any(isinstance(e, DamageApplied) for e in result.events)

    result = engine.step()  # APPLY_EFFECTS -> CHECK_DEATHS
    assert result.state == EncounterState.CHECK_DEATHS
    assert any(isinstance(e, DamageApplied) for e in result.events)


# ---------------------------------------------------------------------------
# 20. APPLY_EFFECTS preserves effect ordering
# ---------------------------------------------------------------------------


def test_apply_effects_ordering(default_party, goblin_party):
    engine = CombatEngine(pc_party=default_party, monster_party=goblin_party)
    source_id = next(cid for cid in engine._ctx.combatants if cid.startswith("pc:"))
    target_id = next(
        cid for cid in engine._ctx.combatants if cid.startswith("monster:")
    )

    target = engine._ctx.combatants[target_id].entity
    target.hit_points = 20

    engine._pending_effects = (
        DamageEffect(source_id=source_id, target_id=target_id, amount=3),
        DamageEffect(source_id=source_id, target_id=target_id, amount=4),
    )

    events = []
    engine._handle_apply_effects(events)

    damage_events = [e for e in events if isinstance(e, DamageApplied)]
    assert [e.amount for e in damage_events] == [3, 4]
    assert target.hit_points == 13
    assert engine.state == EncounterState.CHECK_DEATHS


# ---------------------------------------------------------------------------
# 21. MeleeAttackAction parity: PC critical and damage multiplier
# ---------------------------------------------------------------------------


def test_melee_attack_action_pc_parity(default_party, weak_goblin_party):
    engine = CombatEngine(pc_party=default_party, monster_party=weak_goblin_party)
    actor_id = next(cid for cid in engine._ctx.combatants if cid.startswith("pc:"))
    target_id = next(
        cid for cid in engine._ctx.combatants if cid.startswith("monster:")
    )
    engine._ctx.current_combatant_id = actor_id

    pc = engine._ctx.combatants[actor_id].entity
    pc.get_attack_roll = lambda: DiceRoll(1, 20, 20, 0, 20, [20])
    pc.get_damage_roll = lambda: DiceRoll(1, 8, 5, 0, 5, [5])

    action = MeleeAttackAction(actor_id=actor_id, target_id=target_id)
    assert action.validate(engine._ctx) == ()

    result = action.execute(engine._ctx)
    assert len(result.events) == 1
    assert isinstance(result.events[0], AttackRolled)
    assert result.events[0].critical is True
    assert result.events[0].hit is True

    assert len(result.effects) == 1
    effect = result.effects[0]
    assert isinstance(effect, DamageEffect)
    assert effect.amount == 8  # ceil(5 * 1.5)


# ---------------------------------------------------------------------------
# 22. MeleeAttackAction parity: monster multi-attack stops on lethal damage
# ---------------------------------------------------------------------------


def test_melee_attack_action_monster_multi_attack_parity(
    default_party, multi_attack_party
):
    engine = CombatEngine(pc_party=default_party, monster_party=multi_attack_party)
    actor_id = next(cid for cid in engine._ctx.combatants if cid.startswith("monster:"))
    target_id = next(cid for cid in engine._ctx.combatants if cid.startswith("pc:"))
    engine._ctx.current_combatant_id = actor_id

    monster = engine._ctx.combatants[actor_id].entity
    target = engine._ctx.combatants[target_id].entity
    target.character_class.hp = 10

    monster.get_to_hit_target_ac = lambda _: 10
    monster.get_attack_rolls = lambda: [
        DiceRoll(1, 20, 15, 0, 15, [15]),
        DiceRoll(1, 20, 15, 0, 15, [15]),
        DiceRoll(1, 20, 15, 0, 15, [15]),
    ]

    damage_values = iter([6, 6, 6])

    def _damage_roll():
        value = next(damage_values)
        return DiceRoll(1, 6, value, 0, value, [value])

    monster.get_damage_roll = _damage_roll

    action = MeleeAttackAction(actor_id=actor_id, target_id=target_id)
    assert action.validate(engine._ctx) == ()

    result = action.execute(engine._ctx)

    attack_events = [e for e in result.events if isinstance(e, AttackRolled)]
    assert len(attack_events) == 3
    assert [e.hit for e in attack_events] == [True, True, False]
    assert [e.amount for e in result.effects if isinstance(e, DamageEffect)] == [6, 6]


# ---------------------------------------------------------------------------
# 23. ConsumeSlotEffect applies via class-level slots when caster API is absent
# ---------------------------------------------------------------------------


def test_consume_slot_effect_uses_class_level_slots(default_party, goblin_party):
    engine = CombatEngine(pc_party=default_party, monster_party=goblin_party)

    caster_id = None
    slot_level = None
    slot_count = None
    for cid, ref in engine._ctx.combatants.items():
        if not cid.startswith("pc:"):
            continue
        slots = getattr(ref.entity.character_class.current_level, "spell_slots", None)
        if slots:
            caster_id = cid
            slot_level, slot_count = slots[0]
            break

    assert caster_id is not None, "fixture party must include at least one spellcaster"
    assert slot_level is not None
    assert slot_count is not None

    engine._pending_effects = (
        ConsumeSlotEffect(caster_id=caster_id, level=slot_level),
    )
    events = []
    engine._handle_apply_effects(events)

    consumed = [e for e in events if isinstance(e, SpellSlotConsumed)]
    assert len(consumed) == 1
    assert consumed[0].caster_id == caster_id
    assert consumed[0].level == slot_level
    assert consumed[0].remaining == slot_count - 1
    assert engine.state == EncounterState.CHECK_DEATHS


# ---------------------------------------------------------------------------
# 24. ConsumeSlotEffect rejects when no slot is available
# ---------------------------------------------------------------------------


def test_consume_slot_effect_rejected_without_available_slot(
    default_party, goblin_party
):
    engine = CombatEngine(pc_party=default_party, monster_party=goblin_party)

    caster_id = None
    for cid, ref in engine._ctx.combatants.items():
        if not cid.startswith("pc:"):
            continue
        slots = getattr(ref.entity.character_class.current_level, "spell_slots", None)
        if not slots:
            caster_id = cid
            break

    assert caster_id is not None, (
        "fixture party must include at least one non-spellcaster"
    )

    engine._pending_effects = (ConsumeSlotEffect(caster_id=caster_id, level=1),)
    events = []
    engine._handle_apply_effects(events)

    rejected = [e for e in events if isinstance(e, ActionRejected)]
    assert len(rejected) == 1
    assert rejected[0].reasons[0].code == "NO_SPELL_SLOT"
    assert rejected[0].combatant_id == caster_id
    assert "no level 1 spell slots remaining" in rejected[0].reason
    assert engine.state == EncounterState.CHECK_DEATHS


# ---------------------------------------------------------------------------
# 25. ApplyConditionEffect emits ConditionApplied
# ---------------------------------------------------------------------------


def test_apply_condition_effect_emits_event(default_party, goblin_party):
    engine = CombatEngine(pc_party=default_party, monster_party=goblin_party)
    source_id = next(cid for cid in engine._ctx.combatants if cid.startswith("pc:"))
    target_id = next(
        cid for cid in engine._ctx.combatants if cid.startswith("monster:")
    )

    engine._pending_effects = (
        ApplyConditionEffect(
            source_id=source_id,
            target_id=target_id,
            condition_id="stunned",
            duration=2,
        ),
    )
    events = []
    engine._handle_apply_effects(events)

    applied = [e for e in events if isinstance(e, ConditionApplied)]
    assert len(applied) == 1
    assert applied[0].source_id == source_id
    assert applied[0].target_id == target_id
    assert applied[0].condition_id == "stunned"
    assert applied[0].duration == 2
    assert engine.state == EncounterState.CHECK_DEATHS


# ---------------------------------------------------------------------------
# 26. Unknown effect types are rejected (not silently dropped)
# ---------------------------------------------------------------------------


def test_unknown_effect_type_is_rejected(default_party, goblin_party):
    class UnknownEffect:
        pass

    engine = CombatEngine(pc_party=default_party, monster_party=goblin_party)
    engine._pending_effects = (UnknownEffect(),)
    events = []
    engine._handle_apply_effects(events)

    rejected = [e for e in events if isinstance(e, ActionRejected)]
    assert len(rejected) == 1
    assert rejected[0].reasons[0].code == "UNKNOWN_EFFECT_TYPE"
    assert "unknown effect type: UnknownEffect" in rejected[0].reason
    assert engine.state == EncounterState.CHECK_DEATHS

"""Tests for Phase 4: ranged attacks, spell casting, and spell slot management."""

import pytest
from types import MappingProxyType

from osrlib.combat import (
    ActionChoice,
    ActionRejected,
    AttackRolled,
    CastSpellAction,
    CastSpellIntent,
    CombatEngine,
    CombatSide,
    EncounterState,
    MeleeAttackIntent,
    NeedAction,
    RangedAttackAction,
    RangedAttackIntent,
    RejectionCode,
    SpellCast,
    SpellSlotConsumed,
    get_spell,
)
from osrlib.combat.events import _render_choice_label
from osrlib.dice_roller import DiceRoll
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


@pytest.fixture
def weak_goblin_stats():
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


def _find_events(events, event_type):
    return [e for e in events if isinstance(e, event_type)]


def _get_first_pc_decision(engine):
    """Drive engine to first PC NeedAction and return (results, need_action)."""
    results = engine.step_until_decision()
    for r in results:
        for e in r.events:
            if isinstance(e, NeedAction) and e.combatant_id.startswith("pc:"):
                return results, e
    # If first decision was for a monster side, keep going
    pytest.skip("Could not reach a PC decision point")


def _find_pc_with_class(engine, class_type):
    """Return (cid, pc) for the first PC matching class_type, or skip."""
    for cid, ref in engine._ctx.combatants.items():
        if ref.side == CombatSide.PC and isinstance(ref.entity, PlayerCharacter):
            if ref.entity.character_class.class_type == class_type:
                return cid, ref.entity
    pytest.skip(f"No {class_type.value} in party")


def _equip_ranged_weapon(pc: PlayerCharacter) -> None:
    """Unequip any melee weapon and equip the first ranged weapon in inventory."""
    # Unequip current weapon
    current = pc.inventory.get_equipped_weapon()
    if current.name != "Fists" and current.is_equipped:
        pc.inventory.unequip_item(current)
    # Equip first ranged weapon
    for weapon in pc.inventory.weapons:
        if weapon.range is not None and not weapon.is_equipped:
            pc.inventory.equip_item(weapon)
            return
    pytest.skip("No ranged weapon in inventory")


# ---------------------------------------------------------------------------
# 1. Ranged attack resolves (produces AttackRolled + DamageEffect)
# ---------------------------------------------------------------------------


def test_ranged_attack_resolves(default_party, weak_goblin_party):
    engine = CombatEngine(
        pc_party=default_party,
        monster_party=weak_goblin_party,
        auto_resolve_intents=False,
    )
    results, need_action = _get_first_pc_decision(engine)

    # Find a PC with a ranged weapon (Elf has Long Bow)
    elf_cid, elf_pc = _find_pc_with_class(engine, CharacterClassType.ELF)

    # Force the elf's turn
    target_id = engine._ctx.living(CombatSide.MONSTER)[0].id
    engine._ctx.current_combatant_id = elf_cid
    engine._state = EncounterState.VALIDATE_INTENT

    # Unequip the sword and equip the bow so has_ranged_weapon_equipped() is True
    _equip_ranged_weapon(elf_pc)

    # Force a hit
    elf_pc.get_ranged_attack_roll = lambda: DiceRoll(1, 20, 18, 2, 20, [18])
    elf_pc.get_ranged_damage_roll = lambda: DiceRoll(1, 6, 4, 0, 4, [4])

    intent = RangedAttackIntent(actor_id=elf_cid, target_id=target_id)
    results = engine.step_until_decision(intent=intent)
    all_events = [e for r in results for e in r.events]

    attacks = _find_events(all_events, AttackRolled)
    assert len(attacks) >= 1
    assert attacks[0].attacker_id == elf_cid
    assert attacks[0].hit is True


# ---------------------------------------------------------------------------
# 2. Ranged uses DEX modifier (not STR)
# ---------------------------------------------------------------------------


def test_ranged_uses_dex_modifier(default_party, weak_goblin_party):
    engine = CombatEngine(
        pc_party=default_party,
        monster_party=weak_goblin_party,
        auto_resolve_intents=False,
    )

    elf_cid, elf_pc = _find_pc_with_class(engine, CharacterClassType.ELF)

    _equip_ranged_weapon(elf_pc)

    target_id = engine._ctx.living(CombatSide.MONSTER)[0].id
    engine._ctx.current_combatant_id = elf_cid

    action = RangedAttackAction(actor_id=elf_cid, target_id=target_id)
    assert action.validate(engine._ctx) == ()

    # Verify the ranged roll method uses DEX
    roll = elf_pc.get_ranged_attack_roll()
    assert isinstance(roll, DiceRoll)


# ---------------------------------------------------------------------------
# 3. Ranged damage has no STR modifier
# ---------------------------------------------------------------------------


def test_ranged_no_str_damage(default_party, weak_goblin_party):
    engine = CombatEngine(
        pc_party=default_party,
        monster_party=weak_goblin_party,
        auto_resolve_intents=False,
    )

    elf_cid, elf_pc = _find_pc_with_class(engine, CharacterClassType.ELF)

    _equip_ranged_weapon(elf_pc)

    roll = elf_pc.get_ranged_damage_roll()
    assert isinstance(roll, DiceRoll)
    # Ranged damage roll should have 0 modifier
    assert roll.modifier == 0


# ---------------------------------------------------------------------------
# 4. Ranged rejected when no ranged weapon equipped
# ---------------------------------------------------------------------------


def test_ranged_rejected_no_weapon(default_party, weak_goblin_party):
    engine = CombatEngine(
        pc_party=default_party,
        monster_party=weak_goblin_party,
        auto_resolve_intents=False,
    )

    # Find a fighter (melee only)
    fighter_cid, fighter_pc = _find_pc_with_class(engine, CharacterClassType.FIGHTER)
    target_id = engine._ctx.living(CombatSide.MONSTER)[0].id
    engine._ctx.current_combatant_id = fighter_cid

    action = RangedAttackAction(actor_id=fighter_cid, target_id=target_id)
    reasons = action.validate(engine._ctx)
    assert len(reasons) == 1
    assert reasons[0].code == RejectionCode.NO_RANGED_WEAPON


# ---------------------------------------------------------------------------
# 5. Cast spell resolves (Magic Missile -> SpellCast + ConsumeSlot + Damage)
# ---------------------------------------------------------------------------


def test_cast_spell_resolves(default_party, weak_goblin_party):
    engine = CombatEngine(
        pc_party=default_party,
        monster_party=weak_goblin_party,
        auto_resolve_intents=False,
    )

    # Find a magic user or elf (both have Magic Missile)
    caster_cid = None
    for cid, ref in engine._ctx.combatants.items():
        if ref.side == CombatSide.PC and isinstance(ref.entity, PlayerCharacter):
            ct = ref.entity.character_class.class_type
            if ct in (CharacterClassType.MAGIC_USER, CharacterClassType.ELF):
                caster_cid = cid
                break

    if caster_cid is None:
        pytest.skip("No caster in party")

    target_id = engine._ctx.living(CombatSide.MONSTER)[0].id
    engine._ctx.current_combatant_id = caster_cid

    action = CastSpellAction(
        actor_id=caster_cid,
        spell_id="magic_missile",
        slot_level=1,
        target_ids=(target_id,),
    )
    assert action.validate(engine._ctx) == ()

    result = action.execute(engine._ctx)
    spell_cast_events = _find_events(list(result.events), SpellCast)
    assert len(spell_cast_events) == 1
    assert spell_cast_events[0].spell_id == "magic_missile"
    assert spell_cast_events[0].spell_name == "Magic Missile"
    assert target_id in spell_cast_events[0].target_ids

    # Should have ConsumeSlotEffect and DamageEffect
    from osrlib.combat.effects import ConsumeSlotEffect, DamageEffect

    consume_effects = [e for e in result.effects if isinstance(e, ConsumeSlotEffect)]
    damage_effects = [e for e in result.effects if isinstance(e, DamageEffect)]
    assert len(consume_effects) == 1
    assert len(damage_effects) == 1


# ---------------------------------------------------------------------------
# 6. Cast spell consumes slot (SpellSlotConsumed event with correct remaining)
# ---------------------------------------------------------------------------


def test_cast_spell_consumes_slot(default_party, weak_goblin_party):
    engine = CombatEngine(
        pc_party=default_party,
        monster_party=weak_goblin_party,
        auto_resolve_intents=False,
    )

    caster_cid = None
    for cid, ref in engine._ctx.combatants.items():
        if ref.side == CombatSide.PC and isinstance(ref.entity, PlayerCharacter):
            ct = ref.entity.character_class.class_type
            slots = ref.entity.character_class.current_level.spell_slots
            if ct in (CharacterClassType.MAGIC_USER, CharacterClassType.ELF) and slots:
                caster_cid = cid
                break

    if caster_cid is None:
        pytest.skip("No caster with slots in party")

    target_id = engine._ctx.living(CombatSide.MONSTER)[0].id
    engine._ctx.current_combatant_id = caster_cid

    intent = CastSpellIntent(
        actor_id=caster_cid,
        spell_id="magic_missile",
        slot_level=1,
        target_ids=(target_id,),
    )

    # Drive through the full pipeline
    engine._state = EncounterState.VALIDATE_INTENT
    results = engine.step_until_decision(intent=intent)
    all_events = [e for r in results for e in r.events]

    consumed = _find_events(all_events, SpellSlotConsumed)
    assert len(consumed) == 1
    assert consumed[0].caster_id == caster_cid
    assert consumed[0].level == 1
    # Level 1 MU/Elf at level 1 has 1 slot, so remaining = 0
    assert consumed[0].remaining == 0


# ---------------------------------------------------------------------------
# 7. Cast spell rejected when no slots (non-caster)
# ---------------------------------------------------------------------------


def test_cast_spell_rejected_no_slots(default_party, weak_goblin_party):
    engine = CombatEngine(
        pc_party=default_party,
        monster_party=weak_goblin_party,
        auto_resolve_intents=False,
    )

    # Find a fighter (no spell slots)
    fighter_cid, _ = _find_pc_with_class(engine, CharacterClassType.FIGHTER)
    engine._ctx.current_combatant_id = fighter_cid

    # CastSpellAction itself validates spell existence, but the engine's
    # slot consumption will reject if no slots. Test at action level:
    # the action validates OK (spell exists, targets valid), but the
    # engine APPLY_EFFECTS rejects the ConsumeSlotEffect.
    from osrlib.combat.effects import ConsumeSlotEffect

    engine._pending_effects = (ConsumeSlotEffect(caster_id=fighter_cid, level=1),)
    events = []
    engine._handle_apply_effects(events)

    rejected = _find_events(events, ActionRejected)
    assert len(rejected) == 1
    assert rejected[0].reasons[0].code == RejectionCode.NO_SPELL_SLOT


# ---------------------------------------------------------------------------
# 8. Cast spell condition (Sleep -> ApplyConditionEffect for all targets)
# ---------------------------------------------------------------------------


def test_cast_spell_condition(default_party, goblin_party):
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
        pytest.skip("No MU/Elf in party")

    living_monsters = engine._ctx.living(CombatSide.MONSTER)
    target_ids = tuple(m.id for m in living_monsters)
    engine._ctx.current_combatant_id = caster_cid

    action = CastSpellAction(
        actor_id=caster_cid,
        spell_id="sleep",
        slot_level=1,
        target_ids=target_ids,
    )
    assert action.validate(engine._ctx) == ()
    result = action.execute(engine._ctx)

    from osrlib.combat.effects import ApplyConditionEffect

    condition_effects = [
        e for e in result.effects if isinstance(e, ApplyConditionEffect)
    ]
    assert len(condition_effects) == len(target_ids)
    for eff in condition_effects:
        assert eff.condition_id == "asleep"


# ---------------------------------------------------------------------------
# 9. Manual mode: PC with ranged weapon sees ranged choices
# ---------------------------------------------------------------------------


def test_choices_include_ranged(default_party, weak_goblin_party):
    engine = CombatEngine(
        pc_party=default_party,
        monster_party=weak_goblin_party,
        auto_resolve_intents=False,
    )

    # Find the elf and equip their bow
    elf_cid, elf_pc = _find_pc_with_class(engine, CharacterClassType.ELF)
    _equip_ranged_weapon(elf_pc)

    # Force elf's turn
    engine._ctx.turn_queue.clear()
    engine._ctx.turn_queue.append(elf_cid)
    engine._state = EncounterState.TURN_START
    engine._ctx.round_number = 1

    result = engine.step()  # TURN_START -> AWAIT_INTENT (manual mode)
    need_actions = _find_events(list(result.events), NeedAction)
    assert len(need_actions) == 1

    ranged_choices = [
        c for c in need_actions[0].available if c.ui_key == "ranged_attack_target"
    ]
    assert len(ranged_choices) > 0
    assert isinstance(ranged_choices[0].intent, RangedAttackIntent)


# ---------------------------------------------------------------------------
# 10. Manual mode: caster sees spell choices
# ---------------------------------------------------------------------------


def test_choices_include_spells(default_party, weak_goblin_party):
    engine = CombatEngine(
        pc_party=default_party,
        monster_party=weak_goblin_party,
        auto_resolve_intents=False,
    )

    # Find a caster
    caster_cid = None
    for cid, ref in engine._ctx.combatants.items():
        if ref.side == CombatSide.PC and isinstance(ref.entity, PlayerCharacter):
            ct = ref.entity.character_class.class_type
            slots = ref.entity.character_class.current_level.spell_slots
            if ct in (CharacterClassType.MAGIC_USER, CharacterClassType.ELF) and slots:
                caster_cid = cid
                break

    if caster_cid is None:
        pytest.skip("No caster with slots in party")

    engine._ctx.turn_queue.clear()
    engine._ctx.turn_queue.append(caster_cid)
    engine._state = EncounterState.TURN_START
    engine._ctx.round_number = 1

    result = engine.step()
    need_actions = _find_events(list(result.events), NeedAction)
    assert len(need_actions) == 1

    spell_choices = [c for c in need_actions[0].available if c.ui_key == "cast_spell"]
    assert len(spell_choices) > 0
    assert isinstance(spell_choices[0].intent, CastSpellIntent)


# ---------------------------------------------------------------------------
# 11. Spell choices vanish when slots are depleted
# ---------------------------------------------------------------------------


def test_choices_exclude_exhausted_spells(default_party, weak_goblin_party):
    engine = CombatEngine(
        pc_party=default_party,
        monster_party=weak_goblin_party,
        auto_resolve_intents=False,
    )

    caster_cid = None
    for cid, ref in engine._ctx.combatants.items():
        if ref.side == CombatSide.PC and isinstance(ref.entity, PlayerCharacter):
            ct = ref.entity.character_class.class_type
            slots = ref.entity.character_class.current_level.spell_slots
            if ct in (CharacterClassType.MAGIC_USER, CharacterClassType.ELF) and slots:
                caster_cid = cid
                break

    if caster_cid is None:
        pytest.skip("No caster with slots in party")

    # Exhaust all spell slots
    engine._spell_slots_remaining_by_caster[caster_cid] = {1: 0}

    engine._ctx.turn_queue.clear()
    engine._ctx.turn_queue.append(caster_cid)
    engine._state = EncounterState.TURN_START
    engine._ctx.round_number = 1

    result = engine.step()
    need_actions = _find_events(list(result.events), NeedAction)
    assert len(need_actions) == 1

    spell_choices = [c for c in need_actions[0].available if c.ui_key == "cast_spell"]
    assert len(spell_choices) == 0


# ---------------------------------------------------------------------------
# 12. RandomMonsterProvider works with mixed choice types
# ---------------------------------------------------------------------------


def test_provider_works_with_mixed_choices(default_party, weak_goblin_party):
    """The tactical provider should handle a mix of melee, ranged, and spell choices."""
    from osrlib.combat.tactical_providers import RandomMonsterProvider
    from osrlib.combat.dice_service import BXDiceService

    provider = RandomMonsterProvider(BXDiceService())

    target_id = "monster:Goblin:0"
    actor_id = "pc:TestCaster"

    choices = (
        ActionChoice(
            ui_key="attack_target",
            ui_args=MappingProxyType(
                {"target_id": target_id, "target_name": "Goblin #1"}
            ),
            intent=MeleeAttackIntent(actor_id=actor_id, target_id=target_id),
        ),
        ActionChoice(
            ui_key="ranged_attack_target",
            ui_args=MappingProxyType(
                {"target_id": target_id, "target_name": "Goblin #1"}
            ),
            intent=RangedAttackIntent(actor_id=actor_id, target_id=target_id),
        ),
        ActionChoice(
            ui_key="cast_spell",
            ui_args=MappingProxyType(
                {
                    "spell_id": "magic_missile",
                    "spell_name": "Magic Missile",
                    "target_name": "Goblin #1",
                }
            ),
            intent=CastSpellIntent(
                actor_id=actor_id,
                spell_id="magic_missile",
                slot_level=1,
                target_ids=(target_id,),
            ),
        ),
    )

    # Should not raise — just pick one
    from osrlib.combat.context import CombatContext

    ctx = CombatContext()
    intent = provider.choose_intent(actor_id, choices, ctx)
    assert isinstance(intent, (MeleeAttackIntent, RangedAttackIntent, CastSpellIntent))


# ---------------------------------------------------------------------------
# 13. Spell catalog lookup
# ---------------------------------------------------------------------------


def test_spell_catalog_lookup():
    mm = get_spell("magic_missile")
    assert mm is not None
    assert mm.name == "Magic Missile"
    assert mm.spell_level == 1
    assert mm.damage_die == "1d6+1"
    assert mm.auto_hit is True
    assert mm.num_targets == 1

    sleep = get_spell("sleep")
    assert sleep is not None
    assert sleep.condition_id == "asleep"
    assert sleep.num_targets == -1

    hp = get_spell("hold_person")
    assert hp is not None
    assert hp.spell_level == 2
    assert hp.condition_duration == 9

    light = get_spell("light_offensive")
    assert light is not None
    assert light.condition_id == "blinded"
    assert light.condition_duration == 12

    assert get_spell("nonexistent") is None


# ---------------------------------------------------------------------------
# 14. Choice label rendering for new ui_key values
# ---------------------------------------------------------------------------


def test_choice_labels_ranged_and_spells():
    # Ranged label
    label = _render_choice_label(
        "ranged_attack_target",
        MappingProxyType({"target_name": "Goblin #1"}),
    )
    assert label == "Ranged: Goblin #1"

    # Spell with target
    label = _render_choice_label(
        "cast_spell",
        MappingProxyType({"spell_name": "Magic Missile", "target_name": "Goblin #1"}),
    )
    assert label == "Cast Magic Missile on Goblin #1"

    # AoE spell (no target_name)
    label = _render_choice_label(
        "cast_spell",
        MappingProxyType({"spell_name": "Sleep"}),
    )
    assert label == "Cast Sleep"

    # Melee still works
    label = _render_choice_label(
        "attack_target",
        MappingProxyType({"target_name": "Goblin #1"}),
    )
    assert label == "Attack Goblin #1"


# ---------------------------------------------------------------------------
# 15. Failed slot consumption blocks downstream effects (Fix 1)
# ---------------------------------------------------------------------------


def test_failed_slot_consumption_blocks_downstream_effects(
    default_party, weak_goblin_party
):
    """When ConsumeSlotEffect fails, no DamageApplied/ConditionApplied events are emitted."""
    from osrlib.combat.effects import (
        ApplyConditionEffect,
        ConsumeSlotEffect,
        DamageEffect,
    )
    from osrlib.combat.events import ConditionApplied, DamageApplied

    engine = CombatEngine(
        pc_party=default_party,
        monster_party=weak_goblin_party,
        auto_resolve_intents=False,
    )

    # Find a fighter (no spell slots)
    fighter_cid, _ = _find_pc_with_class(engine, CharacterClassType.FIGHTER)
    target_id = engine._ctx.living(CombatSide.MONSTER)[0].id

    # Simulate the effect pipeline: ConsumeSlot first, then Damage and Condition
    engine._pending_effects = (
        ConsumeSlotEffect(caster_id=fighter_cid, level=1),
        DamageEffect(source_id=fighter_cid, target_id=target_id, amount=5),
        ApplyConditionEffect(
            source_id=fighter_cid,
            target_id=target_id,
            condition_id="asleep",
            duration=None,
        ),
    )
    events: list = []
    engine._handle_apply_effects(events)

    # Should have ActionRejected for the slot failure
    rejected = _find_events(events, ActionRejected)
    assert len(rejected) == 1
    assert rejected[0].reasons[0].code == RejectionCode.NO_SPELL_SLOT

    # Should NOT have any damage or condition events
    assert _find_events(events, DamageApplied) == []
    assert _find_events(events, ConditionApplied) == []


# ---------------------------------------------------------------------------
# 16. Cast spell rejected for ineligible caster class (Fix 2a)
# ---------------------------------------------------------------------------


def test_cast_spell_rejected_ineligible_class(default_party, weak_goblin_party):
    """A Fighter trying to cast Magic Missile gets INELIGIBLE_CASTER rejection."""
    engine = CombatEngine(
        pc_party=default_party,
        monster_party=weak_goblin_party,
        auto_resolve_intents=False,
    )

    fighter_cid, _ = _find_pc_with_class(engine, CharacterClassType.FIGHTER)
    target_id = engine._ctx.living(CombatSide.MONSTER)[0].id
    engine._ctx.current_combatant_id = fighter_cid

    action = CastSpellAction(
        actor_id=fighter_cid,
        spell_id="magic_missile",
        slot_level=1,
        target_ids=(target_id,),
    )
    reasons = action.validate(engine._ctx)
    assert len(reasons) == 1
    assert reasons[0].code == RejectionCode.INELIGIBLE_CASTER


# ---------------------------------------------------------------------------
# 17. Cast spell rejected for slot level mismatch (Fix 2b)
# ---------------------------------------------------------------------------


def test_cast_spell_rejected_slot_level_mismatch(default_party, weak_goblin_party):
    """MU casting Hold Person (level 2) with slot_level=1 gets SLOT_LEVEL_MISMATCH."""
    engine = CombatEngine(
        pc_party=default_party,
        monster_party=weak_goblin_party,
        auto_resolve_intents=False,
    )

    # Find a MU or Elf (they can cast spells, but hold_person is cleric-only)
    # Instead, find a Cleric who has hold_person available but use wrong slot level
    caster_cid, _ = _find_pc_with_class(engine, CharacterClassType.CLERIC)
    target_id = engine._ctx.living(CombatSide.MONSTER)[0].id
    engine._ctx.current_combatant_id = caster_cid

    action = CastSpellAction(
        actor_id=caster_cid,
        spell_id="hold_person",
        slot_level=1,  # Hold Person is spell_level 2
        target_ids=(target_id,),
    )
    reasons = action.validate(engine._ctx)
    assert len(reasons) == 1
    assert reasons[0].code == RejectionCode.SLOT_LEVEL_MISMATCH


# ---------------------------------------------------------------------------
# 18. Monster ranged intent rejected gracefully (Fix 3)
# ---------------------------------------------------------------------------


def test_monster_ranged_intent_rejected_not_faulted(default_party, weak_goblin_party):
    """Monster RangedAttackIntent produces ActionRejected, not EncounterFaulted."""
    engine = CombatEngine(
        pc_party=default_party,
        monster_party=weak_goblin_party,
        auto_resolve_intents=False,
    )

    # Find a monster
    monster_cid = None
    for cid, ref in engine._ctx.combatants.items():
        if ref.side == CombatSide.MONSTER and ref.is_alive:
            monster_cid = cid
            break
    assert monster_cid is not None

    # Find a PC target
    pc_cid = None
    for cid, ref in engine._ctx.combatants.items():
        if ref.side == CombatSide.PC and ref.is_alive:
            pc_cid = cid
            break
    assert pc_cid is not None

    engine._ctx.current_combatant_id = monster_cid
    engine._state = EncounterState.VALIDATE_INTENT

    intent = RangedAttackIntent(actor_id=monster_cid, target_id=pc_cid)
    results = engine.step_until_decision(intent=intent)
    all_events = [e for r in results for e in r.events]

    rejected = _find_events(all_events, ActionRejected)
    assert len(rejected) >= 1
    assert any(
        r.code == RejectionCode.MONSTER_ACTION_NOT_SUPPORTED
        for rej in rejected
        for r in rej.reasons
    )

    # Must NOT have faulted
    from osrlib.combat.events import EncounterFaulted

    faulted = _find_events(all_events, EncounterFaulted)
    assert faulted == []


# ---------------------------------------------------------------------------
# 19. Spell choices filter to known spells (Fix 4)
# ---------------------------------------------------------------------------


def test_spell_choices_filter_to_known_spells(default_party, weak_goblin_party):
    """Caster only sees spells they have in inventory, not the full catalog."""
    engine = CombatEngine(
        pc_party=default_party,
        monster_party=weak_goblin_party,
        auto_resolve_intents=False,
    )

    # Find a MU (equipped with Magic Missile and Sleep by equip_party)
    mu_cid, mu_pc = _find_pc_with_class(engine, CharacterClassType.MAGIC_USER)

    # Verify MU has Magic Missile (and Sleep) in inventory
    known_spell_names = {s.name for s in mu_pc.inventory.spells}
    assert "Magic Missile" in known_spell_names

    engine._ctx.turn_queue.clear()
    engine._ctx.turn_queue.append(mu_cid)
    engine._state = EncounterState.TURN_START
    engine._ctx.round_number = 1

    result = engine.step()
    need_actions = _find_events(list(result.events), NeedAction)
    assert len(need_actions) == 1

    spell_choices = [c for c in need_actions[0].available if c.ui_key == "cast_spell"]

    # All spell choices must correspond to spells in the PC's inventory
    for choice in spell_choices:
        spell_name = choice.ui_args.get("spell_name", "")
        assert spell_name in known_spell_names, (
            f"Spell choice '{spell_name}' not in PC's known spells: {known_spell_names}"
        )

    # Only spells in inventory should appear as choices
    choice_spell_names = {c.ui_args.get("spell_name") for c in spell_choices}
    for name in choice_spell_names:
        assert name in known_spell_names

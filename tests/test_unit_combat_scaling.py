"""Tests for Phase 4: caster-level scaling and reversed spells."""

from osrlib.combat import (
    CastSpellAction,
    CombatEngine,
    CombatSide,
    EncounterState,
    NeedAction,
)
from osrlib.combat.effects import DamageEffect, HealEffect
from osrlib.combat.events import SavingThrowRolled
from osrlib.combat.spells import get_spell
from osrlib.enums import CharacterClassType

from conftest import find_events, find_pc_with_class


# ---------------------------------------------------------------------------
# Spell catalog: scaling fields exist
# ---------------------------------------------------------------------------


def test_fireball_has_damage_per_level():
    fb = get_spell("fireball")
    assert fb is not None
    assert fb.damage_per_level == "1d6"
    assert fb.save_negates is False  # save halves


def test_lightning_bolt_has_damage_per_level():
    lb = get_spell("lightning_bolt")
    assert lb is not None
    assert lb.damage_per_level == "1d6"


def test_magic_missile_has_projectile_thresholds():
    mm = get_spell("magic_missile")
    assert mm is not None
    assert mm.projectile_thresholds == ((1, 1), (6, 3), (11, 5))


# ---------------------------------------------------------------------------
# Projectile scaling: Magic Missile
# ---------------------------------------------------------------------------


def test_magic_missile_single_projectile_at_level_1(default_party, goblin_party):
    engine = CombatEngine(
        pc_party=default_party,
        monster_party=goblin_party,
        auto_resolve_intents=False,
    )

    mu_cid, _ = find_pc_with_class(engine, CharacterClassType.MAGIC_USER)
    monster_cid = engine._ctx.living(CombatSide.MONSTER)[0].id
    engine._ctx.current_combatant_id = mu_cid

    action = CastSpellAction(
        actor_id=mu_cid,
        spell_id="magic_missile",
        slot_level=1,
        target_ids=(monster_cid,),
    )
    result = action.execute(engine._ctx)

    damage_effects = [e for e in result.effects if isinstance(e, DamageEffect)]
    assert len(damage_effects) == 1


def test_magic_missile_multiple_projectiles_at_level_6(default_party, goblin_party):
    engine = CombatEngine(
        pc_party=default_party,
        monster_party=goblin_party,
        auto_resolve_intents=False,
    )

    mu_cid, mu_pc = find_pc_with_class(engine, CharacterClassType.MAGIC_USER)
    while mu_pc.level < 6:
        mu_pc.grant_xp(50000)

    monster_cid = engine._ctx.living(CombatSide.MONSTER)[0].id
    engine._ctx.current_combatant_id = mu_cid

    action = CastSpellAction(
        actor_id=mu_cid,
        spell_id="magic_missile",
        slot_level=1,
        target_ids=(monster_cid,),
    )
    result = action.execute(engine._ctx)

    damage_effects = [e for e in result.effects if isinstance(e, DamageEffect)]
    assert len(damage_effects) == 3


# ---------------------------------------------------------------------------
# Level-scaling damage: Fireball
# ---------------------------------------------------------------------------


def test_fireball_scales_with_caster_level(default_party, goblin_party):
    engine = CombatEngine(
        pc_party=default_party,
        monster_party=goblin_party,
        auto_resolve_intents=False,
    )

    mu_cid, mu_pc = find_pc_with_class(engine, CharacterClassType.MAGIC_USER)
    while mu_pc.level < 5:
        mu_pc.grant_xp(50000)

    monster_ids = tuple(m.id for m in engine._ctx.living(CombatSide.MONSTER))
    engine._ctx.current_combatant_id = mu_cid

    action = CastSpellAction(
        actor_id=mu_cid,
        spell_id="fireball",
        slot_level=3,
        target_ids=monster_ids,
    )
    result = action.execute(engine._ctx)

    # Fireball targets ALL_ENEMIES — should have one DamageEffect per target
    damage_effects = [e for e in result.effects if isinstance(e, DamageEffect)]
    assert len(damage_effects) == len(monster_ids)

    for de in damage_effects:
        assert de.amount > 0

    # Fireball allows a save for each target
    save_events = find_events(list(result.events), SavingThrowRolled)
    assert len(save_events) == len(monster_ids)


# ---------------------------------------------------------------------------
# Reversed spells
# ---------------------------------------------------------------------------


def test_cause_light_wounds_in_catalog():
    clw = get_spell("cause_light_wounds")
    assert clw is not None
    assert clw.is_reversed is True
    assert clw.reverse_id == "cure_light_wounds"
    assert clw.damage_die == "1d6+1"


def test_cure_light_wounds_has_reverse_id():
    clw = get_spell("cure_light_wounds")
    assert clw is not None
    assert clw.reverse_id == "cause_light_wounds"


def test_cleric_sees_reversed_spells(default_party, goblin_party):
    """A Cleric who knows CLW should also see Cause Light Wounds as a choice."""
    engine = CombatEngine(
        pc_party=default_party,
        monster_party=goblin_party,
        auto_resolve_intents=False,
    )

    cleric_cid, cleric_pc = find_pc_with_class(engine, CharacterClassType.CLERIC)
    cleric_pc.grant_xp(2000)

    known = {s.name for s in cleric_pc.inventory.spells}
    assert "Cure Light Wounds" in known

    engine._ctx.turn_queue.clear()
    engine._ctx.turn_queue.append(cleric_cid)
    engine._state = EncounterState.TURN_START
    engine._ctx.round_number = 1

    result = engine.step()
    need_actions = find_events(list(result.events), NeedAction)
    assert len(need_actions) == 1

    spell_choices = [c for c in need_actions[0].available if c.ui_key == "cast_spell"]
    spell_names = {c.ui_args.get("spell_name") for c in spell_choices}

    assert "Cure Light Wounds" in spell_names
    assert "Cause Light Wounds" in spell_names

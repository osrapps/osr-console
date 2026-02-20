# Phase 4: Ranged attacks + spells + spell slots

## Context

Phases 1-3.5 built a state-driven combat engine with melee-only actions. Phase 4 adds ranged attacks and spell casting — the first real expansion of the action system. The engine already has spell slot tracking (`ConsumeSlotEffect`, `_consume_spell_slot`, `_spell_slots_remaining_by_caster`) and the full effect pipeline (`DamageEffect`, `ApplyConditionEffect`). The main work is adding new intent/action types, choice generation, exemplar spells, and fixing `PlayerCharacter` to use DEX modifiers for ranged.

The Phase 3.5 review podcast flagged two items directly relevant here:

- **Duck-typed spell slot access** (`getattr` chains in `_consume_spell_slot`) — should be tightened with a protocol
- **Empty `target_ids` vs `None` trap** in `CastSpellIntent` — must use `if targets is None` not `if not targets`

## Scope

Per design doc: "Implement ranged/spell actions and effects. Implement `use_spell_slot(level) -> int`." Non-goal: "Full data-driven spell/effects DSL (only scaffolding + exemplar effects)."

Spell-casting monsters are deferred (monster stat blocks lack spell infrastructure). Only PC spellcasting for now.

## Workstreams

### WS1: Intent types (`osrlib/osrlib/combat/intents.py`)

Add two frozen dataclasses and update the union:

```python
@dataclass(frozen=True)
class RangedAttackIntent:
    actor_id: str
    target_id: str

@dataclass(frozen=True)
class CastSpellIntent:
    actor_id: str
    spell_id: str
    slot_level: int
    target_ids: tuple[str, ...]  # empty = self-targeting, never None

ActionIntent = MeleeAttackIntent | RangedAttackIntent | CastSpellIntent
```

### WS2: Spell catalog (`osrlib/osrlib/combat/spells.py` — new file)

Lightweight registry of exemplar combat spells. NOT a full DSL — just data-driven definitions the `CastSpellAction` looks up.

```python
@dataclass(frozen=True)
class SpellDefinition:
    spell_id: str
    name: str
    spell_level: int
    damage_die: str | None       # e.g. "1d6+1", None for non-damage
    num_targets: int             # 1 = single, -1 = all opponents
    auto_hit: bool               # True for Magic Missile
    condition_id: str | None     # e.g. "asleep" for Sleep
    condition_duration: int | None
```

Four exemplar spells (offensive/condition only — healing/self-buffs deferred since they require ally/self targeting):

| Spell | Level | Classes | Effect |
|---|---|---|---|
| Magic Missile | 1 | Magic User, Elf | 1d6+1 damage, auto-hit, single target |
| Sleep | 1 | Magic User, Elf | "asleep" condition on all enemies |
| Hold Person | 2 | Cleric | "held" condition on single target, 9 rounds |
| Light (offensive) | 1 | Cleric, MU, Elf | "blinded" condition on single target, 12 rounds |

Module-level `SPELL_CATALOG: dict[str, SpellDefinition]` with `get_spell(spell_id) -> SpellDefinition | None`.

### WS3: PC ranged methods (`osrlib/osrlib/player_character.py`)

Add three methods:

- `get_ranged_attack_roll() -> DiceRoll` — 1d20 + DEX to-hit modifier (not STR)
- `get_ranged_damage_roll() -> DiceRoll` — weapon damage_die with NO ability modifier
- `has_ranged_weapon_equipped() -> bool` — checks `inventory.get_equipped_weapon().range is not None`

### WS4: Action classes (`osrlib/osrlib/combat/actions.py`)

**RangedAttackAction(CombatAction):**

- `validate()`: Same checks as melee (actor alive, current combatant, target alive, target is opponent) + actor must have ranged weapon equipped
- `execute()`: PC path uses `get_ranged_attack_roll()` / `get_ranged_damage_roll()`. Same nat-20 crit / nat-1 miss rules. Returns `AttackRolled` events + `DamageEffect`
- Monster ranged: not implemented (monsters continue melee only)

**CastSpellAction(CombatAction):**

- Fields: `actor_id`, `spell_id`, `slot_level`, `target_ids`
- `validate()`: Actor alive, current combatant, spell exists in catalog, actor has spell slots remaining at `slot_level`, all targets valid. **Explicit check**: `if target_ids is None` (not `if not target_ids`) per podcast warning
- `execute()`: Looks up `SpellDefinition`. Always produces `ConsumeSlotEffect`. If `damage_die`: rolls damage, produces `DamageEffect` per target. If `condition_id`: produces `ApplyConditionEffect` per target. Emits `SpellCast` resolution event. No saving throws (deferred)

New `RejectionCode` members: `NO_RANGED_WEAPON`, `UNKNOWN_SPELL`, `NO_SPELL_SLOT` (already exists).

### WS5: Events (`osrlib/osrlib/combat/events.py`)

Add one new event:

```python
@dataclass(frozen=True)
class SpellCast(EncounterEvent):
    caster_id: str
    spell_id: str
    spell_name: str
    target_ids: tuple[str, ...]
```

Add `RejectionCode.NO_RANGED_WEAPON` and `RejectionCode.UNKNOWN_SPELL`.

Update `_render_choice_label()` for new `ui_key` values: `"ranged_attack_target"` and `"cast_spell"`.

### WS6: Engine integration (`osrlib/osrlib/combat/engine.py`)

Three changes:

**a) `_action_for_intent()`** — add RangedAttackIntent and CastSpellIntent branches.

**b) `_build_choices_or_await()`** — for PC combatants, after melee choices:

1. If equipped weapon has range, add `ranged_attack_target` choices with `RangedAttackIntent`
2. If PC has spell slots remaining and known spells matching catalog entries, add `cast_spell` choices with `CastSpellIntent`. AoE spells (num_targets=-1) get one choice targeting all enemies. Single-target spells get one choice per living target.

**c) `_get_or_init_spell_slots()`** — helper wrapping existing `_get_spell_slots_for_caster` for lazy init.

**Podcast-flagged fix**: Tighten `_consume_spell_slot` and `_get_spell_slots_for_caster` to use a `SpellCaster` protocol instead of `getattr` chains:

```python
class SpellCaster(Protocol):
    character_class: object  # has .current_level.spell_slots
```

### WS7: Item factories and equip functions (`osrlib/osrlib/item_factories.py`)

- Add `spell_data` dict and `SpellFactory.create_spell(name)` following existing factory pattern
- Update `equip_magic_user()`: add Magic Missile spell to inventory
- Update `equip_elf()`: add Magic Missile spell to inventory
- Update `equip_cleric()`: add Light spell to inventory

### WS8: Formatter + serializer + exports

- `formatter.py`: Add `SpellCast` case to `format()`
- `serializer.py`: No changes needed (generic `dataclasses.asdict` handles new events)
- `__init__.py`: Export `RangedAttackIntent`, `CastSpellIntent`, `RangedAttackAction`, `CastSpellAction`, `SpellCast`, `SpellDefinition`, `get_spell`

### WS9: TUI (`osrgame/osrgame/screen_combat.py`)

Minimal changes — the screen already works generically with `ActionChoice.label`:

- Change prompt from "select a target:" to "select an action:" since choices now include ranged/spell options

### WS10: Tests (`tests/test_unit_combat_ranged_spells.py` — new file)

| # | Test | What it proves |
|---|---|---|
| 1 | `test_ranged_attack_resolves` | RangedAttackIntent produces AttackRolled + DamageEffect |
| 2 | `test_ranged_uses_dex_modifier` | DEX to-hit used, not STR |
| 3 | `test_ranged_no_str_damage` | Damage roll has no STR modifier |
| 4 | `test_ranged_rejected_no_weapon` | Melee-only PC gets NO_RANGED_WEAPON rejection |
| 5 | `test_cast_spell_resolves` | Magic Missile produces SpellCast + ConsumeSlotEffect + DamageEffect |
| 6 | `test_cast_spell_consumes_slot` | SpellSlotConsumed event with correct remaining count |
| 7 | `test_cast_spell_rejected_no_slots` | Non-caster gets rejection |
| 8 | `test_cast_spell_condition` | Sleep produces ApplyConditionEffect for all targets |
| 9 | `test_choices_include_ranged` | Manual mode: PC with bow sees ranged choices |
| 10 | `test_choices_include_spells` | Manual mode: caster sees spell choices |
| 11 | `test_choices_exclude_exhausted_spells` | Spell choices vanish when slots depleted |
| 12 | `test_provider_works_with_mixed_choices` | RandomMonsterProvider handles mixed choice types |
| 13 | `test_spell_catalog_lookup` | get_spell returns correct definition |
| 14 | `test_choice_labels_ranged_and_spells` | Label rendering for new ui_key values |

## Implementation order

1. WS2 (spell catalog) — new file, no deps
2. WS1 (intents) — small addition
3. WS3 (PC ranged methods) — independent of engine
4. WS5 (events + rejection codes) — independent of actions
5. WS4 (action classes) — depends on 1-4
6. WS6 (engine integration) — depends on 1-5
7. WS7 (item factories + equip) — depends on 2
8. WS8 (formatter/serializer/exports)
9. WS9 (TUI prompt label)
10. WS10 (tests) — developed incrementally alongside 4-6

## Verification

```bash
# Run all tests
uv run pytest tests/ -x -q

# Run new Phase 4 tests specifically
uv run pytest tests/test_unit_combat_ranged_spells.py -v

# Run existing combat engine tests (regression)
uv run pytest tests/test_unit_combat_engine.py -v

# Run existing combat screen tests (regression)
uv run pytest tests/test_unit_combat_screen.py -v

# Lint + format
uv run ruff check && uv run ruff format --check
```

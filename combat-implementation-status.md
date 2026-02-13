# Combat engine implementation status

This document tracks progress on the state-driven combat engine refactor described in `combat-design-rev-d.md`. It is intended as a handoff reference for whoever picks up subsequent phases.

## Phase 1: State machine + typed events + baseline formatter (COMPLETE)

**Branch:** `combat-engine-phase1`
**PR:** See linked PR

### What was built

A new `osrlib/osrlib/combat/` subpackage containing:

| Module | Contents |
|---|---|
| `state.py` | `EncounterState` (10 states), `EncounterOutcome`, `EncounterLoopError` |
| `events.py` | 14 frozen dataclass event types inheriting from `EncounterEvent` |
| `intents.py` | `MeleeAttackIntent` + `ActionIntent` type alias |
| `dice_service.py` | `DiceService` protocol, `BXDiceService` (production), `FixedDiceService` (deterministic testing) |
| `context.py` | `CombatantRef`, `CombatSide`, `CombatContext` with canonical ID scheme |
| `engine.py` | `CombatEngine` state machine with `step()` / `step_until_decision()` |
| `formatter.py` | `EventFormatter` — match/case dispatch for human-readable log lines |
| `serializer.py` | `EventSerializer.to_dict()` with `"kind"` discriminator |
| `__init__.py` | Re-exports all public types |

### What was changed

`osrlib/osrlib/encounter.py`:

- **Removed:** `_start_combat()` and `execute_combat_round()` — replaced by the engine
- **Modified:** `start_encounter()` now creates a `CombatEngine`, runs it to completion via `step()` loop, and logs formatted events
- **Added:** `self.engine` attribute on `Encounter` for callers wanting event access
- **Preserved:** All public API (`start_encounter`, `end_encounter`, `to_dict`, `from_dict`, `get_random_encounter`, `log_mesg`, `get_encounter_log`)

### Combatant ID scheme

- PCs: `"pc:{name}"` (e.g., `"pc:Sckricko"`)
- Monsters: `"monster:{name}:{index}"` (e.g., `"monster:Goblin:0"`)

Index = position in `MonsterParty.members` at encounter start. PC names are unique per party.

### State machine flow (Phase 1)

```
INIT -> ROUND_START -> TURN_START -> VALIDATE_INTENT -> EXECUTE_ACTION
  -> CHECK_DEATHS -> CHECK_MORALE (pass-through) -> CHECK_VICTORY
  -> (TURN_START | ROUND_START | ENDED)
```

Phase 1 skips `AWAIT_INTENT` because the auto-provider submits `MeleeAttackIntent` with a random living opponent at `TURN_START`, going directly to `VALIDATE_INTENT`. This matches the old `random.choice()` behavior.

### Combat math reuse

The engine calls the **same entity methods** the old loop called:

- **PC attack:** `pc.character_class.current_level.get_to_hit_target_ac()`, `pc.get_attack_roll()`, `pc.get_damage_roll()`, `defender.apply_damage()`. Nat 20 = auto-hit + 1.5x crit. Nat 1 = auto-miss.
- **Monster attack:** `monster.get_to_hit_target_ac()`, `monster.get_attack_rolls()` (loops `attacks_per_round`), `monster.get_damage_roll()`, `defender.apply_damage()`. No crits for monsters.

### Tests

`tests/test_unit_combat_engine.py` — 16 test cases:

1. Full lifecycle (INIT to ENDED)
2. State transition chain verification
3. Surprise events with fixed dice
4. Initiative ordering (descending sort)
5. PC nat-20 critical hit structure
6. PC nat-1 auto-miss
7. Monster multi-attack (3 AttackRolled events)
8. Entity death
9. PC victory outcome
10. Monster victory outcome
11. Combatant ID format validation
12. TurnSkipped for dead combatants
13. `step_until_decision` max_steps raises `EncounterLoopError`
14. ActionRejected for dead target
15. EventFormatter spot-check
16. EventSerializer with kind discriminator

All existing tests pass with zero regressions (283 passed, 3 skipped).

### Design decisions and deviations

1. **No `APPLY_EFFECTS` state in Phase 1.** The design doc specifies `EXECUTE_ACTION -> APPLY_EFFECTS -> CHECK_DEATHS`. Phase 1 combines resolution + mutation in `EXECUTE_ACTION` (damage is applied inline). Phase 2 should split this by introducing `ActionResult` + `Effect` types and the `APPLY_EFFECTS` state.

2. **`SurpriseRolled` field names.** The design doc uses `party_surprised` / `opposition_surprised`. Phase 1 uses `pc_roll`, `monster_roll`, `pc_surprised`, `monster_surprised` for clarity. Future phases should align or keep — not a breaking change since events are internal.

3. **`AttackRolled.needed` vs `target_ac`.** The design doc uses `target_ac`. Phase 1 uses `needed` (the to-hit threshold after THAC0 calculation). This is more useful for the formatter. Consider adding `target_ac` as well in a future phase.

4. **`ActionRejected` uses a `reason: str`** rather than the `reasons: tuple[Rejection, ...]` from the design doc. The simpler form is adequate for Phase 1; Phase 2+ should introduce the structured `Rejection` type.

5. **`CombatContext` is a mutable state bag** rather than the frozen per-turn snapshot described in the design doc. This was pragmatic for Phase 1 — the engine owns it and rebuilds relevant state at `TURN_START`. Phase 3 (Textual integration) should add the `PartiesView` / `ConditionsView` frozen snapshots for safe external consumption.

6. **`NeedAction` in Phase 1 was defined but not emitted** because auto-provider flow bypassed `AWAIT_INTENT`. This is now partially addressed via `auto_resolve_intents=False` in Phase 3 work-in-progress.

## Phase 2: Pure action interface + APPLY_EFFECTS (COMPLETE)

Phase 2 deliverables now implemented in this branch:

- `ActionResult` + `CombatAction` interface in `combat/actions.py`
- `MeleeAttackAction.validate()` and `execute()` returning `(events, effects)`
- `Effect` union and effect dataclasses in `combat/effects.py`
- `APPLY_EFFECTS` state added between `EXECUTE_ACTION` and `CHECK_DEATHS`
- Mutation events emitted from effect application (`DamageApplied`, `SpellSlotConsumed`, `ConditionApplied`)
- Tests for state separation, effect ordering, melee action parity, and effect handling

### Key files to modify

- `combat/engine.py` — split execute/apply phases and add effect dispatch
- `combat/actions.py` — action abstraction + melee action
- `combat/effects.py` — effect dataclasses + `Effect` union
- `combat/state.py` — `APPLY_EFFECTS` state
- `combat/events.py` — `SpellSlotConsumed`, `ConditionApplied`

## Phase 3: Textual integration (STARTED, PARTIAL)

- Added manual mode in `CombatEngine`:
  `CombatEngine(..., auto_resolve_intents=False)` now emits `NeedAction` at `TURN_START` and pauses in `AWAIT_INTENT`.
- Added tests validating manual pause behavior and submission of external `MeleeAttackIntent`.
- Not yet done:
  - TUI wiring in explore screen
  - menu rendering from available choices
  - frozen `PartiesView` / `ConditionsView` snapshots

## Phase 4: Ranged + spells + slots (NOT STARTED)

## Phase 5: Morale + flee (NOT STARTED)

## Current test count

`tests/test_unit_combat_engine.py` now contains 28 tests (up from 16 in Phase 1),
including Phase 2 coverage and manual `NeedAction` path coverage.

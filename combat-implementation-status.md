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

## Phase 3: Textual integration (COMPLETE)

### What was built

Bard's Tale-style interactive `CombatScreen` that replaces the synchronous
auto-resolve combat flow with a manual-mode engine driven by the TUI.

| File | Change |
|---|---|
| `osrgame/osrgame/screen_combat.py` | **New.** `CombatScreen(Screen)` — grid layout with party roster, monster roster, target `OptionList`, and scrolling combat log. Creates `CombatEngine(auto_resolve_intents=False)`, advances via `step_until_decision()`, auto-resolves monster turns (random PC target), shows target menu for PC turns. Uses `set_timer()` between steps to keep UI responsive. Dismisses with outcome data to explore screen callback. |
| `osrgame/osrgame/widgets.py` | **Modified.** Added `MonsterRosterTable(Container)` — `DataTable` showing monster name, HP, and alive/dead status. `update_table(combatants, announced_deaths)` refreshes from engine context. |
| `osrgame/osrgame/screen_explore.py` | **Modified.** `check_for_encounter()` now pushes `CombatScreen` instead of calling `encounter.start_encounter()` synchronously. Added `_on_combat_ended(result)` callback that calls `encounter.end_encounter()` for XP/treasure awards and `dungeon_assistant.summarize_battle()` for the adventure log. |
| `osrgame/osrgame/screen.tcss` | **Modified.** Added CSS grid rules for `CombatScreen` (40/60 column split, 3-row left column, right column row-span 3). |
| `tests/test_unit_combat_screen.py` | **New.** 8 tests covering the manual-mode combat controller logic. |

### Combat screen layout

```
┌──────────────────────────────────────────────────┐
│ Header                                           │
├─────────────────┬────────────────────────────────┤
│ Party roster    │ Combat log (scrolling)         │
│ Name  HP  AC    │                                │
├─────────────────┤ Round 1                        │
│ Monsters        │ Sckricko attacks Goblin #1...  │
│ Goblin #1  3 HP│ Hit! 4 damage.                  │
├─────────────────┤                                │
│ > Sckricko's    │                                │
│   turn:         │                                │
│ 1. Goblin #1   │                                │
│ 2. Goblin #2   │                                │
└─────────────────┴────────────────────────────────┘
│ Footer: keybindings                              │
└──────────────────────────────────────────────────┘
```

### Combat loop (TUI controller)

1. `ExploreScreen.check_for_encounter()` pushes `CombatScreen` with encounter and party.
2. `on_mount`: creates `CombatEngine(auto_resolve_intents=False)`, kicks off `_advance_combat()`.
3. `_advance_combat()` calls `step_until_decision()`, formats events to log.
4. If `ENDED`: show outcome message, enable Escape to dismiss.
5. If `AWAIT_INTENT` + monster side: auto-pick random living PC target, re-call `_advance_combat(intent=...)` via `set_timer`.
6. If `AWAIT_INTENT` + PC side: populate `OptionList` with `NeedAction.available` choices.
7. On player selection: call `_advance_combat(intent=selected.intent)`.
8. On dismiss: callback calls `encounter.end_encounter()` for XP/treasure, then `summarize_battle()`.

### Tests

`tests/test_unit_combat_screen.py` — 8 test cases:

1. Engine pauses at `AWAIT_INTENT` in manual mode
2. `NeedAction` has available `ActionChoice` targets with `MeleeAttackIntent`
3. Monster auto-resolve (TUI picks random target, submits intent)
4. PC turn choices target monsters (`target_id` starts with `"monster:"`)
5. Full encounter completes via manual-mode loop
6. Full encounter with weak monsters (1 HP goblins) → party victory
7. `Encounter.end_encounter()` works correctly after manual-mode combat
8. Encounter log populated with formatted events during manual combat

### Design decisions

1. **Monster auto-resolve in TUI layer.** The engine stays in pure manual mode for all combatants. The TUI detects monster turns via `CombatSide` and auto-submits a random target intent. This keeps the engine simple and the auto-resolve policy in the controller.

2. **No frozen `PartiesView` / `ConditionsView` snapshots.** The TUI accesses `engine._ctx` directly for roster updates. This is pragmatic for now — the context is only read between `step_until_decision()` calls when the engine is paused. Frozen snapshots remain a future improvement for Phase 4+.

3. **`set_timer()` for UI responsiveness.** Monster turns and combat advancement use `set_timer(0.05, ...)` to yield control to Textual's event loop between steps, preventing the screen from appearing frozen during multi-step monster turns.

## Phase 3.5: Combat architecture stabilization (COMPLETE)

Five workstreams to harden engine contracts and clean up layering issues before Phase 4.

### WS3: Rejection model hardening

- Added `RejectionCode` enum (10 members) to `events.py`
- Changed `Rejection.code` type from `str` to `RejectionCode`
- Updated all rejection constructors in `engine.py` and `actions.py`
- Fixed `serializer.py` to recursively normalize nested enum values in `to_dict()`

### WS4: Decouple action choice labels

- Replaced `ActionChoice.label: str` field with `ui_key: str` + `ui_args: dict[str, str]`
- Added computed `label` property via `_render_choice_label()` for backward compatibility
- Engine builds choices with `ui_key="attack_target"` and structured target args
- Removed regex-based label rewriting from `formatter.py`

### WS1: Engine-owned tactical providers

| File | Change |
|---|---|
| `combat/tactical_providers.py` | **New.** `TacticalProvider` protocol + `RandomMonsterProvider` default implementation |
| `combat/engine.py` | Constructor accepts optional `tactical_provider` param. In manual mode, monsters are auto-resolved by the provider — `NeedAction` only emits for PCs. Auto-resolve mode also routes through provider for consistency. |
| `screen_combat.py` | Removed `import random` and monster auto-resolve branch. `_advance_combat()` simplified: `needs_intent` always means PC turn. |

### WS2: Frozen combat snapshots

| File | Change |
|---|---|
| `combat/views.py` | **New.** `CombatantView` and `CombatView` frozen dataclasses |
| `combat/engine.py` | Added `get_view() -> CombatView` public method |
| `widgets.py` | `MonsterRosterTable.update_table()` accepts `CombatView` instead of raw context dicts |
| `screen_combat.py` | `_refresh_rosters()` calls `engine.get_view()` — no more `engine._ctx` access |

### WS5: Forced-intent contract

- Added `ForcedIntentQueued` and `ForcedIntentApplied` event types to `events.py`
- Added `forced_intents: dict[str, ActionIntent]` field to `CombatContext`
- Added `engine.queue_forced_intent(combatant_id, intent, reason)` public method
- Engine checks forced intents at `TURN_START` before normal decision flow — forced turns bypass `AWAIT_INTENT` and do not emit `NeedAction`
- Added formatter support for new event types

### Exit criteria met

- No UI access to `engine._ctx` — screen uses `engine.get_view()` only
- No AI/tactical logic in TUI — `random.choice` removed from screen; engine handles monsters via provider
- No rejection-string parsing — all codes are `RejectionCode` enum values

### Design decisions

1. **Monster turns invisible to TUI in manual mode.** The engine now auto-resolves all monster turns via `TacticalProvider` before reaching `AWAIT_INTENT`. The TUI only ever sees `NeedAction` for PC combatants. This is a deliberate reversal of the Phase 3 design decision (#1) to keep monster auto-resolve in the controller layer.

2. **`ActionChoice.label` preserved as computed property.** Rather than a breaking removal, `label` is derived from `ui_key`/`ui_args` at read time. Existing code referencing `choice.label` continues to work.

3. **Minimal `CombatView` surface.** Only fields the TUI currently needs are exposed (`combatants`, `announced_deaths`, `round_number`, `current_combatant_id`). Future phases can extend without breaking existing consumers.

4. **Forced-intent scaffolding only.** No morale rules or flee actions — just the queue/consume mechanism and event contract so Phase 5 can plug in without engine-level changes.

### Post-review hardening (COMPLETE)

Follow-up fixes from code review are now implemented:

- **Forced-intent rejection fallback:** Rejected forced intents no longer leave the engine in bare `AWAIT_INTENT`; the engine falls back to normal choice generation (`NeedAction` for PCs / tactical provider for monsters).
- **ActionChoice immutability:** `ActionChoice.ui_args` now uses `MappingProxyType` and is immutable to consumers.
- **Serializer compatibility:** `EventSerializer.to_dict()` now includes computed `ActionChoice.label` in serialized `NeedAction.available` entries and safely handles `MappingProxyType`.
- **Forced-intent observability:** `ForcedIntentQueued` events are buffered and emitted in the next `step()` result.
- **Ended-state safety:** `queue_forced_intent()` now raises a clear `RuntimeError` if called after the encounter has ended.

Additional tests added:

- `test_rejected_forced_intent_falls_back_to_choices`
- `test_action_choice_ui_args_immutable`
- `test_serialized_need_action_includes_label`
- `test_forced_intent_queued_emitted_in_step`
- `test_queue_forced_intent_after_ended_raises`
- `test_forced_rejection_event_ordering`

## Phase 4: Ranged + spells + slots (NOT STARTED)

## Phase 5: Morale + flee (NOT STARTED)

## Current test count

- `tests/test_unit_combat_engine.py`: 43 tests (Phases 1-3 + Phase 3.5 additions + post-review hardening)
- `tests/test_unit_combat_screen.py`: 10 tests (Phase 3 combat controller + Phase 3.5 monster auto-resolve)
- Total suite: 320 passed, 3 skipped

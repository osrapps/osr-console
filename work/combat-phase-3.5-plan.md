# Combat Phase 3.5 Plan

## Objective
Stabilize architecture boundaries and event contracts after Phase 3 so Phase 4 (spells/ranged) and Phase 5 (morale/flee) can be implemented without UI coupling, stringly-typed logic, or brittle state transitions.

## Inputs
- `combat-design-rev-d.md`
- `combat-implementation-status.md`
- `audit-podcast.md`

## Findings To Address
1. Yellow: Monster tactical selection currently lives in `osrgame/osrgame/screen_combat.py` instead of engine/provider layer.
2. Yellow: UI reads mutable internal engine state (`engine._ctx`) directly; no frozen turn snapshots.
3. Yellow: `ActionChoice.label` couples engine payloads to English UI text.
4. Red: Rejection handling must be fully machine-readable for Phase 4 complexity.
5. Red: Forced-intent behavior must not rely on UI-side suppression of `NeedAction`.

## Scope
Phase 3.5 is contract and layering cleanup only. It does not implement full spell catalogs or morale rules.

## Workstreams (in order)

### 1) Engine-owned tactical providers
Target outcome: monster turns are resolved by engine-side policy, not by Textual controller code.

Changes:
- Add `osrlib/osrlib/combat/tactical_providers.py` with:
  - `TacticalProvider` protocol
  - `RandomMonsterProvider` default implementation
- Update `CombatEngine` in `osrlib/osrlib/combat/engine.py`:
  - inject provider(s) via constructor
  - route monster `AWAIT_INTENT` decisions through provider path
  - emit `NeedAction` only when external input is truly required
- Remove monster random-pick logic from `osrgame/osrgame/screen_combat.py`
- Update `osrlib/osrlib/combat/__init__.py` exports

Tests:
- Add/adjust unit tests in `tests/test_unit_combat_engine.py` for provider invocation and deterministic monster intent generation.
- Update `tests/test_unit_combat_screen.py` so screen behavior is fully driven by `NeedAction` events (no side checks + `random.choice` branch).

### 2) Frozen combat snapshots for read-only consumers
Target outcome: UI and future adapters consume immutable views, not mutable engine internals.

Changes:
- Add `osrlib/osrlib/combat/views.py` with frozen dataclasses:
  - `CombatantView`
  - `PartiesView`
  - `ConditionsView`
  - `TurnView` (or equivalent)
- Add engine API in `osrlib/osrlib/combat/engine.py`:
  - `get_view()` (or `current_view` property) returning frozen snapshot
- Update `osrgame/osrgame/screen_combat.py` and `osrgame/osrgame/widgets.py` to refresh tables from view objects instead of `engine._ctx`.

Tests:
- Add immutability and shape tests in `tests/test_unit_combat_engine.py`.
- Update screen tests to use snapshot access path.

### 3) Rejection model hardening (finish migration)
Target outcome: all validation/execution failures are robustly machine-readable; UI and formatters do not parse free text.

Current status note:
- `ActionRejected.reasons` already exists.
- Remaining work is to remove stringly-typed codes and finalize contract.

Changes:
- Add `RejectionCode` enum in `osrlib/osrlib/combat/events.py` (or dedicated module).
- Update `Rejection.code` type from `str` to `RejectionCode`.
- Normalize all rejection emission sites in `osrlib/osrlib/combat/engine.py` and `osrlib/osrlib/combat/actions.py`.
- Keep `ActionRejected.reason` as temporary compatibility shim for one phase; mark deprecated in docstring.
- Ensure formatter (`osrlib/osrlib/combat/formatter.py`) renders from structured reasons, not ad-hoc string checks.

Tests:
- Update assertions to compare enum values in `tests/test_unit_combat_engine.py`.
- Add serialization coverage in `tests/test_unit_combat_engine.py` for enum-backed rejection payloads.

### 4) Decouple action choice data from English labels
Target outcome: `NeedAction.available` is localization-ready and presentation-agnostic.

Changes:
- Replace/augment `ActionChoice.label` in `osrlib/osrlib/combat/events.py` with:
  - `ui_key` (example: `attack_target`)
  - `ui_args` (example: `{"target_id": "monster:Goblin:0"}`)
  - `intent` unchanged
- Update choice generation in `osrlib/osrlib/combat/engine.py`.
- Update formatter and `osrgame/osrgame/screen_combat.py` to render labels from `ui_key` + args.

Tests:
- Update `tests/test_unit_combat_engine.py` and `tests/test_unit_combat_screen.py` to assert structured choice payloads.

### 5) Forced-intent contract correction (pre-Phase 5 guardrail)
Target outcome: forced turns are explicit and do not emit misleading `NeedAction`.

Changes:
- Update contract in `combat-design-rev-d.md`:
  - if forced intent is consumed, do not emit `NeedAction` for that turn
  - emit explicit forced-intent event(s) only
- Add event scaffolding in `osrlib/osrlib/combat/events.py`:
  - `ForcedIntentQueued`
  - `ForcedIntentApplied`
- Add minimal forced-intent queue plumbing in `osrlib/osrlib/combat/context.py` and `osrlib/osrlib/combat/engine.py` without full morale rules.

Tests:
- Add transition tests in `tests/test_unit_combat_engine.py` to prove forced path bypasses `AWAIT_INTENT`/`NeedAction`.
- Add UI regression test in `tests/test_unit_combat_screen.py` that no menu is requested on forced turns.

## Delivery Gates
1. Gate A: Workstreams 1-2 merged and all current tests green.
2. Gate B: Workstreams 3-4 merged, serializer/formatter compatibility verified.
3. Gate C: Workstream 5 merged with new transition tests.
4. Exit criteria: no UI access to `engine._ctx`; no AI logic in TUI; no rejection-string parsing required by any caller.

## Out Of Scope
- Full spell action implementations and targeting rules (Phase 4).
- Morale probabilities, flee pathfinding, and behavior balancing (Phase 5).
- Broader gameplay rebalance.


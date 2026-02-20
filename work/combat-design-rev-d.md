# Technical design: State-driven tactical combat system for osrlib (rev D)

## Summary

Refactor the `osrlib` combat engine from a synchronous, hardcoded loop into a
state-driven encounter runner that:

- can be paused/resumed by external controllers (e.g., Textual TUI),
- delegates tactical decisions to pluggable providers (user or AI),
- resolves combat via polymorphic `CombatAction` implementations,
- emits structured, typed events suitable for UI rendering and DungeonAssistant
  summarization.

Rev D incorporates final review items from the rev C cycle:

- specifies `max_steps` exhaustion behavior in `step_until_decision()`,
- adds implementation guidance for the `TURN_START` handler (most complex single
  state),
- documents formatter obligations around forced-intent `NeedAction` suppression,
- adds `TurnSkipped` event for dead/ineligible combatants,
- sketches `Ruleset` responsibilities,
- completes the typed event catalog (`InitiativeRolled`, `TurnQueueBuilt`,
  `MoraleCheckRolled`),
- consolidates duplicate `EncounterFaulted` definition,
- clarifies `CastSpellIntent` empty-target semantics,
- enriches test fixture guidance (state + events).

## Goals

- Incremental execution: run combat as discrete steps with explicit state
  transitions.
- Separation of concerns:
  - Encounter orchestration (turn order, phase flow, victory checks),
  - Tactical choice (provider),
  - Rule execution (actions),
  - Presentation (formatters/summaries).
- Deterministic testing via injectable dice/RNG.
- Backward-compatible combat math and outcomes (unless explicitly changed).

## Non-goals

- Rebalancing combat rules.
- Full data-driven spell/effects DSL (only scaffolding + exemplar effects).
- Networking/multiplayer.

---

## Encounter state machine

### States

- `INIT`
- `ROUND_START`
- `TURN_START`
- `AWAIT_INTENT`
- `VALIDATE_INTENT`
- `EXECUTE_ACTION`
- `APPLY_EFFECTS`
- `CHECK_DEATHS`
- `CHECK_MORALE`
- `CHECK_VICTORY`
- `ENDED`

### External step contract

```python
@dataclass(frozen=True)
class StepResult:
    state: EncounterState
    needs_intent: bool
    pending_combatant_id: str | None
    events: tuple[EncounterEvent, ...]
```

### Controller convenience method

`step_until_decision()` advances through non-interactive states so UIs do not
need mechanical loops.

```python
class Encounter:
    def step(self, intent: ActionIntent | None = None) -> StepResult: ...

    def step_until_decision(
        self, intent: ActionIntent | None = None, max_steps: int = 64
    ) -> tuple[StepResult, ...]:
        """Repeatedly call step() until either:

        - needs_intent == True, or
        - state == ENDED, or
        - max_steps reached (guard against bugs).

        Decision-point convention:
        - The final element, results[-1], is always the decision-point
          StepResult (needs_intent True) or the terminal StepResult
          (state == ENDED).
        - Intermediate StepResults (results[:-1]) are non-interactive
          transitions.

        Raises:
            EncounterLoopError: If max_steps is exhausted without reaching
                a decision point or terminal state. This indicates a bug
                in the state machine (infinite non-interactive loop).
                The encounter transitions to ENDED with outcome FAULTED
                before the exception is raised, so the encounter is in
                a safe terminal state after the exception.
        """
        ...
```

(Deliberately no `DecisionPoint` wrapper: `results[-1]` is sufficient, and this
keeps API surface minimal.)

### `run()` contract (unchanged)

`run()` is synchronous-only and stops if external intent would be required. UI
controllers use `step()` / `step_until_decision()`.

---

## Typed outcomes

```python
class EncounterOutcome(Enum):
    PARTY_VICTORY = "PARTY_VICTORY"
    OPPOSITION_VICTORY = "OPPOSITION_VICTORY"
    DRAW = "DRAW"
    ABORT = "ABORT"
    FAULTED = "FAULTED"
```

---

## Fault / recovery model

Unexpected exceptions during a `step()` transition end the encounter safely.

```python
@dataclass(frozen=True)
class EncounterFaulted(EncounterEvent):
    state: EncounterState
    actor_id: str | None
    error_type: str
    message: str
```

Behavior:

- emit `EncounterFaulted`,
- set outcome = `FAULTED`,
- transition to `ENDED`,
- subsequent `step()` calls return `ENDED` with no mutation.

This model is also used when `step_until_decision()` exhausts `max_steps`: the
encounter is faulted before the `EncounterLoopError` exception is raised.

---

## Typed event model

Events are immutable dataclasses. Consumers pattern match by class.

### Lifecycle / control

```python
@dataclass(frozen=True)
class EncounterEvent: ...

@dataclass(frozen=True)
class EncounterStarted(EncounterEvent):
    encounter_id: str

@dataclass(frozen=True)
class SurpriseRolled(EncounterEvent):
    party_surprised: bool
    opposition_surprised: bool
    # If the rules produce a numeric surprise delta, include it here as well.

@dataclass(frozen=True)
class RoundStarted(EncounterEvent):
    round_no: int

@dataclass(frozen=True)
class InitiativeRolled(EncounterEvent):
    order: tuple[tuple[str, int], ...]  # (combatant_id, roll) pairs

@dataclass(frozen=True)
class TurnQueueBuilt(EncounterEvent):
    queue: tuple[str, ...]  # ordered combatant IDs for this round

@dataclass(frozen=True)
class TurnStarted(EncounterEvent):
    combatant_id: str

@dataclass(frozen=True)
class TurnSkipped(EncounterEvent):
    combatant_id: str
    reason: str  # e.g. "dead", "incapacitated", "fled"

@dataclass(frozen=True)
class NeedAction(EncounterEvent):
    combatant_id: str
    available: tuple["ActionChoice", ...]
```

### Validation / errors

```python
@dataclass(frozen=True)
class Rejection:
    code: str       # e.g. "NO_AMMO", "NO_SPELL_SLOT", "OUT_OF_RANGE"
    message: str    # human-readable

@dataclass(frozen=True)
class ActionRejected(EncounterEvent):
    combatant_id: str
    reasons: tuple[Rejection, ...]
```

`EncounterFaulted` is defined once in the fault / recovery model section above.

### Resolution vs mutation events (ordering rule)

Ordering contract (explicit):

- `EXECUTE_ACTION` emits **resolution events** only (what happened
  mechanically).
- `APPLY_EFFECTS` emits **mutation events** only (what changed in the world).
- Later check states emit their respective domain events.

Resolution events (examples):

```python
@dataclass(frozen=True)
class AttackRolled(EncounterEvent):
    attacker_id: str
    defender_id: str
    roll: int
    total: int
    target_ac: int
    hit: bool
    critical: bool
```

Mutation events (examples):

```python
@dataclass(frozen=True)
class DamageApplied(EncounterEvent):
    source_id: str
    target_id: str
    amount: int
    target_hp_after: int

@dataclass(frozen=True)
class SpellSlotConsumed(EncounterEvent):
    caster_id: str
    level: int
    remaining: int

@dataclass(frozen=True)
class ConditionApplied(EncounterEvent):
    source_id: str
    target_id: str
    condition_id: str
    duration: int | None
```

### Death / morale / victory

```python
@dataclass(frozen=True)
class EntityDied(EncounterEvent):
    entity_id: str

@dataclass(frozen=True)
class MoraleCheckRolled(EncounterEvent):
    combatant_id: str
    roll: int
    threshold: int
    failed: bool

class ForcedIntentKind(Enum):
    FLEE = "FLEE"

@dataclass(frozen=True)
class ForcedIntentQueued(EncounterEvent):
    combatant_id: str
    kind: ForcedIntentKind

@dataclass(frozen=True)
class ForcedIntentApplied(EncounterEvent):
    combatant_id: str
    kind: ForcedIntentKind

@dataclass(frozen=True)
class VictoryDetermined(EncounterEvent):
    outcome: EncounterOutcome
```

Notes:

- `ForcedIntentQueued` is emitted when morale rules enqueue a forced behavior.
- `ForcedIntentApplied` is emitted when the forced intent is actually consumed
  at `TURN_START`.
- `TurnStarted` is always emitted for every active turn, regardless of
  forced-intent bypass.
- `TurnSkipped` is emitted for dead or ineligible combatants so the event stream
  has no unexplained gaps in turn order.

### Serialization / DungeonAssistant integration

A serializer adapter converts typed events to a stable schema:

- includes `"kind"` discriminator derived from the class,
- uses `dataclasses.asdict()` plus normalization of enums.

DungeonAssistant consumes the serialized event stream (not presentation
strings).

---

## State transition rules

### Transition sketch (single-step granularity)

- `INIT -> ROUND_START`: emit `EncounterStarted`, `SurpriseRolled`.
- `ROUND_START -> TURN_START`: emit `RoundStarted`, `InitiativeRolled`,
  `TurnQueueBuilt`.
- `TURN_START -> AWAIT_INTENT` (normal path): emit `TurnStarted`, `NeedAction`.
- `TURN_START -> VALIDATE_INTENT` (forced-intent path): emit `TurnStarted`,
  `NeedAction`, `ForcedIntentApplied`; consume override.
- `TURN_START -> TURN_START` (skip path): emit `TurnSkipped`; advance to next
  combatant in queue.
- `AWAIT_INTENT -> VALIDATE_INTENT`: only when a compatible intent is provided.
- `VALIDATE_INTENT -> EXECUTE_ACTION`: if legal; else emit `ActionRejected` and
  return to `AWAIT_INTENT`.
- `EXECUTE_ACTION -> APPLY_EFFECTS`: emit resolution events; record effects.
- `APPLY_EFFECTS -> CHECK_DEATHS`: emit mutation events.
- `CHECK_DEATHS -> CHECK_MORALE`: emit `EntityDied` per death.
- `CHECK_MORALE -> CHECK_VICTORY`: emit morale events; enqueue forced behaviors
  for future turns (no recursion).
- `CHECK_VICTORY -> (ENDED | TURN_START | ROUND_START)`: emit
  `VictoryDetermined` if ended; otherwise advance to next turn or next round.

### `TURN_START` implementation guidance

`TURN_START` is the most complex single-state handler in the machine. It
performs the following steps in order:

1. Select the next combatant from the turn queue.
2. If the combatant is dead or ineligible: emit `TurnSkipped`, advance to the
   next combatant (repeat from step 1), or transition to `ROUND_START` if the
   queue is exhausted.
3. Rebuild `CombatContext` for this combatant.
4. Emit `TurnStarted(combatant_id)`.
5. Compute `available_choices(ctx, actor_id)`.
6. Emit `NeedAction(combatant_id, available=...)`.
7. Check for a forced-intent override:
   - If present: consume and remove it, emit
     `ForcedIntentApplied(combatant_id, kind)`, transition to
     `VALIDATE_INTENT` with the forced intent.
   - If absent: transition to `AWAIT_INTENT`.

This handler requires thorough test coverage of all three paths (normal,
forced-intent, skip). The implementation should include a comment mirroring this
step sequence.

---

## Intent model (typed union)

```python
@dataclass(frozen=True)
class MeleeAttackIntent:
    actor_id: str
    target_id: str

@dataclass(frozen=True)
class RangedAttackIntent:
    actor_id: str
    target_id: str
    weapon_id: str | None = None

@dataclass(frozen=True)
class CastSpellIntent:
    actor_id: str
    spell_id: str
    slot_level: int
    target_ids: tuple[str, ...] = ()

@dataclass(frozen=True)
class FleeIntent:
    actor_id: str

ActionIntent = MeleeAttackIntent | RangedAttackIntent | CastSpellIntent | FleeIntent
```

### `CastSpellIntent.target_ids` semantics

An empty `target_ids` tuple means "self-targeting spell" (e.g., Shield, Bless
self). It does **not** mean "no target specified." Spells that require explicit
external targets must have at least one entry in `target_ids`; validation
rejects them otherwise. This distinction is enforced by the individual spell's
`CombatAction.validate()` implementation, which knows whether the spell is
self-targeting or requires external targets.

---

## Tactical providers

Providers choose intents only.

```python
class TacticalProvider(Protocol):
    def get_intent(self, ctx: CombatContext, actor_id: str) -> ActionIntent:
        ...
```

- `AITacticalProvider`: synchronous and used by headless runs / tests.
- UI controllers provide intents externally via `Encounter.step(intent=...)`.

---

## Action choices (UI contract)

### `ActionChoice`

```python
@dataclass(frozen=True)
class ActionChoice:
    label: str
    intent: ActionIntent
```

Design note (explicit coupling):

`label` is presentation-facing and therefore a mild layering leak. This is
accepted for now because:

- labels are derived from canonical game data (weapon/spell names) already owned
  by the engine domain,
- it keeps UI logic a pure function of `NeedAction`,
- it avoids requiring UIs to replicate name formatting rules.

If localization or multiple UI formats become a requirement, refactor `label`
into structured fields and move text generation into the formatter.

---

## CombatContext and views

### Snapshot boundary

`CombatContext` is rebuilt at each `TURN_START` for the active combatant and
remains stable through `AWAIT_INTENT -> VALIDATE_INTENT -> EXECUTE_ACTION` for
that turn.

**Invariant (for maintainers):** No encounter mutations occur between
`TURN_START` and `VALIDATE_INTENT`. Therefore, `NeedAction.available` computed
at `TURN_START` remains valid through intent submission.

### `CombatContext`

```python
@dataclass(frozen=True)
class CombatContext:
    encounter_id: str
    round_no: int
    actor_id: str
    parties: PartiesView
    conditions: ConditionsView
    rules: Ruleset
    dice: DiceService
```

### `ConditionsView` (definition)

`ConditionsView` is a per-turn snapshot that exposes:

- active conditions per entity ID,
- queries: `has(entity_id, condition_id) -> bool` and
  `list(entity_id) -> tuple[str, ...]`,
- derived convenience flags used by legality checks:
  `can_act(entity_id) -> bool` (derived from active conditions such as stunned,
  paralyzed, etc.).

It is read-only, and its contents do not change during the actor's turn (by
snapshot invariant).

### `PartiesView` and party identity (definition)

`PartiesView` is a per-turn snapshot that exposes:

- combatant membership and side identity (party vs opposition),
- target selection queries:
  - `allies_of(entity_id) -> tuple[str, ...]`
  - `opponents_of(entity_id) -> tuple[str, ...]`
  - `is_party(entity_id) -> bool`
- convenience filtered queries:
  - `living_allies_of(entity_id) -> tuple[str, ...]`
  - `living_opponents_of(entity_id) -> tuple[str, ...]`

This enables:

- `EncounterOutcome` semantics (`PARTY_VICTORY` vs `OPPOSITION_VICTORY`),
- target legality and UI menu construction,
- AI provider heuristics (e.g., target selection among living opponents).

### `Ruleset` (responsibilities sketch)

`Ruleset` is a protocol exposing mechanical formulas and constants consumed by
actions and encounter phases. It does not own mutable state.

Responsibilities include:

- to-hit calculation (attack roll modifiers, AC comparison),
- damage modifiers,
- morale thresholds and check formulas,
- surprise determination rules,
- initiative formula,
- any other mechanical constants needed by actions or encounter phases.

`Ruleset` is injected via `CombatContext`, allowing tests to substitute
simplified or deterministic rule implementations.

---

## Action model and effects

### `ActionResult` (pure output)

```python
@dataclass(frozen=True)
class ActionResult:
    events: tuple[EncounterEvent, ...]   # resolution events only
    effects: tuple["Effect", ...]        # mutations to apply later
```

### `CombatAction` interface

```python
class CombatAction(ABC):
    @abstractmethod
    def validate(self, ctx: CombatContext) -> tuple[Rejection, ...]:
        ...

    @abstractmethod
    def execute(self, ctx: CombatContext) -> ActionResult:
        ...
```

### Effect types

```python
@dataclass(frozen=True)
class DamageEffect:
    source_id: str
    target_id: str
    amount: int

@dataclass(frozen=True)
class ConsumeSlotEffect:
    caster_id: str
    level: int

@dataclass(frozen=True)
class ApplyConditionEffect:
    source_id: str
    target_id: str
    condition_id: str
    duration: int | None = None

Effect = DamageEffect | ConsumeSlotEffect | ApplyConditionEffect
```

### `APPLY_EFFECTS` ordering rule (explicit)

- Effects are applied strictly in the order they appear in
  `ActionResult.effects`.
- The engine does not reorder, group, or deduplicate effects.
- For multi-target actions, the ordering is defined by the action
  implementation.

This makes ordering deterministic and testable and avoids hidden engine
heuristics.

### Multi-target semantics

Targets are determined at validation time. All effects are applied even if
earlier effects kill a target, unless a specific effect/spell defines different
behavior. Multi-target actions produce multiple effects and therefore multiple
mutation events.

---

## `NeedAction.available` computation

At `TURN_START`:

1. Engine emits `TurnStarted(combatant_id)`.
2. Engine computes `available_choices(ctx, actor_id)`.
3. Engine emits `NeedAction(combatant_id, available=...)`.
4. Engine transitions to:
   - forced-intent path (if applicable), or
   - `AWAIT_INTENT`.

This ensures the UI always has enough information to render a tactical menu.

---

## Morale and forced intents

### Mechanism

Encounter maintains:

```
forced_intents: dict[str, ActionIntent]  # single-use overrides
```

Rules:

- `CHECK_MORALE` may enqueue:
  `forced_intents[combatant_id] = FleeIntent(actor_id=combatant_id)` and emit
  `ForcedIntentQueued(combatant_id, kind=FLEE)`.
- At `TURN_START`, if `combatant_id` has a forced intent:
  - emit `TurnStarted(combatant_id)` as usual,
  - compute and emit `NeedAction` as usual (for observability; see formatter
    note below),
  - consume override and emit `ForcedIntentApplied(combatant_id, kind=FLEE)`,
  - transition directly to `VALIDATE_INTENT` with the forced intent,
  - bypass `AWAIT_INTENT` and providers.
- Forced intents are single-use and do not persist across turns unless
  re-queued.

### Rationale for emitting `NeedAction` during forced-intent bypass

This preserves uniform event flow for consumers and keeps turn structure
consistent. UIs can optionally show the "menu" but then immediately show forced
behavior.

**Formatter obligation:** When `ForcedIntentApplied` follows `NeedAction` in the
same `step()` result, the formatter should suppress or annotate the `NeedAction`
rendering rather than displaying an actionable menu that was never available to
the player. The formatter can detect this by checking whether both events appear
in the same `StepResult.events` tuple.

---

## DiceService contract

If `roll(expr: str)` is used, supported grammar is:

`NdS` optionally followed by `+M` or `-M`, where:

- `N` is a positive integer count; `N` may be omitted as shorthand for 1 (so
  `d6` == `1d6`),
- `S` is a positive integer sides,
- `M` is an integer modifier.

Examples: `d6`, `1d6`, `2d8+3`, `3d4-1`.

No keep/drop/explode/reroll syntax is relied upon by the engine contract.

```python
T = TypeVar("T")

class DiceService(Protocol):
    def roll(self, expr: str) -> int: ...
    def d20(self) -> int: ...
    def choice(self, items: Sequence[T]) -> T: ...
```

(If the underlying library supports richer syntax, it is not relied upon by the
engine contract.)

---

## Formatter layer (deliverable)

Deliverables:

- **`EventSerializer`**: typed event -> stable dict, including `"kind"`
  discriminator and enum normalization.
- **`EventFormatter`**: typed event -> baseline human text for TUI.

Formatter responsibilities include:

- Rendering combat log entries from the event stream.
- Suppressing or annotating `NeedAction` during forced-intent turns (see morale
  section).
- Converting events into DungeonAssistant-compatible input.

Textual UI consumes:

- `NeedAction.available` to render the tactical menu,
- formatted event stream to render the combat log.

---

## Testing strategy

### Unit tests

- For each action: `validate` + `execute` with deterministic dice.
- For `APPLY_EFFECTS`: verify effect ordering, state mutations, and emitted
  mutation events.
- For `available_choices()`: verify it respects obvious constraints (slots, ammo,
  incapacitated).

### Integration tests

State transitions with `step()` (fine-grained):

- `NeedAction` loops until intent supplied,
- rejection stays in `AWAIT_INTENT`,
- forced-intent bypass transitions to `VALIDATE_INTENT` and emits
  `ForcedIntentApplied`,
- dead/ineligible combatants produce `TurnSkipped` (not `TurnStarted`).

Controller-style tests with `step_until_decision()`:

- one call produces the full batch after an action through victory checks,
- `max_steps` exhaustion produces `EncounterLoopError` and faults the encounter.

`TURN_START` path coverage (all three paths):

- normal path (eligible combatant, no forced intent),
- forced-intent path (override present, consumed and applied),
- skip path (dead/ineligible combatant).

### Regression parity

Fixed dice sequences: compare outcomes between legacy loop and new engine for
baseline scenarios.

### Test fixtures guidance

Store roll sequences and expected outcomes under `tests/fixtures/combat/`
(e.g., JSON files describing dice outputs, expected serialized events, and
expected `StepResult.state` at each step). Capturing state transitions alongside
events ensures the core invariant — correct state machine progression — is
explicitly tested.

---

## Migration plan

### Phase 1: State machine + typed event foundation + baseline formatter

- Implement `EncounterState`, `StepResult`, `step()`,
  `step_until_decision()`.
- Implement typed events required for parity and UI wiring:
  `EncounterStarted`, `SurpriseRolled`, `RoundStarted`, `InitiativeRolled`,
  `TurnQueueBuilt`, `TurnStarted`, `TurnSkipped`, `NeedAction`,
  `AttackRolled`, `DamageApplied`, `EntityDied`, `VictoryDetermined`,
  `ActionRejected`, `EncounterFaulted`.
- Implement baseline `EventSerializer` + `EventFormatter`.
- Provider: internal synchronous "random target melee" for parity.

### Phase 2: Pure action interface + `APPLY_EFFECTS`

- Introduce `ActionResult` and `Effect` types.
- Implement `MeleeAttackAction` returning (resolution events, effects).
- Implement `APPLY_EFFECTS` mutation event emission and effect ordering tests.
- Lock parity via fixed-dice regression tests.

### Phase 3: Textual integration

- UI loop uses `step_until_decision()`; on `NeedAction`, show `available`.
- Submit selected typed intent to `step_until_decision(intent=...)`.
- Expand formatter as needed for UI, including forced-intent suppression.

### Phase 4: Ranged + spells + slots

- Implement ranged/spell actions and effects (`ConsumeSlotEffect`).
- Implement `use_spell_slot(level: int) -> int` (returns remaining).

### Phase 5: Morale + flee

- Implement morale triggers in `CHECK_MORALE`.
- Implement forced-intent queue + `ForcedIntentQueued` / `ForcedIntentApplied`
  events.
- Implement flee resolution rules.

---

## Validation mapping (rev D)

| Phase | Owner | Primary events emitted |
| --- | --- | --- |
| `INIT` | Encounter | `EncounterStarted`, `SurpriseRolled` |
| `ROUND_START` | Encounter / Ruleset | `RoundStarted`, `InitiativeRolled`, `TurnQueueBuilt` |
| `TURN_START` | Encounter | `TurnStarted`, `NeedAction`, (`ForcedIntentApplied` if override consumed), (`TurnSkipped` if ineligible) |
| `VALIDATE_INTENT` | Encounter / Action | `ActionRejected` (on failure) |
| `EXECUTE_ACTION` | CombatAction | `AttackRolled`, (other resolution events) |
| `APPLY_EFFECTS` | Encounter | `DamageApplied`, `SpellSlotConsumed`, `ConditionApplied` |
| `CHECK_DEATHS` | Encounter | `EntityDied` |
| `CHECK_MORALE` | Encounter / Ruleset | `MoraleCheckRolled`, `ForcedIntentQueued` |
| `CHECK_VICTORY` | Encounter | `VictoryDetermined` |
| `ENDED` | Encounter | `EncounterFaulted` (fault path only); otherwise none (terminal) |

---

## Open questions / follow-ups (track in issues)

- Exact spell effect framework: registry vs data-driven definitions.
- Condition system: how specific conditions (stunned, paralyzed, etc.) map to
  `can_act()` and other legality flags.
- Party flee semantics: individual vs group escape, and resulting encounter
  outcome.
- Initiative rerolling rules: per-round or per-encounter (match current behavior
  first, then decide).

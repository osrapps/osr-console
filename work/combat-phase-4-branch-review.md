# Phase 4 Branch Review (`combat-phase-4-ranged-spells`)

## Findings

1. **[HIGH] Spell effects still apply when slot consumption fails**
   - **Where:** `osrlib/osrlib/combat/actions.py:329`, `osrlib/osrlib/combat/engine.py:546`, `osrlib/osrlib/combat/engine.py:533`
   - **What:** `CastSpellAction.execute()` always emits `ConsumeSlotEffect` plus damage/condition effects. In `_handle_apply_effects()`, a `NO_SPELL_SLOT` error on `ConsumeSlotEffect` only `continue`s that effect; subsequent `DamageEffect`/`ApplyConditionEffect` entries still execute.
   - **Impact:** Invalid casts (including no-slot casts) can still damage/disable targets while also emitting rejection.
   - **Why this conflicts with plan:** Phase 4 validation requires "has spell slots remaining" before successful cast resolution.

2. **[HIGH] `CastSpellAction.validate()` does not enforce caster/spell/slot legality**
   - **Where:** `osrlib/osrlib/combat/actions.py:272`, `osrlib/osrlib/combat/actions.py:316`
   - **What:** Validation checks actor/current turn/liveness + spell existence + target liveness, but does **not** check:
     - caster class is allowed by `SpellDefinition.usable_by`
     - slot level matches spell level
     - slot availability before execution
   - **Impact:** Illegal casts are accepted (example: Magic-User can cast `hold_person` using a level 1 slot), bypassing class and progression constraints.
   - **Why this conflicts with plan:** Plan explicitly calls for cast validation of slot availability and spell legality.

3. **[HIGH] Monster ranged intents fault the encounter instead of being rejected**
   - **Where:** `osrlib/osrlib/combat/actions.py:205`, `osrlib/osrlib/combat/actions.py:225`
   - **What:** `RangedAttackAction.validate()` only enforces ranged-weapon checks for PCs, so monster actors pass validation. `execute()` then assumes `PlayerCharacter` and accesses `character_class`, causing `AttributeError` for monsters.
   - **Impact:** A malformed/forced `RangedAttackIntent` for a monster hard-faults the engine (`EncounterFaulted`) instead of returning `ActionRejected`.
   - **Why this conflicts with plan:** Phase 4 says monster ranged is deferred; deferred behavior should reject gracefully, not fault.

4. **[MEDIUM] Spell choice generation ignores known spells and exposes full class catalog**
   - **Where:** `osrlib/osrlib/combat/engine.py:356`, `osrlib/osrlib/item_factories.py:560`, `osrlib/osrlib/item_factories.py:643`
   - **What:** `_build_choices_or_await()` iterates all `SPELL_CATALOG` entries matching class + slots, without filtering to spells the PC actually knows/owns.
   - **Impact:** Casters can select spells not granted by loadout (e.g., MU/Elf can cast `Sleep` immediately despite only adding `Magic Missile` in equip functions).
   - **Why this conflicts with plan:** Plan states choices should be based on known spells matching catalog entries.

## Test Coverage Gaps

- No end-to-end test verifies that failed slot consumption blocks all downstream spell effects.
- No validation test asserts rejection for class-ineligible spells or spell-level/slot-level mismatch.
- No test asserts monster `RangedAttackIntent` is rejected without faulting the encounter.

## Brief Summary

Phase 4 adds the intended surface area (intents/actions/events/catalog/choices), but core validation invariants for spell legality are currently incomplete, and one deferred-path (`monster` ranged intent) can crash the encounter. These should be corrected before treating the branch as rules-complete for Phase 4.

"""Human-readable text formatter for combat events.

Output style is designed to match the existing log messages from ``encounter.py``
so that ``DungeonAssistant.summarize_battle()`` receives similar input.
"""

from osrlib.combat.events import (
    ActionRejected,
    AttackRolled,
    ConditionApplied,
    DamageApplied,
    EncounterEvent,
    EncounterFaulted,
    EncounterStarted,
    EntityDied,
    EntityFled,
    ForcedIntentApplied,
    ForcedIntentQueued,
    InitiativeRolled,
    MoraleChecked,
    NeedAction,
    RoundStarted,
    SpellCast,
    SpellSlotConsumed,
    SurpriseRolled,
    TurnQueueBuilt,
    TurnSkipped,
    TurnStarted,
    VictoryDetermined,
)
from osrlib.combat.state import EncounterOutcome


class EventFormatter:
    """Formats combat events into human-readable log lines."""

    @staticmethod
    def _display_combatant(combatant_id: str) -> str:
        """Convert canonical combatant IDs into player-facing names."""
        if combatant_id.startswith("pc:"):
            _, name = combatant_id.split(":", 1)
            return name

        if combatant_id.startswith("monster:"):
            parts = combatant_id.split(":")
            if len(parts) == 3:
                _, name, idx = parts
                if idx.isdigit():
                    return f"{name} #{int(idx) + 1}"
                return name

        return combatant_id

    def format(self, event: EncounterEvent) -> str:
        """Return a single-line string for *event*."""
        match event:
            case EncounterStarted(encounter_id=eid):
                return f"Encounter {eid} begins."

            case SurpriseRolled(
                pc_roll=pr, monster_roll=mr, pc_surprised=pcs, monster_surprised=ms
            ):
                if pcs:
                    return f"PCs are surprised! (PC roll: {pr}, Monster roll: {mr})"
                elif ms:
                    return (
                        f"Monsters are surprised! (PC roll: {pr}, Monster roll: {mr})"
                    )
                return f"No surprise. (PC roll: {pr}, Monster roll: {mr})"

            case RoundStarted(round_number=rn):
                return f"Round {rn} begins."

            case InitiativeRolled(order=order):
                parts = [
                    f"{self._display_combatant(combatant_id)} ({roll})"
                    for combatant_id, roll in order
                ]
                return f"Initiative: {', '.join(parts)}"

            case TurnQueueBuilt(queue=q):
                turn_order = [
                    self._display_combatant(combatant_id) for combatant_id in q
                ]
                return f"Turn order: {', '.join(turn_order)}"

            case TurnStarted(combatant_id=cid):
                return f"{self._display_combatant(cid)}'s turn."

            case TurnSkipped(combatant_id=cid, reason=reason):
                return f"{self._display_combatant(cid)}'s turn is skipped ({reason})."

            case NeedAction(combatant_id=cid, available=choices):
                labels = [choice.label for choice in choices]
                return f"Choose action for {self._display_combatant(cid)}: {', '.join(labels)}"

            case AttackRolled(
                attacker_id=aid, defender_id=did, total=tot, needed=n, hit=h, critical=c
            ):
                attacker = self._display_combatant(aid)
                defender = self._display_combatant(did)
                if c:
                    return (
                        f"{attacker} attacks {defender}: HIT (rolled {tot} vs {n}) "
                        "CRITICAL HIT!"
                    )
                result = "HIT" if h else "MISS"
                return f"{attacker} attacks {defender}: {result} (rolled {tot} vs {n})."

            case DamageApplied(
                source_id=sid, target_id=tid, amount=amt, target_hp_after=hp
            ):
                source = self._display_combatant(sid)
                target = self._display_combatant(tid)
                return (
                    f"{source} deals {amt} damage to {target}. "
                    f"{target} has {max(hp, 0)} HP remaining."
                )

            case SpellCast(caster_id=cid, spell_name=name, target_ids=tids):
                caster = self._display_combatant(cid)
                targets = ", ".join(self._display_combatant(t) for t in tids)
                if targets:
                    return f"{caster} casts {name} on {targets}."
                return f"{caster} casts {name}."

            case SpellSlotConsumed(caster_id=cid, level=level, remaining=rem):
                caster = self._display_combatant(cid)
                return f"{caster} uses a level {level} spell slot ({rem} remaining)."

            case ConditionApplied(
                source_id=sid, target_id=tid, condition_id=cond, duration=dur
            ):
                duration_text = "permanent" if dur is None else f"{dur} rounds"
                source = self._display_combatant(sid)
                target = self._display_combatant(tid)
                return f"{source} applies {cond} to {target} ({duration_text})."

            case ForcedIntentQueued(combatant_id=cid, reason=reason):
                return f"{self._display_combatant(cid)} is forced to act ({reason})."

            case ForcedIntentApplied(combatant_id=cid):
                return f"{self._display_combatant(cid)}'s forced action is applied."

            case MoraleChecked(
                monster_morale=mm,
                roll=roll,
                passed=passed,
                trigger=trigger,
            ):
                result = "passed" if passed else "failed"
                trigger_text = trigger.replace("_", " ")
                return (
                    f"Morale check ({trigger_text}): rolled {roll} vs {mm} — {result}."
                )

            case EntityDied(entity_id=eid):
                return f"{self._display_combatant(eid)} falls!"

            case EntityFled(entity_id=eid):
                name = self._display_combatant(eid)
                if eid.startswith("pc:"):
                    return f"{name} flees the battle!"
                return f"{name} flees!"

            case VictoryDetermined(outcome=outcome):
                if outcome == EncounterOutcome.PARTY_VICTORY:
                    return "The party is victorious!"
                elif outcome == EncounterOutcome.OPPOSITION_VICTORY:
                    return "The party has been defeated."
                return "Encounter ended in a fault."

            case ActionRejected(combatant_id=cid, reasons=reasons):
                reason_text = "; ".join(rejection.message for rejection in reasons)
                return (
                    f"Action rejected for {self._display_combatant(cid)}: {reason_text}"
                )

            case EncounterFaulted(state=st, error_type=et, message=msg):
                return f"FAULT in {st.name}: [{et}] {msg}"

            case _:
                return repr(event)

    def format_all(
        self, events: tuple[EncounterEvent, ...] | list[EncounterEvent]
    ) -> str:
        """Format a sequence of events, joining with newlines."""
        return "\n".join(self.format(e) for e in events)

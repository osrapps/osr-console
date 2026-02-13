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
    InitiativeRolled,
    NeedAction,
    RoundStarted,
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

    def format(self, event: EncounterEvent) -> str:
        """Return a single-line string for *event*."""
        match event:
            case EncounterStarted(encounter_id=eid):
                return f"Encounter {eid} started."

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
                return f"Starting combat round {rn}..."

            case InitiativeRolled(order=order):
                parts = [f"{name}={roll}" for name, roll in order]
                return f"Initiative: {', '.join(parts)}"

            case TurnQueueBuilt(queue=q):
                return f"Turn order: {', '.join(q)}"

            case TurnStarted(combatant_id=cid):
                return f"{cid}'s turn."

            case TurnSkipped(combatant_id=cid, reason=reason):
                return f"{cid}'s turn skipped ({reason})."

            case NeedAction(combatant_id=cid, available=choices):
                labels = [choice.label for choice in choices]
                return f"Awaiting action for {cid}: {', '.join(labels)}"

            case AttackRolled(
                attacker_id=aid, defender_id=did, total=tot, needed=n, hit=h, critical=c
            ):
                result = "HIT" if h else "MISS"
                crit = " CRITICAL HIT!" if c else ""
                return (
                    f"{aid} attacked {did} (rolled {tot}, needed {n}): {result}{crit}"
                )

            case DamageApplied(
                source_id=sid, target_id=tid, amount=amt, target_hp_after=hp
            ):
                return f"{sid} dealt {amt} damage to {tid} (HP: {hp})."

            case SpellSlotConsumed(caster_id=cid, level=level, remaining=rem):
                return f"{cid} used a level {level} spell slot ({rem} remaining)."

            case ConditionApplied(
                source_id=sid, target_id=tid, condition_id=cond, duration=dur
            ):
                duration_text = "permanent" if dur is None else f"{dur} rounds"
                return f"{sid} applied {cond} to {tid} ({duration_text})."

            case EntityDied(entity_id=eid):
                return f"{eid} was killed!"

            case VictoryDetermined(outcome=outcome):
                if outcome == EncounterOutcome.PARTY_VICTORY:
                    return "The party is victorious!"
                elif outcome == EncounterOutcome.OPPOSITION_VICTORY:
                    return "The party has been defeated."
                return "Encounter ended in a fault."

            case ActionRejected(combatant_id=cid, reasons=reasons):
                reason_text = "; ".join(rejection.message for rejection in reasons)
                return f"Action rejected for {cid}: {reason_text}"

            case EncounterFaulted(state=st, error_type=et, message=msg):
                return f"FAULT in {st.name}: [{et}] {msg}"

            case _:
                return repr(event)

    def format_all(
        self, events: tuple[EncounterEvent, ...] | list[EncounterEvent]
    ) -> str:
        """Format a sequence of events, joining with newlines."""
        return "\n".join(self.format(e) for e in events)

"""Typed event dataclasses emitted by the combat engine."""

from dataclasses import dataclass
from enum import Enum, auto
from types import MappingProxyType

from osrlib.combat.intents import ActionIntent
from osrlib.combat.state import EncounterOutcome, EncounterState


class TurnResult(Enum):
    """Outcome of a Turn Undead attempt."""

    IMPOSSIBLE = auto()
    FAILED = auto()
    TURNED = auto()
    DESTROYED = auto()


class RejectionCode(Enum):
    """Enumerated rejection codes for combat action validation failures."""

    NO_INTENT = auto()
    UNSUPPORTED_INTENT = auto()
    INVALID_ACTOR = auto()
    NOT_CURRENT_COMBATANT = auto()
    ACTOR_DEAD = auto()
    INVALID_TARGET = auto()
    TARGET_NOT_OPPONENT = auto()
    NO_SPELL_SLOT = auto()
    NO_RANGED_WEAPON = auto()
    UNKNOWN_SPELL = auto()
    UNKNOWN_EFFECT_TYPE = auto()
    NO_VALIDATED_ACTION = auto()
    INELIGIBLE_CASTER = auto()
    SLOT_LEVEL_MISMATCH = auto()
    MONSTER_ACTION_NOT_SUPPORTED = auto()
    TARGET_NOT_ALLY = auto()
    ITEM_NOT_THROWABLE = auto()
    ITEM_NOT_IN_INVENTORY = auto()


@dataclass(frozen=True)
class EncounterEvent:
    """Base class for all combat events."""


@dataclass(frozen=True)
class EncounterStarted(EncounterEvent):
    """Emitted once when the engine enters INIT."""

    encounter_id: str


@dataclass(frozen=True)
class SurpriseRolled(EncounterEvent):
    """Emitted during INIT with surprise roll results."""

    pc_roll: int
    monster_roll: int
    pc_surprised: bool
    monster_surprised: bool


@dataclass(frozen=True)
class RoundStarted(EncounterEvent):
    """Emitted at the start of each combat round."""

    round_number: int


@dataclass(frozen=True)
class InitiativeRolled(EncounterEvent):
    """Emitted after initiative is rolled for all combatants."""

    order: tuple[tuple[str, int], ...]


@dataclass(frozen=True)
class TurnQueueBuilt(EncounterEvent):
    """Emitted after the turn queue is assembled from initiative order."""

    queue: tuple[str, ...]


@dataclass(frozen=True)
class TurnStarted(EncounterEvent):
    """Emitted when a living combatant's turn begins."""

    combatant_id: str


@dataclass(frozen=True)
class TurnSkipped(EncounterEvent):
    """Emitted when a dead combatant's turn is skipped."""

    combatant_id: str
    reason: str


@dataclass(frozen=True)
class Rejection:
    """Structured reason for an action validation or execution rejection."""

    code: RejectionCode
    message: str


@dataclass(frozen=True)
class ActionChoice:
    """A UI-facing actionable choice for the active combatant."""

    ui_key: str
    ui_args: MappingProxyType
    intent: ActionIntent

    @property
    def label(self) -> str:
        """Human-readable label derived from ``ui_key`` and ``ui_args``."""
        return _render_choice_label(self.ui_key, self.ui_args)


def _render_choice_label(ui_key: str, ui_args: MappingProxyType) -> str:
    """Render a human-readable label from structured action-choice data."""
    if ui_key == "attack_target":
        return f"Attack {ui_args.get('target_name', ui_args.get('target_id', '???'))}"
    if ui_key == "ranged_attack_target":
        return f"Ranged: {ui_args.get('target_name', ui_args.get('target_id', '???'))}"
    if ui_key == "cast_spell":
        spell_name = ui_args.get("spell_name", ui_args.get("spell_id", "???"))
        target = ui_args.get("target_name", "")
        if target:
            return f"Cast {spell_name} on {target}"
        return f"Cast {spell_name}"
    if ui_key == "use_item":
        item_name = ui_args.get("item_name", "???")
        target = ui_args.get("target_name", "")
        if target:
            return f"Throw {item_name} at {target}"
        return f"Use {item_name}"
    if ui_key == "flee":
        return "Flee"
    if ui_key == "turn_undead":
        return "Turn undead"
    return ui_key


@dataclass(frozen=True)
class NeedAction(EncounterEvent):
    """Emitted when the engine pauses for an external intent."""

    combatant_id: str
    available: tuple[ActionChoice, ...] = ()

    @property
    def available_intents(self) -> tuple[str, ...]:
        """Backward-compatible intent names used by older formatter/tests."""
        return tuple(type(choice.intent).__name__ for choice in self.available)


@dataclass(frozen=True)
class AttackRolled(EncounterEvent):
    """Emitted for each attack roll (PC or monster)."""

    attacker_id: str
    defender_id: str
    roll: int
    total: int
    needed: int
    hit: bool
    critical: bool


@dataclass(frozen=True)
class DamageApplied(EncounterEvent):
    """Emitted when damage is dealt to a combatant."""

    source_id: str
    target_id: str
    amount: int
    target_hp_after: int


@dataclass(frozen=True)
class SpellSlotConsumed(EncounterEvent):
    """Emitted when a spell slot is consumed."""

    caster_id: str
    level: int
    remaining: int


@dataclass(frozen=True)
class ConditionApplied(EncounterEvent):
    """Emitted when a named condition is applied."""

    source_id: str
    target_id: str
    condition_id: str
    duration: int | None


@dataclass(frozen=True)
class SpellCast(EncounterEvent):
    """Emitted when a spell is successfully cast."""

    caster_id: str
    spell_id: str
    spell_name: str
    target_ids: tuple[str, ...]


@dataclass(frozen=True)
class MoraleChecked(EncounterEvent):
    """Emitted when a B/X morale check is rolled for the monster group."""

    monster_morale: int
    roll: int
    modifier: int
    passed: bool
    trigger: str  # "first_death" or "half_incapacitated"
    checks_passed_total: int
    now_immune: bool


@dataclass(frozen=True)
class EntityDied(EncounterEvent):
    """Emitted when a combatant's HP drops to zero."""

    entity_id: str


@dataclass(frozen=True)
class EntityFled(EncounterEvent):
    """Emitted when a combatant flees from combat."""

    entity_id: str


@dataclass(frozen=True)
class VictoryDetermined(EncounterEvent):
    """Emitted when one side has been defeated."""

    outcome: EncounterOutcome


@dataclass(frozen=True)
class ActionRejected(EncounterEvent):
    """Emitted when a submitted intent fails validation."""

    combatant_id: str
    reasons: tuple[Rejection, ...]

    @property
    def reason(self) -> str:
        """Backward-compatible plain-text view used by older callers."""
        return "; ".join(rejection.message for rejection in self.reasons)


@dataclass(frozen=True)
class ForcedIntentQueued(EncounterEvent):
    """Emitted when a forced intent is queued for a combatant (e.g. morale/flee)."""

    combatant_id: str
    intent: ActionIntent
    reason: str


@dataclass(frozen=True)
class ForcedIntentApplied(EncounterEvent):
    """Emitted when a forced intent is consumed and applied to a combatant's turn."""

    combatant_id: str
    intent: ActionIntent


@dataclass(frozen=True)
class HealingApplied(EncounterEvent):
    """Emitted when healing is applied to a combatant."""

    source_id: str
    target_id: str
    amount: int
    target_hp_after: int


@dataclass(frozen=True)
class ItemUsed(EncounterEvent):
    """Emitted when a combat item is used (e.g. thrown oil flask)."""

    actor_id: str
    item_name: str
    target_ids: tuple[str, ...]


@dataclass(frozen=True)
class ModifierApplied(EncounterEvent):
    """Emitted when a temporary stat modifier is applied."""

    source_id: str
    target_id: str
    modifier_id: str
    stat: str
    value: int
    duration: int


@dataclass(frozen=True)
class ModifierExpired(EncounterEvent):
    """Emitted when a temporary stat modifier expires."""

    combatant_id: str
    modifier_id: str


@dataclass(frozen=True)
class SavingThrowRolled(EncounterEvent):
    """Emitted when a saving throw is rolled against a spell effect."""

    target_id: str
    save_type: str
    target_number: int
    roll: int
    success: bool
    spell_name: str
    penalty: int = 0


@dataclass(frozen=True)
class ConditionExpired(EncounterEvent):
    """Emitted when a condition is removed from a combatant."""

    combatant_id: str
    condition_id: str
    reason: str  # "duration", "damage", "dispelled"


@dataclass(frozen=True)
class GroupTargetsResolved(EncounterEvent):
    """Emitted when a spell resolves its group/HD-pool targets."""

    spell_name: str
    pool_roll: int | None
    resolved_target_ids: tuple[str, ...]


@dataclass(frozen=True)
class TurnUndeadAttempted(EncounterEvent):
    """Emitted when a cleric attempts to turn undead."""

    actor_id: str
    roll: int
    target_number: int | None
    result: TurnResult


@dataclass(frozen=True)
class UndeadTurned(EncounterEvent):
    """Emitted for each undead affected by Turn Undead."""

    actor_id: str
    target_id: str
    destroyed: bool
    hd_spent: int


@dataclass(frozen=True)
class EncounterFaulted(EncounterEvent):
    """Emitted when the engine hits an unrecoverable error."""

    state: EncounterState
    error_type: str
    message: str

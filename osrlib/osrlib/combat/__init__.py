"""Combat subpackage — state-driven tactical combat engine for osrlib.

Import public types from here::

    from osrlib.combat import CombatEngine, EncounterState, EventFormatter
"""

from osrlib.combat.context import CombatContext, CombatSide, CombatantRef
from osrlib.combat.dice_service import BXDiceService, DiceService, FixedDiceService
from osrlib.combat.effects import (
    ApplyConditionEffect,
    ConsumeSlotEffect,
    DamageEffect,
    Effect,
)
from osrlib.combat.actions import ActionResult, CombatAction, MeleeAttackAction
from osrlib.combat.engine import CombatEngine, StepResult
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
from osrlib.combat.formatter import EventFormatter
from osrlib.combat.intents import ActionIntent, MeleeAttackIntent
from osrlib.combat.serializer import EventSerializer
from osrlib.combat.state import EncounterLoopError, EncounterOutcome, EncounterState

__all__ = [
    "ActionIntent",
    "ActionResult",
    "ActionRejected",
    "ApplyConditionEffect",
    "AttackRolled",
    "BXDiceService",
    "CombatAction",
    "CombatContext",
    "CombatEngine",
    "CombatSide",
    "CombatantRef",
    "ConditionApplied",
    "ConsumeSlotEffect",
    "DamageEffect",
    "DamageApplied",
    "DiceService",
    "Effect",
    "EncounterEvent",
    "EncounterFaulted",
    "EncounterLoopError",
    "EncounterOutcome",
    "EncounterStarted",
    "EncounterState",
    "EntityDied",
    "EventFormatter",
    "EventSerializer",
    "FixedDiceService",
    "InitiativeRolled",
    "MeleeAttackIntent",
    "NeedAction",
    "RoundStarted",
    "SpellSlotConsumed",
    "StepResult",
    "SurpriseRolled",
    "MeleeAttackAction",
    "TurnQueueBuilt",
    "TurnSkipped",
    "TurnStarted",
    "VictoryDetermined",
]

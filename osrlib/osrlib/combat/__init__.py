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
from osrlib.combat.actions import (
    ActionResult,
    CastSpellAction,
    CombatAction,
    MeleeAttackAction,
    RangedAttackAction,
)
from osrlib.combat.engine import CombatEngine, StepResult
from osrlib.combat.events import (
    ActionChoice,
    ActionRejected,
    AttackRolled,
    ConditionApplied,
    DamageApplied,
    EncounterEvent,
    EncounterFaulted,
    EncounterStarted,
    EntityDied,
    ForcedIntentApplied,
    ForcedIntentQueued,
    InitiativeRolled,
    NeedAction,
    RoundStarted,
    Rejection,
    RejectionCode,
    SpellCast,
    SpellSlotConsumed,
    SurpriseRolled,
    TurnQueueBuilt,
    TurnSkipped,
    TurnStarted,
    VictoryDetermined,
)
from osrlib.combat.formatter import EventFormatter
from osrlib.combat.intents import (
    ActionIntent,
    CastSpellIntent,
    MeleeAttackIntent,
    RangedAttackIntent,
)
from osrlib.combat.serializer import EventSerializer
from osrlib.combat.spells import SpellDefinition, get_spell
from osrlib.combat.tactical_providers import RandomMonsterProvider, TacticalProvider
from osrlib.combat.views import CombatView, CombatantView
from osrlib.combat.state import EncounterLoopError, EncounterOutcome, EncounterState

__all__ = [
    "ActionIntent",
    "ActionChoice",
    "ActionResult",
    "ActionRejected",
    "ApplyConditionEffect",
    "AttackRolled",
    "BXDiceService",
    "CastSpellAction",
    "CastSpellIntent",
    "CombatAction",
    "CombatContext",
    "CombatEngine",
    "CombatSide",
    "CombatView",
    "CombatantRef",
    "CombatantView",
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
    "ForcedIntentApplied",
    "ForcedIntentQueued",
    "EventFormatter",
    "EventSerializer",
    "FixedDiceService",
    "InitiativeRolled",
    "MeleeAttackIntent",
    "NeedAction",
    "RangedAttackAction",
    "RangedAttackIntent",
    "RoundStarted",
    "Rejection",
    "RejectionCode",
    "SpellCast",
    "SpellDefinition",
    "SpellSlotConsumed",
    "StepResult",
    "SurpriseRolled",
    "MeleeAttackAction",
    "RandomMonsterProvider",
    "TacticalProvider",
    "TurnQueueBuilt",
    "TurnSkipped",
    "TurnStarted",
    "VictoryDetermined",
    "get_spell",
]

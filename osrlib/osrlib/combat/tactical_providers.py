"""Tactical decision providers for engine-side combatant AI."""

from typing import Protocol

from osrlib.combat.context import CombatContext
from osrlib.combat.dice_service import DiceService
from osrlib.combat.events import ActionChoice
from osrlib.combat.intents import ActionIntent


class TacticalProvider(Protocol):
    """Protocol for choosing an intent from available action choices."""

    def choose_intent(
        self,
        combatant_id: str,
        choices: tuple[ActionChoice, ...],
        ctx: CombatContext,
    ) -> ActionIntent: ...


class RandomMonsterProvider:
    """Picks a random available action choice using the engine's dice service."""

    def __init__(self, dice: DiceService) -> None:
        self._dice = dice

    def choose_intent(
        self,
        combatant_id: str,
        choices: tuple[ActionChoice, ...],
        ctx: CombatContext,
    ) -> ActionIntent:
        return self._dice.choice(choices).intent

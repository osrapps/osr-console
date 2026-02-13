"""State enum and exception types for the combat engine."""

from enum import Enum, auto


class EncounterState(Enum):
    """States of the combat state machine."""

    INIT = auto()
    ROUND_START = auto()
    TURN_START = auto()
    AWAIT_INTENT = auto()
    VALIDATE_INTENT = auto()
    EXECUTE_ACTION = auto()
    CHECK_DEATHS = auto()
    CHECK_MORALE = auto()
    CHECK_VICTORY = auto()
    ENDED = auto()


class EncounterOutcome(Enum):
    """Possible outcomes when combat ends."""

    PARTY_VICTORY = auto()
    OPPOSITION_VICTORY = auto()
    FAULTED = auto()


class EncounterLoopError(RuntimeError):
    """Raised when ``step_until_decision`` exhausts its ``max_steps`` budget."""

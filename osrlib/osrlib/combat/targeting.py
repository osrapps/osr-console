"""Targeting modes for spells and combat items."""

from enum import Enum, auto


class TargetMode(Enum):
    """How a spell or item selects its targets."""

    SINGLE_ENEMY = auto()  # existing num_targets=1
    ALL_ENEMIES = auto()  # existing num_targets=-1
    SELF = auto()  # caster only (Shield)
    SINGLE_ALLY = auto()  # pick one ally (Cure Light Wounds)
    ALL_ALLIES = auto()  # entire friendly side (Bless)
    ENEMY_GROUP = auto()  # up to N random enemies (Hold Person group)

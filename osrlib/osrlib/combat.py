from enum import Enum


class AttackType(Enum):
    MELEE = "Meelee"
    RANGED = "Ranged"
    DEATH_RAY_POISON = "Death ray or poison"
    MAGIC_WANDS = "Magic wands"
    PARALYSIS_TURN_TO_STONE = "Paralysis or turn to stone"
    DRAGON_BREATH = "Dragon breath"
    RODS_STAVES_SPELLS = "Rods, staves, or spells"


class ModifierType(Enum):
    TO_HIT = "To hit"
    DAMAGE = "Damage"
    OPEN_DOORS = "Open doors"
    LANGUAGES = "Languages"
    SAVING_THROWS = "Magic-based saving throws"
    AC = "AC"
    INITIATIVE = "Initiative"
    HP = "HP"
    REACTION = "Monster and NPC reactions"
    XP = "XP"

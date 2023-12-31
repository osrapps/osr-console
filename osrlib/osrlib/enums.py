from enum import Enum


class AbilityType(Enum):
    STRENGTH = "Strength"
    INTELLIGENCE = "Intelligence"
    WISDOM = "Wisdom"
    DEXTERITY = "Dexterity"
    CONSTITUTION = "Constitution"
    CHARISMA = "Charisma"


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


class CharacterClassType(Enum):
    CLERIC = "Cleric"
    DWARF = "Dwarf"
    ELF = "Elf"
    FIGHTER = "Fighter"
    HALFLING = "Halfling"
    MAGIC_USER = "Magic User"
    THIEF = "Thief"
    COMMONER = "Commoner"


class ItemType(Enum):
    ARMOR = ("Armor", "Armor, helmet, gloves, or boots")
    WEAPON = ("Weapon", "Bladed, blunt, or ranged weapon")
    SPELL = ("Spell", "Spell or scroll")
    EQUIPMENT = ("Equipment", "Piece of adventurers' equipment")
    MAGIC_ITEM = (
        "Magic item",
        "Potion, ring, or other item imbued with magical properties",
    )
    ITEM = ("Normal item", "Normal (non-magical) item")


class OpenAIModelVersion(Enum):
    DEFAULT = "gpt-3.5-turbo-1106"
    GPT35 = "gpt-3.5"
    GPT35TURBO = "gpt-3.5-turbo-1106"
    GPT4 = "gpt-4"
    GPT4TURBO = "gpt-4-1106-preview"


class PartyReaction(Enum):
    FIGHT = "Fight"
    RUN = "Run"
    TALK = "Talk"
    PASS = "Pass"


class TreasureType(Enum):
    NONE = "None"
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"
    G = "G"
    H = "H"
    I = "I"
    J = "J"
    K = "K"
    L = "L"
    M = "M"
    N = "N"
    O = "O"
    P = "P"
    Q = "Q"
    R = "R"
    S = "S"
    T = "T"
    U = "U"
    V = "V"
    W = "W"
    X = "X"
    Y = "Y"
    Z = "Z"

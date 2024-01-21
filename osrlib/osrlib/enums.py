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


class Direction(Enum):
    """Enumeration for directions a player can go within a location.

    Attributes:
        NORTH, SOUTH, EAST, WEST, UP, DOWN: Cardinal directions and vertical movements.
    """

    NORTH = "N"
    SOUTH = "S"
    EAST = "E"
    WEST = "W"
    UP = "U"
    DOWN = "D"


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
    GEMS_JEWELRY = ("Gems and jewelry", "Precious stones and fine jewelry.")


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


class CoinType(Enum):
    COPPER = ("copper", 0.01)
    SILVER = ("silver", 0.1)
    ELECTRUM = ("electrum", 0.5)
    GOLD = ("gold", 1)
    PLATINUM = ("platinum", 5)
    
    def __init__(self, description: str, exchange_rate: float):
        self.description = description
        self.exchange_rate = exchange_rate

    @staticmethod
    def value_in_gold(coin_amounts: dict) -> float:
        """
        Calculate the combined value in gold pieces based on the coin amounts.

        Args:
        coin_amounts (dict): A dictionary with CoinType as keys and amounts as values.

        Returns:
        float: The total value in gold pieces.

        Example usage:
        >>> CoinType.value_in_gold({CoinType.COPPER: 1000, CoinType.SILVER: 100})
        20.0
        """
        return sum(coin_type.exchange_rate * amount for coin_type, amount in coin_amounts.items())

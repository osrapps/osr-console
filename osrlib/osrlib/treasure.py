from osrlib.dice_roller import roll_dice
from osrlib.enums import ItemType, TreasureType
from osrlib.item import Item, Weapon, Armor

from enum import Enum


# Define enums for the types of treasure.
class CoinType(Enum):
    COPPER = "copper"
    SILVER = "silver"
    ELECTRUM = "electrum"
    GOLD = "gold"
    PLATINUM = "platinum"


class OtherType(Enum):
    GEMS_JEWELRY = "gems_jewelry"
    MAGIC_ITEMS = "magic_items"


# Example of a treasure type structure using the enums and dice notation.
treasure_types = [
    {
        TreasureType.A,
        {
            CoinType.COPPER: {"percent_chance": 25, "amount": "1d6"},
            CoinType.SILVER: {"percent_chance": 30, "amount": "1d6"},
            CoinType.ELECTRUM: {"percent_chance": 20, "amount": "1d4"},
            CoinType.GOLD: {"percent_chance": 35, "amount": "2d6"},
            CoinType.PLATINUM: {"percent_chance": 25, "amount": "1d2"},
            OtherType.GEMS_JEWELRY: {"percent_chance": 50, "amount": "6d6"},
            OtherType.MAGIC_ITEMS: {"percent_chance": 30, "description": "Any 3"},
        },
    },
    {
        TreasureType.B,
        {
            CoinType.COPPER: {"percent_chance": 50, "amount": "1d8"},
            CoinType.SILVER: {"percent_chance": 25, "amount": "1d6"},
            CoinType.ELECTRUM: {"percent_chance": 25, "amount": "1d4"},
            CoinType.GOLD: {"percent_chance": 25, "amount": "1d3"},
            OtherType.GEMS_JEWELRY: {"percent_chance": 25, "amount": "1d6"},
            OtherType.MAGIC_ITEMS: {
                "percent_chance": 10,
                "description": "1 sword, armor, or weapon",
            },
        },
    },
    {
        TreasureType.C,
        {
            CoinType.COPPER: {"percent_chance": 20, "amount": "1d12"},
            CoinType.SILVER: {"percent_chance": 30, "amount": "1d4"},
            CoinType.ELECTRUM: {"percent_chance": 10, "amount": "1d4"},
            OtherType.GEMS_JEWELRY: {"percent_chance": 25, "amount": "1d4"},
            OtherType.MAGIC_ITEMS: {"percent_chance": 10, "description": "Any 2"},
        },
    },
    {
        TreasureType.D,
        {
            CoinType.COPPER: {"percent_chance": 10, "amount": "1d8"},
            CoinType.SILVER: {"percent_chance": 15, "amount": "1d12"},
            CoinType.GOLD: {"percent_chance": 60, "amount": "1d6"},
            OtherType.GEMS_JEWELRY: {"percent_chance": 30, "amount": "1d8"},
            OtherType.MAGIC_ITEMS: {
                "percent_chance": 15,
                "description": "Any 2 + 1 potion",
            },
        },
    },
    {
        TreasureType.E,
        {
            CoinType.COPPER: {"percent_chance": 5, "amount": "1d10"},
            CoinType.SILVER: {"percent_chance": 30, "amount": "1d12"},
            CoinType.ELECTRUM: {"percent_chance": 25, "amount": "1d4"},
            CoinType.GOLD: {"percent_chance": 25, "amount": "1d8"},
            OtherType.GEMS_JEWELRY: {"percent_chance": 10, "amount": "1d10"},
            OtherType.MAGIC_ITEMS: {
                "percent_chance": 25,
                "description": "Any 3 + 1 scroll",
            },
        },
    },
    {
        TreasureType.F,
        {
            CoinType.SILVER: {"percent_chance": 10, "amount": "2d10"},
            CoinType.ELECTRUM: {"percent_chance": 20, "amount": "1d8"},
            CoinType.GOLD: {"percent_chance": 45, "amount": "1d12"},
            CoinType.PLATINUM: {"percent_chance": 30, "amount": "1d3"},
            OtherType.GEMS_JEWELRY: {"percent_chance": 20, "amount": "2d12"},
            OtherType.MAGIC_ITEMS: {
                "percent_chance": 30,
                "description": "Any 3 except weapons, + 1 potion, + 1 scroll",
            },
        },
    },
    {
        TreasureType.G,
        {
            CoinType.GOLD: {"percent_chance": 50, "amount": "10d4"},
            CoinType.PLATINUM: {"percent_chance": 50, "amount": "1d6"},
            OtherType.GEMS_JEWELRY: {"percent_chance": 25, "amount": "3d6"},
            OtherType.MAGIC_ITEMS: {
                "percent_chance": 35,
                "description": "Any 4 + 1 scroll",
            },
        },
    },
    {
        TreasureType.H,
        {
            CoinType.COPPER: {"percent_chance": 25, "amount": "3d6"},
            CoinType.SILVER: {"percent_chance": 50, "amount": "1d100"},
            CoinType.ELECTRUM: {"percent_chance": 50, "amount": "1d6"},
            CoinType.GOLD: {"percent_chance": 50, "amount": "1d20"},
            CoinType.PLATINUM: {"percent_chance": 25, "amount": "1d10"},
            OtherType.GEMS_JEWELRY: {"percent_chance": 50, "amount": "1d100"},
            OtherType.MAGIC_ITEMS: {
                "percent_chance": 15,
                "description": "Any 4 + 1 potion + 1 scroll",
            },
        },
    },
    {
        TreasureType.I,
        {
            CoinType.COPPER: {"percent_chance": 0, "amount": "0"},
            CoinType.SILVER: {"percent_chance": 0, "amount": "0"},
            CoinType.ELECTRUM: {"percent_chance": 0, "amount": "0"},
            CoinType.GOLD: {"percent_chance": 30, "amount": "1d8"},
            CoinType.PLATINUM: {"percent_chance": 0, "amount": "0"},
            OtherType.GEMS_JEWELRY: {"percent_chance": 50, "amount": "2d12"},
            OtherType.MAGIC_ITEMS: {"percent_chance": 15, "description": "Any 1"},
        },
    },
    {
        TreasureType.J,
        {
            CoinType.COPPER: {"percent_chance": 25, "amount": "1d4"},
            CoinType.SILVER: {"percent_chance": 10, "amount": "1d3"},
            CoinType.ELECTRUM: {"percent_chance": 0, "amount": "0"},
            CoinType.GOLD: {"percent_chance": 0, "amount": "0"},
            CoinType.PLATINUM: {"percent_chance": 0, "amount": "0"},
            OtherType.GEMS_JEWELRY: {"percent_chance": 0, "amount": "0"},
            OtherType.MAGIC_ITEMS: {"percent_chance": 0, "description": ""},
        },
    },
    {
        TreasureType.K,
        {
            CoinType.COPPER: {"percent_chance": 50, "amount": "2d8"},
            CoinType.SILVER: {"percent_chance": 25, "amount": "1d12"},
            CoinType.ELECTRUM: {"percent_chance": 0, "amount": "0"},
            CoinType.GOLD: {"percent_chance": 50, "amount": "1d6"},
            CoinType.PLATINUM: {"percent_chance": 0, "amount": "0"},
            OtherType.GEMS_JEWELRY: {"percent_chance": 15, "amount": "1d4"},
            OtherType.MAGIC_ITEMS: {"percent_chance": 0, "description": ""},
        },
    },
    {
        TreasureType.L,
        {
            CoinType.COPPER: {"percent_chance": 0, "amount": "0"},
            CoinType.SILVER: {"percent_chance": 0, "amount": "0"},
            CoinType.ELECTRUM: {"percent_chance": 0, "amount": "0"},
            CoinType.GOLD: {"percent_chance": 100, "amount": "1d100"},
            CoinType.PLATINUM: {"percent_chance": 0, "amount": "0"},
            OtherType.GEMS_JEWELRY: {"percent_chance": 50, "amount": "1d6"},
            OtherType.MAGIC_ITEMS: {
                "percent_chance": 30,
                "description": "Any 1 + 1 potion",
            },
        },
    },
    {
        TreasureType.M,
        {
            CoinType.COPPER: {"percent_chance": 0, "amount": "0"},
            CoinType.SILVER: {"percent_chance": 0, "amount": "0"},
            CoinType.ELECTRUM: {"percent_chance": 0, "amount": "0"},
            CoinType.GOLD: {"percent_chance": 40, "amount": "2d8"},
            CoinType.PLATINUM: {"percent_chance": 50, "amount": "5d30"},
            OtherType.GEMS_JEWELRY: {"percent_chance": 55, "amount": "5d20"},
            OtherType.MAGIC_ITEMS: {"percent_chance": 0, "description": ""},
        },
    },
    {
        TreasureType.N,
        {
            CoinType.COPPER: {"percent_chance": 0, "amount": "0"},
            CoinType.SILVER: {"percent_chance": 0, "amount": "0"},
            CoinType.ELECTRUM: {"percent_chance": 0, "amount": "0"},
            CoinType.GOLD: {"percent_chance": 0, "amount": "0"},
            CoinType.PLATINUM: {"percent_chance": 0, "amount": "0"},
            OtherType.GEMS_JEWELRY: {"percent_chance": 45, "amount": "2d12"},
            OtherType.MAGIC_ITEMS: {"percent_chance": 40, "description": "2d8 potions"},
        },
    },
    {
        TreasureType.O,
        {
            CoinType.COPPER: {"percent_chance": 0, "amount": "0"},
            CoinType.SILVER: {"percent_chance": 0, "amount": "0"},
            CoinType.ELECTRUM: {"percent_chance": 0, "amount": "0"},
            CoinType.GOLD: {"percent_chance": 0, "amount": "0"},
            CoinType.PLATINUM: {"percent_chance": 0, "amount": "0"},
            OtherType.GEMS_JEWELRY: {"percent_chance": 50, "amount": "1d4 scrolls"},
            OtherType.MAGIC_ITEMS: {"percent_chance": 0, "description": ""},
        },
    },
    {
        TreasureType.P,
        {
            CoinType.COPPER: {"percent_chance": 100, "amount": "4d6"},
            CoinType.SILVER: {"percent_chance": 0, "amount": "0"},
            CoinType.ELECTRUM: {"percent_chance": 0, "amount": "0"},
            CoinType.GOLD: {"percent_chance": 0, "amount": "0"},
            CoinType.PLATINUM: {"percent_chance": 0, "amount": "0"},
            OtherType.GEMS_JEWELRY: {"percent_chance": 0, "amount": "0"},
            OtherType.MAGIC_ITEMS: {"percent_chance": 0, "description": ""},
        },
    },
    {
        TreasureType.Q,
        {
            CoinType.COPPER: {"percent_chance": 0, "amount": "0"},
            CoinType.SILVER: {"percent_chance": 100, "amount": "3d6"},
            CoinType.ELECTRUM: {"percent_chance": 0, "amount": "0"},
            CoinType.GOLD: {"percent_chance": 0, "amount": "0"},
            CoinType.PLATINUM: {"percent_chance": 0, "amount": "0"},
            OtherType.GEMS_JEWELRY: {"percent_chance": 0, "amount": "0"},
            OtherType.MAGIC_ITEMS: {"percent_chance": 0, "description": ""},
        },
    },
    {
        TreasureType.R,
        {
            CoinType.COPPER: {"percent_chance": 0, "amount": "0"},
            CoinType.SILVER: {"percent_chance": 0, "amount": "0"},
            CoinType.ELECTRUM: {"percent_chance": 100, "amount": "2d6"},
            CoinType.GOLD: {"percent_chance": 0, "amount": "0"},
            CoinType.PLATINUM: {"percent_chance": 0, "amount": "0"},
            OtherType.GEMS_JEWELRY: {"percent_chance": 0, "amount": "0"},
            OtherType.MAGIC_ITEMS: {"percent_chance": 0, "description": ""},
        },
    },
    {
        TreasureType.S,
        {
            CoinType.COPPER: {"percent_chance": 0, "amount": "0"},
            CoinType.SILVER: {"percent_chance": 0, "amount": "0"},
            CoinType.ELECTRUM: {"percent_chance": 0, "amount": "0"},
            CoinType.GOLD: {"percent_chance": 100, "amount": "2d4"},
            CoinType.PLATINUM: {"percent_chance": 0, "amount": "0"},
            OtherType.GEMS_JEWELRY: {"percent_chance": 0, "amount": "0"},
            OtherType.MAGIC_ITEMS: {"percent_chance": 0, "description": ""},
        },
    },
    {
        TreasureType.T,
        {
            CoinType.COPPER: {"percent_chance": 0, "amount": "0"},
            CoinType.SILVER: {"percent_chance": 0, "amount": "0"},
            CoinType.ELECTRUM: {"percent_chance": 0, "amount": "0"},
            CoinType.GOLD: {"percent_chance": 0, "amount": "0"},
            CoinType.PLATINUM: {"percent_chance": 100, "amount": "1d6"},
            OtherType.GEMS_JEWELRY: {"percent_chance": 0, "amount": "0"},
            OtherType.MAGIC_ITEMS: {"percent_chance": 0, "description": ""},
        },
    },
    {
        TreasureType.U,
        {
            CoinType.COPPER: {"percent_chance": 10, "amount": "1d100"},
            CoinType.SILVER: {"percent_chance": 10, "amount": "1d100"},
            CoinType.ELECTRUM: {"percent_chance": 0, "amount": "0"},
            CoinType.GOLD: {"percent_chance": 5, "amount": "1d100"},
            CoinType.PLATINUM: {"percent_chance": 100, "amount": "0"},
            OtherType.GEMS_JEWELRY: {"percent_chance": 5, "amount": "1d4"},
            OtherType.MAGIC_ITEMS: {"percent_chance": 2, "description": "Any 1"},
        },
    },
    {
        TreasureType.V,
        {
            CoinType.COPPER: {"percent_chance": 0, "amount": "0"},
            CoinType.SILVER: {"percent_chance": 10, "amount": "1d100"},
            CoinType.ELECTRUM: {"percent_chance": 5, "amount": "1d100"},
            CoinType.GOLD: {"percent_chance": 10, "amount": "1d100"},
            CoinType.PLATINUM: {"percent_chance": 5, "amount": "1d100"},
            OtherType.GEMS_JEWELRY: {"percent_chance": 10, "amount": "1d4"},
            OtherType.MAGIC_ITEMS: {"percent_chance": 5, "description": "Any 1"},
        },
    },
]


def get_treasure(treasure_type: TreasureType):
    """Get a collection of items appropriate for the specified treasure type.

    Typical use of this method is to pass it the treasure_type attribute value of a MonsterStatBlock instance
    when determining the treasure to award the party for defeating a monster.

    Args:
        treasure_type (TreasureType): The type of treasure to get.

    Returns:
        list: A list of the items to be awarded as treasure to the party.
    """
    treasure_items = []
    if treasure_type == TreasureType.NONE:
        return None
    elif treasure_type == TreasureType.A:
        pass
    elif treasure_type == TreasureType.B:
        pass
    elif treasure_type == TreasureType.C:
        pass
    elif treasure_type == TreasureType.D:
        pass
    elif treasure_type == TreasureType.E:
        pass
    elif treasure_type == TreasureType.F:
        pass
    elif treasure_type == TreasureType.G:
        pass
    elif treasure_type == TreasureType.H:
        pass
    elif treasure_type == TreasureType.I:
        pass
    elif treasure_type == TreasureType.J:
        pass
    elif treasure_type == TreasureType.K:
        pass
    elif treasure_type == TreasureType.L:
        pass
    elif treasure_type == TreasureType.M:
        pass
    elif treasure_type == TreasureType.N:
        pass
    elif treasure_type == TreasureType.O:
        pass
    elif treasure_type == TreasureType.P:
        pass
    elif treasure_type == TreasureType.Q:
        pass
    elif treasure_type == TreasureType.R:
        pass
    elif treasure_type == TreasureType.S:
        pass
    elif treasure_type == TreasureType.T:
        pass
    elif treasure_type == TreasureType.U:
        pass
    elif treasure_type == TreasureType.V:
        pass
    elif treasure_type == TreasureType.W:
        pass
    elif treasure_type == TreasureType.X:
        pass
    elif treasure_type == TreasureType.Y:
        pass
    elif treasure_type == TreasureType.Z:
        pass

    return treasure_items

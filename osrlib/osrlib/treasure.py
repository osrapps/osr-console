from typing import Dict, NamedTuple, Union
from osrlib.dice_roller import roll_dice
from osrlib.enums import ItemType, TreasureType
from osrlib.item import Item, Weapon, Armor

from enum import Enum


class CoinType(Enum):
    COPPER = "copper"
    SILVER = "silver"
    ELECTRUM = "electrum"
    GOLD = "gold"
    PLATINUM = "platinum"


class OtherType(Enum):
    GEMS_JEWELRY = "gems_jewelry"
    MAGIC_ITEMS = "magic_items"

class Treasure(NamedTuple):
    coins: Dict[CoinType, int]
    other: Dict[OtherType, Union[str, int]]

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
            CoinType.COPPER: {"percent_chance": 25, "amount": "3d8"},
            CoinType.SILVER: {"percent_chance": 50, "amount": "1d100"},
            CoinType.ELECTRUM: {"percent_chance": 50, "amount": "10d4"},
            CoinType.GOLD: {"percent_chance": 50, "amount": "10d6"},
            CoinType.PLATINUM: {"percent_chance": 25, "amount": "5d4"},
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
            CoinType.GOLD: {"percent_chance": 0, "amount": "0"},
            CoinType.PLATINUM: {"percent_chance": 30, "amount": "1d8"},
            OtherType.GEMS_JEWELRY: {"percent_chance": 50, "amount": "2d6"},
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
            CoinType.COPPER: {"percent_chance": 0, "amount": "0"},
            CoinType.SILVER: {"percent_chance": 30, "amount": "1d6"},
            CoinType.ELECTRUM: {"percent_chance": 10, "amount": "1d2"},
            CoinType.GOLD: {"percent_chance": 0, "amount": "0"},
            CoinType.PLATINUM: {"percent_chance": 0, "amount": "0"},
            OtherType.GEMS_JEWELRY: {"percent_chance": 0, "amount": "0"},
            OtherType.MAGIC_ITEMS: {"percent_chance": 0, "description": "0"},
        },
    },
    {
        TreasureType.L, # TODO: Resume from here.
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


def get_treasure(treasure_type: TreasureType) -> Treasure:
    """
    Calculates the treasure based on the defined treasure types and computes the total value in gold pieces.

    Args:
        treasure_type (TreasureType): The type of treasure to calculate.

    Returns:
        Treasure: A named tuple containing the coins and other treasure items.
    """
    treasure_details = treasure_types[treasure_type]
    treasure_haul = {
        "coins": {},
        "other": {}
    }
    total_gp_value = 0  # Initialize the total gold pieces value

    for item_type, details in treasure_details.items():
        # Use roll_dice for chance determination
        chance_roll = roll_dice('1d100').total
        if chance_roll <= details["percent_chance"]:
            # Roll dice to determine the amount
            amount_roll = roll_dice(details["amount"])
            amount = amount_roll.total
            if isinstance(item_type, CoinType):
                treasure_haul["coins"][item_type] = amount
                # Update the total value in gold pieces
                total_gp_value += amount * item_type.exchange_rate
            else:
                treasure_haul["other"][item_type] = details.get("description", amount)

    # Add the total_gp_value to the treasure haul
    treasure_haul["total_gp_value"] = total_gp_value

    return Treasure(**treasure_haul)

# Example usage:
treasure = get_treasure(TreasureType.A)
print(f"Treasure haul: {treasure}")
# Calculate XP from the total gold pieces value
xp_from_treasure = treasure.total_gp_value
print(f"XP from treasure: {xp_from_treasure}")

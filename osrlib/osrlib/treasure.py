from typing import Dict, NamedTuple, Union
from dataclasses import dataclass
from osrlib.dice_roller import roll_dice
from osrlib.enums import ItemType, TreasureType, CoinType
from osrlib.item import Item, Weapon, Armor

from enum import Enum


@dataclass
class TreasureDetail:
    chance: float  # Probability as a float between 0 and 1
    amount: str  # Dice notation for the amount
    magical: bool = False  # Whether the item should be magical


class Treasure(NamedTuple):
    coins: Dict[CoinType, int]
    other: Dict[ItemType, Union[str, int]]
    total_gp_value: int


TreasureContent = Dict[Union[CoinType, ItemType], TreasureDetail]


treasure_types: Dict[TreasureType, TreasureContent] = {
    TreasureType.A: {
        CoinType.COPPER: TreasureDetail(chance=25, amount="1d6"),
        CoinType.SILVER: TreasureDetail(chance=30, amount="1d6"),
        CoinType.ELECTRUM: TreasureDetail(chance=20, amount="1d4"),
        CoinType.GOLD: TreasureDetail(chance=35, amount="2d6"),
        CoinType.PLATINUM: TreasureDetail(chance=25, amount="1d2"),
        ItemType.GEMS_JEWELRY: TreasureDetail(chance=50, amount="6d6"),
        ItemType.MAGIC_ITEM: TreasureDetail(chance=30, amount="3", magical=True),
    },
    TreasureType.B: {
        CoinType.COPPER: TreasureDetail(chance=50, amount="1d8"),
        CoinType.SILVER: TreasureDetail(chance=25, amount="1d6"),
        CoinType.ELECTRUM: TreasureDetail(chance=25, amount="1d4"),
        CoinType.GOLD: TreasureDetail(chance=25, amount="1d3"),
        ItemType.GEMS_JEWELRY: TreasureDetail(chance=25, amount="1d6"),
        ItemType.MAGIC_ITEM: TreasureDetail(chance=10, amount="1", magical=True),
    },
    TreasureType.C: {
        CoinType.COPPER: TreasureDetail(chance=20, amount="1d12"),
        CoinType.SILVER: TreasureDetail(chance=30, amount="1d4"),
        CoinType.ELECTRUM: TreasureDetail(chance=10, amount="1d4"),
        ItemType.GEMS_JEWELRY: TreasureDetail(chance=25, amount="1d4"),
        ItemType.MAGIC_ITEM: TreasureDetail(chance=10, amount="2", magical=True),
    },
    TreasureType.D: {
        CoinType.COPPER: TreasureDetail(chance=10, amount="1d8"),
        CoinType.SILVER: TreasureDetail(chance=15, amount="1d12"),
        CoinType.GOLD: TreasureDetail(chance=60, amount="1d6"),
        ItemType.GEMS_JEWELRY: TreasureDetail(chance=30, amount="1d8"),
        ItemType.MAGIC_ITEM: TreasureDetail(chance=15, amount="2+1", magical=True),
    },
    TreasureType.E: {
        CoinType.COPPER: TreasureDetail(chance=5, amount="1d10"),
        CoinType.SILVER: TreasureDetail(chance=30, amount="1d12"),
        CoinType.ELECTRUM: TreasureDetail(chance=25, amount="1d4"),
        CoinType.GOLD: TreasureDetail(chance=25, amount="1d8"),
        ItemType.GEMS_JEWELRY: TreasureDetail(chance=10, amount="1d10"),
        ItemType.MAGIC_ITEM: TreasureDetail(chance=25, amount="3+1", magical=True),
    },
    TreasureType.F: {
        CoinType.SILVER: TreasureDetail(chance=10, amount="2d10"),
        CoinType.ELECTRUM: TreasureDetail(chance=20, amount="1d8"),
        CoinType.GOLD: TreasureDetail(chance=45, amount="1d12"),
        CoinType.PLATINUM: TreasureDetail(chance=30, amount="1d3"),
        ItemType.GEMS_JEWELRY: TreasureDetail(chance=20, amount="2d12"),
        ItemType.MAGIC_ITEM: TreasureDetail(
            chance=30,
            amount="Any 3 except weapons, + 1 potion, + 1 scroll",
        ),
    },
    TreasureType.G: {
        CoinType.GOLD: TreasureDetail(chance=50, amount="10d4"),
        CoinType.PLATINUM: TreasureDetail(chance=50, amount="1d6"),
        ItemType.GEMS_JEWELRY: TreasureDetail(chance=25, amount="3d6"),
        ItemType.MAGIC_ITEM: TreasureDetail(
            chance=35,
            amount="Any 4 + 1 scroll",
        ),
    },
    TreasureType.H: {
        CoinType.COPPER: TreasureDetail(chance=25, amount="3d8"),
        CoinType.SILVER: TreasureDetail(chance=50, amount="1d100"),
        CoinType.ELECTRUM: TreasureDetail(chance=50, amount="10d4"),
        CoinType.GOLD: TreasureDetail(chance=50, amount="10d6"),
        CoinType.PLATINUM: TreasureDetail(chance=25, amount="5d4"),
        ItemType.GEMS_JEWELRY: TreasureDetail(chance=50, amount="1d100"),
        ItemType.MAGIC_ITEM: TreasureDetail(
            chance=15,
            amount="Any 4 + 1 potion + 1 scroll",
        ),
    },
    TreasureType.I: {
        CoinType.COPPER: TreasureDetail(chance=0, amount="0"),
        CoinType.SILVER: TreasureDetail(chance=0, amount="0"),
        CoinType.ELECTRUM: TreasureDetail(chance=0, amount="0"),
        CoinType.GOLD: TreasureDetail(chance=0, amount="0"),
        CoinType.PLATINUM: TreasureDetail(chance=30, amount="1d8"),
        ItemType.GEMS_JEWELRY: TreasureDetail(chance=50, amount="2d6"),
        ItemType.MAGIC_ITEM: TreasureDetail(chance=15, amount="Any 1"),
    },
    TreasureType.J: {
        CoinType.COPPER: TreasureDetail(chance=25, amount="1d4"),
        CoinType.SILVER: TreasureDetail(chance=10, amount="1d3"),
        CoinType.ELECTRUM: TreasureDetail(chance=0, amount="0"),
        CoinType.GOLD: TreasureDetail(chance=0, amount="0"),
        CoinType.PLATINUM: TreasureDetail(chance=0, amount="0"),
        ItemType.GEMS_JEWELRY: TreasureDetail(chance=0, amount="0"),
        ItemType.MAGIC_ITEM: TreasureDetail(chance=0, amount=""),
    },
    TreasureType.K: {
        CoinType.COPPER: TreasureDetail(chance=0, amount="0"),
        CoinType.SILVER: TreasureDetail(chance=30, amount="1d6"),
        CoinType.ELECTRUM: TreasureDetail(chance=10, amount="1d2"),
        CoinType.GOLD: TreasureDetail(chance=0, amount="0"),
        CoinType.PLATINUM: TreasureDetail(chance=0, amount="0"),
        ItemType.GEMS_JEWELRY: TreasureDetail(chance=0, amount="0"),
        ItemType.MAGIC_ITEM: TreasureDetail(chance=0, amount="0"),
    },
    TreasureType.L: {
        CoinType.COPPER: TreasureDetail(chance=0, amount="0"),
        CoinType.SILVER: TreasureDetail(chance=0, amount="0"),
        CoinType.ELECTRUM: TreasureDetail(chance=0, amount="0"),
        CoinType.GOLD: TreasureDetail(chance=100, amount="1d100"),
        CoinType.PLATINUM: TreasureDetail(chance=0, amount="0"),
        ItemType.GEMS_JEWELRY: TreasureDetail(chance=50, amount="1d6"),
        ItemType.MAGIC_ITEM: TreasureDetail(
            chance=30,
            amount="Any 1 + 1 potion",
        ),
    },
    TreasureType.M: {
        CoinType.COPPER: TreasureDetail(chance=0, amount="0"),
        CoinType.SILVER: TreasureDetail(chance=0, amount="0"),
        CoinType.ELECTRUM: TreasureDetail(chance=0, amount="0"),
        CoinType.GOLD: TreasureDetail(chance=40, amount="2d8"),
        CoinType.PLATINUM: TreasureDetail(chance=50, amount="5d30"),
        ItemType.GEMS_JEWELRY: TreasureDetail(chance=55, amount="5d20"),
        ItemType.MAGIC_ITEM: TreasureDetail(chance=0, amount=""),
    },
    TreasureType.N: {
        CoinType.COPPER: TreasureDetail(chance=0, amount="0"),
        CoinType.SILVER: TreasureDetail(chance=0, amount="0"),
        CoinType.ELECTRUM: TreasureDetail(chance=0, amount="0"),
        CoinType.GOLD: TreasureDetail(chance=0, amount="0"),
        CoinType.PLATINUM: TreasureDetail(chance=0, amount="0"),
        ItemType.GEMS_JEWELRY: TreasureDetail(chance=45, amount="2d12"),
        ItemType.MAGIC_ITEM: TreasureDetail(chance=40, amount="2d8 potions"),
    },
    TreasureType.O: {
        CoinType.COPPER: TreasureDetail(chance=0, amount="0"),
        CoinType.SILVER: TreasureDetail(chance=0, amount="0"),
        CoinType.ELECTRUM: TreasureDetail(chance=0, amount="0"),
        CoinType.GOLD: TreasureDetail(chance=0, amount="0"),
        CoinType.PLATINUM: TreasureDetail(chance=0, amount="0"),
        ItemType.GEMS_JEWELRY: TreasureDetail(chance=50, amount="1d4 scrolls"),
        ItemType.MAGIC_ITEM: TreasureDetail(chance=0, amount=""),
    },
    TreasureType.P: {
        CoinType.COPPER: TreasureDetail(chance=100, amount="4d6"),
        CoinType.SILVER: TreasureDetail(chance=0, amount="0"),
        CoinType.ELECTRUM: TreasureDetail(chance=0, amount="0"),
        CoinType.GOLD: TreasureDetail(chance=0, amount="0"),
        CoinType.PLATINUM: TreasureDetail(chance=0, amount="0"),
        ItemType.GEMS_JEWELRY: TreasureDetail(chance=0, amount="0"),
        ItemType.MAGIC_ITEM: TreasureDetail(chance=0, amount=""),
    },
    TreasureType.Q: {
        CoinType.COPPER: TreasureDetail(chance=0, amount="0"),
        CoinType.SILVER: TreasureDetail(chance=100, amount="3d6"),
        CoinType.ELECTRUM: TreasureDetail(chance=0, amount="0"),
        CoinType.GOLD: TreasureDetail(chance=0, amount="0"),
        CoinType.PLATINUM: TreasureDetail(chance=0, amount="0"),
        ItemType.GEMS_JEWELRY: TreasureDetail(chance=0, amount="0"),
        ItemType.MAGIC_ITEM: TreasureDetail(chance=0, amount=""),
    },
    TreasureType.R: {
        CoinType.COPPER: TreasureDetail(chance=0, amount="0"),
        CoinType.SILVER: TreasureDetail(chance=0, amount="0"),
        CoinType.ELECTRUM: TreasureDetail(chance=100, amount="2d6"),
        CoinType.GOLD: TreasureDetail(chance=0, amount="0"),
        CoinType.PLATINUM: TreasureDetail(chance=0, amount="0"),
        ItemType.GEMS_JEWELRY: TreasureDetail(chance=0, amount="0"),
        ItemType.MAGIC_ITEM: TreasureDetail(chance=0, amount=""),
    },
    TreasureType.S: {
        CoinType.COPPER: TreasureDetail(chance=0, amount="0"),
        CoinType.SILVER: TreasureDetail(chance=0, amount="0"),
        CoinType.ELECTRUM: TreasureDetail(chance=0, amount="0"),
        CoinType.GOLD: TreasureDetail(chance=100, amount="2d4"),
        CoinType.PLATINUM: TreasureDetail(chance=0, amount="0"),
        ItemType.GEMS_JEWELRY: TreasureDetail(chance=0, amount="0"),
        ItemType.MAGIC_ITEM: TreasureDetail(chance=0, amount=""),
    },
    TreasureType.T: {
        CoinType.COPPER: TreasureDetail(chance=0, amount="0"),
        CoinType.SILVER: TreasureDetail(chance=0, amount="0"),
        CoinType.ELECTRUM: TreasureDetail(chance=0, amount="0"),
        CoinType.GOLD: TreasureDetail(chance=0, amount="0"),
        CoinType.PLATINUM: TreasureDetail(chance=100, amount="1d6"),
        ItemType.GEMS_JEWELRY: TreasureDetail(chance=0, amount="0"),
        ItemType.MAGIC_ITEM: TreasureDetail(chance=0, amount=""),
    },
    TreasureType.U: {
        CoinType.COPPER: TreasureDetail(chance=10, amount="1d100"),
        CoinType.SILVER: TreasureDetail(chance=10, amount="1d100"),
        CoinType.ELECTRUM: TreasureDetail(chance=0, amount="0"),
        CoinType.GOLD: TreasureDetail(chance=5, amount="1d100"),
        CoinType.PLATINUM: TreasureDetail(chance=100, amount="0"),
        ItemType.GEMS_JEWELRY: TreasureDetail(chance=5, amount="1d4"),
        ItemType.MAGIC_ITEM: TreasureDetail(chance=200, amount="Any 1"),
    },
    TreasureType.V: {
        CoinType.COPPER: TreasureDetail(chance=0, amount="0"),
        CoinType.SILVER: TreasureDetail(chance=10, amount="1d100"),
        CoinType.ELECTRUM: TreasureDetail(chance=5, amount="1d100"),
        CoinType.GOLD: TreasureDetail(chance=10, amount="1d100"),
        CoinType.PLATINUM: TreasureDetail(chance=5, amount="1d100"),
        ItemType.GEMS_JEWELRY: TreasureDetail(chance=10, amount="1d4"),
        ItemType.MAGIC_ITEM: TreasureDetail(chance=5, amount="Any 1"),
    },
}


def get_treasure(treasure_type: TreasureType) -> Treasure:
    """Calculates the treasure based on the defined treasure types and computes the total value in gold pieces.

    Args:
        treasure_type (TreasureType): The type of treasure to calculate.

    Returns:
        Treasure: A named tuple containing the coins and other treasure items.
    """
    treasure_details = treasure_types[treasure_type]
    treasure_haul = {"coins": {}, "other": {}, "total_gp_value": {}}
    total_gp_value = 0  # Initialize the total gold pieces value

    for item_type, details in treasure_details.items():
        chance_roll = roll_dice("1d100").total
        if chance_roll <= details.chance:
            # Roll dice to determine the amount
            amount_roll = roll_dice(details.amount)
            amount = amount_roll.total
            if isinstance(item_type, CoinType):
                treasure_haul["coins"][item_type] = amount
                # Update the total value in gold pieces
                total_gp_value += amount * item_type.exchange_rate
            else:
                treasure_haul["other"][item_type] = details.amount

    # Add the total_gp_value to the treasure haul
    treasure_haul["total_gp_value"] = total_gp_value

    return Treasure(**treasure_haul)


# Example usage:
treasure = get_treasure(TreasureType.A)
print(f"Treasure haul: {treasure}")
# Calculate XP from the total gold pieces value
xp_from_treasure = treasure.total_gp_value
print(f"XP from treasure: {xp_from_treasure}")

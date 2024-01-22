"""Implements the treasure generation system for a dungeon crawler RPG, inspired by the Dungeons & Dragons Basic Rules.

The system is built around the `Treasure` class, which encapsulates the logic for generating treasure hauls for the the
player's party. Central to `Treasure` class is the `_treasure_types` attribute, a detailed mapping of various treasure
categories to their respective contents. These categories represent different types of treasure the party might obtain,
each with specified probabilities and quantities of items like coins, gems, jewelry, and magical items.
"""
from typing import Dict, NamedTuple, Union
from dataclasses import dataclass
from osrlib.dice_roller import roll_dice
from osrlib.enums import ItemType, TreasureType, CoinType
from osrlib.item import Item, Weapon, Armor
from osrlib.game_manager import logger

from enum import Enum


@dataclass
class TreasureDetail:
    """Defines the characteristics of a particular "unit" of treasure (coins, gems, magic items, ...) in a treasure type.

    This class dictatd the attributes of each item type within a defined treasure type. It outlines the chance of
    occurrence, the amount (in dice notation or a fixed number), and whether the item is magical. This class is used
    by the `Treasure` class, but you can also use it to customize the contents of treasure hauls by creating your own
    treasure types.

    Attributes:
        chance (int): The probability (as a percentage) of this item appearing in the treasure.
        amount (str): The quantity of the item, expressed in dice notation (e.g., "1d6") or as a fixed number.
        magical (bool): True if the item is magical, False otherwise (defaults to False).

    Example:
        # Defining a custom treasure detail for a new treasure type
        custom_treasure_detail = TreasureDetail(chance=40, amount="3d4", magical=True)
        custom_treasure_type = {
            CoinType.GOLD: custom_treasure_detail,
            ItemType.MAGIC_ITEM: TreasureDetail(chance=25, amount="1", magical=True)
        }
        custom_treasure = Treasure.from_custom_type(custom_treasure_type)
        # This creates a Treasure instance with the custom-defined treasure type
    """
    chance: int  # Probability of appearing in the treasure haul
    amount: str  # Dice notation for the amount/number of coins/items
    magical: bool = False  # Whether the item should be magical


class Treasure:
    """Represents a treasure haul within the game, encapsulating various types of loot.

    ``Treasure`` manages the generation and valuation of treasures comprising coins, gems, jewelry, and magical items.
    The treasure is generated based on predefined types, each corresponding to different probabilities and amounts
    of items. The class provides functionalities to generate treasure based on a specified type, calculate its total
    value in gold pieces (gp), and retrieve the generated items.

    Attributes:
        items (Dict[Union[CoinType, ItemType], int]): A dictionary holding the treasure items. The keys are instances
            of either CoinType or ItemType enumerations, and the values are integers representing the quantity of each item.

    Methods:
        __init__(treasure_type: TreasureType = None): Initializes a new Treasure instance, optionally generating
            treasure contents based on the provided type.
        total_gp_value(): Property that calculates and returns the total value of the treasure in gold pieces.
        from_treasure_type(treasure_type: TreasureType): Class method to create a new Treasure instance with contents
            generated based on the specified TreasureType.

    Example:
        >>> treasure = Treasure.from_treasure_type(TreasureType.A)
        >>> treasure.items
        {<CoinType.GOLD: 3>: 12, <ItemType.GEMS_JEWELRY: 2>: 6}
        >>> treasure.total_gp_value
        12
    """
    items: Dict[Union[CoinType, ItemType], int]

    _treasure_types: Dict[
        TreasureType, Dict[Union[CoinType, ItemType], TreasureDetail]
    ] = {
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
            ItemType.MAGIC_ITEM: TreasureDetail(chance=15, amount="3", magical=True),
        },
        TreasureType.E: {
            CoinType.COPPER: TreasureDetail(chance=5, amount="1d10"),
            CoinType.SILVER: TreasureDetail(chance=30, amount="1d12"),
            CoinType.ELECTRUM: TreasureDetail(chance=25, amount="1d4"),
            CoinType.GOLD: TreasureDetail(chance=25, amount="1d8"),
            ItemType.GEMS_JEWELRY: TreasureDetail(chance=10, amount="1d10"),
            ItemType.MAGIC_ITEM: TreasureDetail(chance=25, amount="4", magical=True),
        },
        TreasureType.F: {
            CoinType.SILVER: TreasureDetail(chance=10, amount="2d10"),
            CoinType.ELECTRUM: TreasureDetail(chance=20, amount="1d8"),
            CoinType.GOLD: TreasureDetail(chance=45, amount="1d12"),
            CoinType.PLATINUM: TreasureDetail(chance=30, amount="1d3"),
            ItemType.GEMS_JEWELRY: TreasureDetail(chance=20, amount="2d12"),
            ItemType.MAGIC_ITEM: TreasureDetail(chance=30, amount="5", magical=True),
        },
        TreasureType.G: {
            CoinType.GOLD: TreasureDetail(chance=50, amount="10d4"),
            CoinType.PLATINUM: TreasureDetail(chance=50, amount="1d6"),
            ItemType.GEMS_JEWELRY: TreasureDetail(chance=25, amount="3d6"),
            ItemType.MAGIC_ITEM: TreasureDetail(chance=35, amount="5", magical=True),
        },
        TreasureType.H: {
            CoinType.COPPER: TreasureDetail(chance=25, amount="3d8"),
            CoinType.SILVER: TreasureDetail(chance=50, amount="1d100"),
            CoinType.ELECTRUM: TreasureDetail(chance=50, amount="10d4"),
            CoinType.GOLD: TreasureDetail(chance=50, amount="10d6"),
            CoinType.PLATINUM: TreasureDetail(chance=25, amount="5d4"),
            ItemType.GEMS_JEWELRY: TreasureDetail(chance=50, amount="1d100"),
            ItemType.MAGIC_ITEM: TreasureDetail(chance=15, amount="6", magical=True),
        },
        TreasureType.I: {
            CoinType.COPPER: TreasureDetail(chance=0, amount="0"),
            CoinType.SILVER: TreasureDetail(chance=0, amount="0"),
            CoinType.ELECTRUM: TreasureDetail(chance=0, amount="0"),
            CoinType.GOLD: TreasureDetail(chance=0, amount="0"),
            CoinType.PLATINUM: TreasureDetail(chance=30, amount="1d8"),
            ItemType.GEMS_JEWELRY: TreasureDetail(chance=50, amount="2d6"),
            ItemType.MAGIC_ITEM: TreasureDetail(chance=15, amount="1", magical=True),
        },
        TreasureType.J: {
            CoinType.COPPER: TreasureDetail(chance=25, amount="1d4"),
            CoinType.SILVER: TreasureDetail(chance=10, amount="1d3"),
            CoinType.ELECTRUM: TreasureDetail(chance=0, amount="0"),
            CoinType.GOLD: TreasureDetail(chance=0, amount="0"),
            CoinType.PLATINUM: TreasureDetail(chance=0, amount="0"),
            ItemType.GEMS_JEWELRY: TreasureDetail(chance=0, amount="0"),
            ItemType.MAGIC_ITEM: TreasureDetail(chance=0, amount="0", magical=True),
        },
        TreasureType.K: {
            CoinType.COPPER: TreasureDetail(chance=0, amount="0"),
            CoinType.SILVER: TreasureDetail(chance=30, amount="1d6"),
            CoinType.ELECTRUM: TreasureDetail(chance=10, amount="1d2"),
            CoinType.GOLD: TreasureDetail(chance=0, amount="0"),
            CoinType.PLATINUM: TreasureDetail(chance=0, amount="0"),
            ItemType.GEMS_JEWELRY: TreasureDetail(chance=0, amount="0"),
            ItemType.MAGIC_ITEM: TreasureDetail(chance=0, amount="0", magical=True),
        },
        TreasureType.L: {
            CoinType.COPPER: TreasureDetail(chance=0, amount="0"),
            CoinType.SILVER: TreasureDetail(chance=0, amount="0"),
            CoinType.ELECTRUM: TreasureDetail(chance=0, amount="0"),
            CoinType.GOLD: TreasureDetail(chance=100, amount="1d100"),
            CoinType.PLATINUM: TreasureDetail(chance=0, amount="0"),
            ItemType.GEMS_JEWELRY: TreasureDetail(chance=50, amount="1d6"),
            ItemType.MAGIC_ITEM: TreasureDetail(chance=30, amount="2", magical=True),
        },
        TreasureType.M: {
            CoinType.COPPER: TreasureDetail(chance=0, amount="0"),
            CoinType.SILVER: TreasureDetail(chance=0, amount="0"),
            CoinType.ELECTRUM: TreasureDetail(chance=0, amount="0"),
            CoinType.GOLD: TreasureDetail(chance=40, amount="2d8"),
            CoinType.PLATINUM: TreasureDetail(chance=50, amount="5d30"),
            ItemType.GEMS_JEWELRY: TreasureDetail(chance=55, amount="5d20"),
            ItemType.MAGIC_ITEM: TreasureDetail(chance=0, amount="0", magical=True),
        },
        TreasureType.N: {
            CoinType.COPPER: TreasureDetail(chance=0, amount="0"),
            CoinType.SILVER: TreasureDetail(chance=0, amount="0"),
            CoinType.ELECTRUM: TreasureDetail(chance=0, amount="0"),
            CoinType.GOLD: TreasureDetail(chance=0, amount="0"),
            CoinType.PLATINUM: TreasureDetail(chance=0, amount="0"),
            ItemType.GEMS_JEWELRY: TreasureDetail(chance=45, amount="2d12"),
            ItemType.MAGIC_ITEM: TreasureDetail(chance=40, amount="2d8", magical=True),
        },
        TreasureType.O: {
            CoinType.COPPER: TreasureDetail(chance=0, amount="0"),
            CoinType.SILVER: TreasureDetail(chance=0, amount="0"),
            CoinType.ELECTRUM: TreasureDetail(chance=0, amount="0"),
            CoinType.GOLD: TreasureDetail(chance=0, amount="0"),
            CoinType.PLATINUM: TreasureDetail(chance=0, amount="0"),
            ItemType.GEMS_JEWELRY: TreasureDetail(chance=50, amount="1d4"),
            ItemType.MAGIC_ITEM: TreasureDetail(chance=0, amount="0", magical=True),
        },
        TreasureType.P: {
            CoinType.COPPER: TreasureDetail(chance=100, amount="4d6"),
            CoinType.SILVER: TreasureDetail(chance=0, amount="0"),
            CoinType.ELECTRUM: TreasureDetail(chance=0, amount="0"),
            CoinType.GOLD: TreasureDetail(chance=0, amount="0"),
            CoinType.PLATINUM: TreasureDetail(chance=0, amount="0"),
            ItemType.GEMS_JEWELRY: TreasureDetail(chance=0, amount="0"),
            ItemType.MAGIC_ITEM: TreasureDetail(chance=0, amount="0", magical=True),
        },
        TreasureType.Q: {
            CoinType.COPPER: TreasureDetail(chance=0, amount="0"),
            CoinType.SILVER: TreasureDetail(chance=100, amount="3d6"),
            CoinType.ELECTRUM: TreasureDetail(chance=0, amount="0"),
            CoinType.GOLD: TreasureDetail(chance=0, amount="0"),
            CoinType.PLATINUM: TreasureDetail(chance=0, amount="0"),
            ItemType.GEMS_JEWELRY: TreasureDetail(chance=0, amount="0"),
            ItemType.MAGIC_ITEM: TreasureDetail(chance=0, amount="0", magical=True),
        },
        TreasureType.R: {
            CoinType.COPPER: TreasureDetail(chance=0, amount="0"),
            CoinType.SILVER: TreasureDetail(chance=0, amount="0"),
            CoinType.ELECTRUM: TreasureDetail(chance=100, amount="2d6"),
            CoinType.GOLD: TreasureDetail(chance=0, amount="0"),
            CoinType.PLATINUM: TreasureDetail(chance=0, amount="0"),
            ItemType.GEMS_JEWELRY: TreasureDetail(chance=0, amount="0"),
            ItemType.MAGIC_ITEM: TreasureDetail(chance=0, amount="0", magical=True),
        },
        TreasureType.S: {
            CoinType.COPPER: TreasureDetail(chance=0, amount="0"),
            CoinType.SILVER: TreasureDetail(chance=0, amount="0"),
            CoinType.ELECTRUM: TreasureDetail(chance=0, amount="0"),
            CoinType.GOLD: TreasureDetail(chance=100, amount="2d4"),
            CoinType.PLATINUM: TreasureDetail(chance=0, amount="0"),
            ItemType.GEMS_JEWELRY: TreasureDetail(chance=0, amount="0"),
            ItemType.MAGIC_ITEM: TreasureDetail(chance=0, amount="0", magical=True),
        },
        TreasureType.T: {
            CoinType.COPPER: TreasureDetail(chance=0, amount="0"),
            CoinType.SILVER: TreasureDetail(chance=0, amount="0"),
            CoinType.ELECTRUM: TreasureDetail(chance=0, amount="0"),
            CoinType.GOLD: TreasureDetail(chance=0, amount="0"),
            CoinType.PLATINUM: TreasureDetail(chance=100, amount="1d6"),
            ItemType.GEMS_JEWELRY: TreasureDetail(chance=0, amount="0"),
            ItemType.MAGIC_ITEM: TreasureDetail(chance=0, amount="0", magical=True),
        },
        TreasureType.U: {
            CoinType.COPPER: TreasureDetail(chance=10, amount="1d100"),
            CoinType.SILVER: TreasureDetail(chance=10, amount="1d100"),
            CoinType.ELECTRUM: TreasureDetail(chance=0, amount="0"),
            CoinType.GOLD: TreasureDetail(chance=5, amount="1d100"),
            CoinType.PLATINUM: TreasureDetail(chance=100, amount="0"),
            ItemType.GEMS_JEWELRY: TreasureDetail(chance=5, amount="1d4"),
            ItemType.MAGIC_ITEM: TreasureDetail(chance=200, amount="1", magical=True),
        },
        TreasureType.V: {
            CoinType.COPPER: TreasureDetail(chance=0, amount="0"),
            CoinType.SILVER: TreasureDetail(chance=10, amount="1d100"),
            CoinType.ELECTRUM: TreasureDetail(chance=5, amount="1d100"),
            CoinType.GOLD: TreasureDetail(chance=10, amount="1d100"),
            CoinType.PLATINUM: TreasureDetail(chance=5, amount="1d100"),
            ItemType.GEMS_JEWELRY: TreasureDetail(chance=10, amount="1d4"),
            ItemType.MAGIC_ITEM: TreasureDetail(chance=5, amount="1", magical=True),
        },
    }
    """Represents treasure configurations based on classic tabletop RPG game rules.

    This private class attribute maps each `TreasureType` to its possible contents, aligning with the variability and
    randomness of treasure discovery as set forth in some classic RPGs.
    """

    def __init__(self, treasure_type: TreasureType = None):
        self.items = {}
        if treasure_type:
            self._generate_treasure(treasure_type)

    def _generate_treasure(self, treasure_type: TreasureType) -> None:
        """Populates the treasure's contents based on whether and how much of each valuable should be included according
        to the treasure type.

        Args:
            treasure_type (TreasureType): The type of treasure for which to calculate its contents.
        """
        treasure_details = self._treasure_types[treasure_type]
        for item_type, details in treasure_details.items():
            chance_roll = roll_dice("1d100").total
            if chance_roll <= details.chance:
                amount_roll = roll_dice(details.amount)
                self.items[item_type] = amount_roll.total

    @property
    def total_gp_value(self) -> int:
        """Gets the total value in gold pieces (gp) of the treasure.

        Use this value when calculating the amount of experience points (XP) to award a party who obtains the treasure.
        For example, at the end of an encounter, quest, or any other event in which the party receives it.

        Returns:
            int: The total value in gold pieces (gp) of the coins, gems, jewelry, and items in the treasure.
        """
        total_gp_value = 0
        # Calculate the value of coins
        for item_type, amount in self.items.items():
            if isinstance(item_type, CoinType):
                total_gp_value += CoinType.value_in_gold({item_type: amount})

        # TODO: Calculate the value of the other items in the treasure
        # for item_type, amount in self.items.items():
        #     if isinstance(item_type, ItemType):
        #         total_gp_value += item_type.value * amount

        return total_gp_value

    @classmethod
    def from_treasure_type(cls, treasure_type: TreasureType) -> "Treasure":
        """Generate a treasure haul by populating the treasure's contents based the given treasure type.

        Args:
            treasure_type (TreasureType): The type of treasure for which to calculate its contents.

        Returns:
            Treasure: The treasure haul.
        """
        return cls(treasure_type)

    @classmethod
    def from_custom_type(cls, custom_type: Dict[Union[CoinType, ItemType], TreasureDetail]) -> "Treasure":
        """Creates a Treasure instance using a custom-defined treasure type.

        This method allows for the generation of your own custom sets of treasure not included in the
        standard treasure types. The custom_type parameter should be a dictionary mapping CoinType or
        ItemType to TreasureDetail, similar to the predefined treasure types.

        Args:
            custom_type (Dict[Union[CoinType, ItemType], TreasureDetail]): Custom-defined treasure type details.

        Returns:
            Treasure: An instance of Treasure whose contents are based on the custom treasure type.

        Example:
            python```
            # Define a custom treasure type with a 50% chance of 2d6 gold pieces, 40% chance of 1d4 gems/jewelry,
            # and 15% chance of 1 magic item.
            custom_treasure_type = {
                CoinType.GOLD: TreasureDetail(chance=50, amount="2d6", magical=False),
                ItemType.GEMS_JEWELRY: TreasureDetail(chance=40, amount="1d4", magical=False),
                ItemType.MAGIC_ITEM: TreasureDetail(chance=15, amount="1", magical=True)
            }
            # Creating a Treasure instance with the custom treasure type
            custom_treasure = Treasure.from_custom_type(custom_treasure_type)
            # The custom_treasure Treasure instance now contains items based on the custom type definition
            ```
        """
        treasure = cls()
        for item_type, details in custom_type.items():
            chance_roll = roll_dice("1d100").total
            if chance_roll <= details.chance:
                amount_roll = roll_dice(details.amount)
                treasure.items[item_type] = amount_roll.total
        return treasure

# Example usage:
treasure_haul_01 = Treasure.from_treasure_type(TreasureType.A)
treasure_haul_02 = Treasure(TreasureType.B)

print(f"Treasure haul 1: {treasure_haul_01}")
print(f"Treasure haul 2: {treasure_haul_02}")

xp_from_treasure = treasure_haul_01.total_gp_value + treasure_haul_02.total_gp_value
print(f"Total XP from treasure: {xp_from_treasure}")

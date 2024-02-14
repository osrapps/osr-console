"""Implements the treasure generation system inspired by a 1980's version of the world's most popular role-playing game.

The system is built around the [Treasure][osrlib.treasure.Treasure] class, which encapsulates the logic for generating treasure hauls for the the
player's party. Central to `Treasure` class is the `_treasure_types` attribute, a detailed mapping of various treasure
categories to their respective contents. These categories represent different types of treasure the party might obtain,
each with specified probabilities and quantities of items like coins, gems, jewelry, and magical items.
"""
import random
from typing import Dict, Union, List
from dataclasses import dataclass
from osrlib.dice_roller import roll_dice
from osrlib.enums import ItemType, TreasureType, CoinType
from osrlib.item import Item
from osrlib.item_factories import get_random_item
from osrlib.utils import logger

from enum import Enum


@dataclass
class TreasureDetail:
    """Defines the characteristics of a particular "unit" of treasure (coins, gems, magic items, ...) in a treasure type.

    This class dictates the attributes of each item type within a defined treasure type. It outlines the chance of
    occurrence, the amount (in dice notation or a fixed number), and whether the item is magical. This class is used
    by the `Treasure` class, but you can also use it to customize the contents of treasure hauls by creating your own
    treasure types.

    Attributes:
        chance (int): The probability (as a percentage) of this item appearing in the treasure.
        amount (str): The quantity of the item, expressed in dice notation (e.g., "1d6") or as a fixed number.
        magical (bool): True if the item is magical, False otherwise (defaults to False).

    Example:

    ```python
    # Defining a custom treasure detail for a new treasure type
    custom_treasure_detail = TreasureDetail(chance=40, amount="3d4")
    custom_treasure_type = {
        CoinType.GOLD: custom_treasure_detail,
        ItemType.MAGIC_ITEM: TreasureDetail(chance=25, amount="1", magical=True)
    }
    custom_treasure = Treasure.from_custom_type(custom_treasure_type)
    # This creates a Treasure instance with the custom-defined treasure type
    ```
    """
    chance: int  # Probability of appearing in the treasure haul
    amount: str  # Dice notation for the amount/number of coins/items
    magical: bool = False  # Whether the item should be magical


class Treasure:
    """Represents a treasure haul within the game, encapsulating various physical item rewards.

    `Treasure` manages the generation and valuation of treasures comprising coins, gems, jewelry, and magical items.
    The treasure is generated based on predefined types, each corresponding to different probabilities and amounts
    of items. The class provides functionalities to generate treasure based on a specified type, calculate its total
    value in gold pieces (gp), and retrieve the generated items.

    Attributes:
        items (Dict[Union[CoinType, ItemType], int]): A dictionary holding the treasure items. The keys are instances
                                                      of either CoinType or ItemType enumerations, and the values are
                                                      integers representing the quantity of each item.

    Example:

    ```python
    treasure_haul_01 = Treasure.from_treasure_type(TreasureType.A)
    treasure_haul_02 = Treasure(TreasureType.B)

    print(f"Treasure haul 1: {treasure_haul_01}")
    print(f"Treasure haul 2: {treasure_haul_02}")

    xp_from_treasure = treasure_haul_01.total_gp_value + treasure_haul_02.total_gp_value
    print(f"Total XP from treasure: {xp_from_treasure}")
    ```
    """
    items: Dict[Union[CoinType, ItemType], int]
    magic_items: List[Item]

    _treasure_types: Dict[
        TreasureType, Dict[Union[CoinType, ItemType], TreasureDetail]
    ] = {
        TreasureType.NONE: {},
        TreasureType.A: {
            CoinType.COPPER: TreasureDetail(chance=25, amount="1000d6"),
            CoinType.SILVER: TreasureDetail(chance=30, amount="1000d6"),
            CoinType.ELECTRUM: TreasureDetail(chance=20, amount="1000d4"),
            CoinType.GOLD: TreasureDetail(chance=35, amount="2000d6"),
            CoinType.PLATINUM: TreasureDetail(chance=25, amount="1000d2"),
            ItemType.GEMS_JEWELRY: TreasureDetail(chance=50, amount="6d6"),
            ItemType.ARMOR: TreasureDetail(chance=30, amount="1", magical=True),
            ItemType.WEAPON: TreasureDetail(chance=30, amount="1", magical=True),
        },
        TreasureType.B: {
            CoinType.COPPER: TreasureDetail(chance=50, amount="1000d8"),
            CoinType.SILVER: TreasureDetail(chance=25, amount="1000d6"),
            CoinType.ELECTRUM: TreasureDetail(chance=25, amount="1000d4"),
            CoinType.GOLD: TreasureDetail(chance=25, amount="1000d3"),
            ItemType.GEMS_JEWELRY: TreasureDetail(chance=25, amount="1d6"),
            ItemType.MAGIC_ITEM: TreasureDetail(chance=10, amount="1", magical=True),
        },
        TreasureType.C: {
            CoinType.COPPER: TreasureDetail(chance=20, amount="1000d12"),
            CoinType.SILVER: TreasureDetail(chance=30, amount="1000d4"),
            CoinType.ELECTRUM: TreasureDetail(chance=10, amount="1000d4"),
            ItemType.GEMS_JEWELRY: TreasureDetail(chance=25, amount="1d4"),
            ItemType.MAGIC_ITEM: TreasureDetail(chance=10, amount="2", magical=True),
        },
        TreasureType.D: {
            CoinType.COPPER: TreasureDetail(chance=10, amount="1000d8"),
            CoinType.SILVER: TreasureDetail(chance=15, amount="1000d12"),
            CoinType.GOLD: TreasureDetail(chance=60, amount="1000d6"),
            ItemType.GEMS_JEWELRY: TreasureDetail(chance=30, amount="1d8"),
            ItemType.MAGIC_ITEM: TreasureDetail(chance=15, amount="3", magical=True),
        },
        TreasureType.E: {
            CoinType.COPPER: TreasureDetail(chance=5, amount="1000d10"),
            CoinType.SILVER: TreasureDetail(chance=30, amount="1000d12"),
            CoinType.ELECTRUM: TreasureDetail(chance=25, amount="1000d4"),
            CoinType.GOLD: TreasureDetail(chance=25, amount="1000d8"),
            ItemType.GEMS_JEWELRY: TreasureDetail(chance=10, amount="1d10"),
            ItemType.MAGIC_ITEM: TreasureDetail(chance=25, amount="4", magical=True),
        },
        TreasureType.F: {
            CoinType.SILVER: TreasureDetail(chance=10, amount="2000d10"),
            CoinType.ELECTRUM: TreasureDetail(chance=20, amount="1000d8"),
            CoinType.GOLD: TreasureDetail(chance=45, amount="1000d12"),
            CoinType.PLATINUM: TreasureDetail(chance=30, amount="1000d3"),
            ItemType.GEMS_JEWELRY: TreasureDetail(chance=20, amount="2d12"),
            ItemType.MAGIC_ITEM: TreasureDetail(chance=30, amount="5", magical=True),
        },
        TreasureType.G: {
            CoinType.GOLD: TreasureDetail(chance=50, amount="10000d4"),
            CoinType.PLATINUM: TreasureDetail(chance=50, amount="1000d6"),
            ItemType.GEMS_JEWELRY: TreasureDetail(chance=25, amount="3d6"),
            ItemType.MAGIC_ITEM: TreasureDetail(chance=35, amount="5", magical=True),
        },
        TreasureType.H: {
            CoinType.COPPER: TreasureDetail(chance=25, amount="3000d8"),
            CoinType.SILVER: TreasureDetail(chance=50, amount="1000d100"),
            CoinType.ELECTRUM: TreasureDetail(chance=50, amount="10000d4"),
            CoinType.GOLD: TreasureDetail(chance=50, amount="10000d6"),
            CoinType.PLATINUM: TreasureDetail(chance=25, amount="5000d4"),
            ItemType.GEMS_JEWELRY: TreasureDetail(chance=50, amount="1d100"),
            ItemType.MAGIC_ITEM: TreasureDetail(chance=15, amount="6", magical=True),
        },
        TreasureType.I: {
            CoinType.PLATINUM: TreasureDetail(chance=30, amount="1000d8"),
            ItemType.GEMS_JEWELRY: TreasureDetail(chance=50, amount="2d6"),
            ItemType.MAGIC_ITEM: TreasureDetail(chance=15, amount="1", magical=True),
        },
        TreasureType.J: {
            CoinType.COPPER: TreasureDetail(chance=25, amount="1000d4"),
            CoinType.SILVER: TreasureDetail(chance=10, amount="1000d3"),
        },
        TreasureType.K: {
            CoinType.SILVER: TreasureDetail(chance=30, amount="1000d6"),
            CoinType.ELECTRUM: TreasureDetail(chance=10, amount="1000d2"),
        },
        TreasureType.L: {
            ItemType.GEMS_JEWELRY: TreasureDetail(chance=50, amount="1d4"),
        },
        TreasureType.M: {
            CoinType.GOLD: TreasureDetail(chance=40, amount="2000d4"),
            CoinType.PLATINUM: TreasureDetail(chance=50, amount="5000d6"),
            ItemType.GEMS_JEWELRY: TreasureDetail(chance=55, amount="5d4"),
        },
        TreasureType.N: {
            ItemType.MAGIC_ITEM: TreasureDetail(chance=40, amount="2000d4", magical=True),
        },
        TreasureType.O: {
            ItemType.MAGIC_ITEM: TreasureDetail(chance=50, amount="1d4", magical=True),
        },
        TreasureType.P: {
            CoinType.COPPER: TreasureDetail(chance=100, amount="4d6"),
        },
        TreasureType.Q: {
            CoinType.SILVER: TreasureDetail(chance=100, amount="3d6"),
        },
        TreasureType.R: {
            CoinType.ELECTRUM: TreasureDetail(chance=100, amount="2d6"),
        },
        TreasureType.S: {
            CoinType.GOLD: TreasureDetail(chance=100, amount="2d4"),
        },
        TreasureType.T: {
            CoinType.PLATINUM: TreasureDetail(chance=100, amount="1d6"),
        },
        TreasureType.U: {
            CoinType.COPPER: TreasureDetail(chance=10, amount="1d100"),
            CoinType.SILVER: TreasureDetail(chance=10, amount="1d100"),
            CoinType.GOLD: TreasureDetail(chance=5, amount="1d100"),
            ItemType.GEMS_JEWELRY: TreasureDetail(chance=5, amount="1d4"),
            ItemType.MAGIC_ITEM: TreasureDetail(chance=2, amount="1", magical=True),
        },
        TreasureType.V: {
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

    def __init__(self, treasure_type: TreasureType = TreasureType.NONE):
        self.items = {}
        self.magic_items = []
        self._generate_treasure(treasure_type)
        self.treasure_type = treasure_type

    def __str__(self) -> str:
        """Returns a string representation of the treasure in a multi-line format, showing each type of treasure with its quantity on separate lines, followed by the total value in gold pieces (GP) on a separate line.

        Returns:
            str: A multi-line description of the treasure's contents and total GP value.
        """
        lines = []
        lines.append(f"{str(self.treasure_type)} ({self.total_gp_value} GP value)")

        for item_type, amount in self.items.items():
            if isinstance(item_type, CoinType):
                lines.append(f"{item_type.name.capitalize()}: {amount}")
            elif isinstance(item_type, ItemType):
                # Adjusting item name formatting to be more readable
                item_name = item_type.name.replace('_', ' ').capitalize()
                lines.append(f"{item_name}: {amount}")
            else:
                # Fallback for any item types not accounted for
                lines.append(f"Unknown item: {amount}")

        return " | ".join(lines)

    def _generate_treasure(self, treasure_type: TreasureType) -> None:
        """Populates the treasure's contents based on whether and how much of each valuable should be included according to the treasure type.

        Args:
            treasure_type (TreasureType): The type of treasure for which to calculate its contents.
        """
        treasure_details = self._treasure_types[treasure_type]
        for item_type, details in treasure_details.items():
            chance_roll = roll_dice("1d100").total
            if chance_roll <= details.chance:
                amount_roll = roll_dice(details.amount)
                if isinstance(item_type, CoinType):
                    self.items[item_type] = amount_roll.total_with_modifier
                elif item_type == ItemType.ARMOR or item_type == ItemType.WEAPON:
                    magic_item = get_random_item(item_type, magical=True)
                    self.magic_items.append(magic_item)
                    logger.debug(f"Added {magic_item} to {treasure_type}")

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

        ```python
        # Define a custom treasure type with a 50% chance of 2d6 gold pieces,
        # 40% chance of 1d4 gems/jewelry, and 15% chance of 1 magic item.
        custom_treasure_type = {
            CoinType.GOLD: TreasureDetail(chance=50, amount="2d6", magical=False),
            ItemType.GEMS_JEWELRY: TreasureDetail(chance=40, amount="1d4", magical=False),
            ItemType.MAGIC_ITEM: TreasureDetail(chance=15, amount="1", magical=True)
        }
        # Create a Treasure instance with the custom treasure type
        custom_treasure = Treasure.from_custom_type(custom_treasure_type)
        ```
        """
        treasure = cls()
        for item_type, details in custom_type.items():
            chance_roll = roll_dice("1d100").total
            if chance_roll <= details.chance:
                amount_roll = roll_dice(details.amount)
                treasure.items[item_type] = amount_roll.total
        return treasure

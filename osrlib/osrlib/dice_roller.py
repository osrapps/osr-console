"""Dice roller module for rolling dice based on the nDn or Dn notation, supporting modifiers.

This module provides functionality for rolling dice using traditional RPG notations such as '3d6' (three six-sided dice)
and '1d20+5' (one twenty-sided die plus a modifier of 5). It supports modifiers and the option to drop the lowest roll.
"""

import random
import re
from collections import namedtuple

class DiceRoll(
    namedtuple(
        "RollResultBase",
        ["num_dice", "num_sides", "total", "modifier", "total_with_modifier", "rolls"],
    )
):
    """Represent the result of a dice roll.

    This class is a named tuple containing details of a dice roll, including the number of dice, number of sides,
    base roll, modifier, total roll with modifier, and the individual rolls.

    Attributes:
        num_dice (int): Number of dice rolled.
        num_sides (int): Number of sides on each die.
        total (int): Total value of the dice rolls without modifiers.
        modifier (int): Modifier value added to or subtracted from the total roll.
        total_with_modifier (int): Total value of the dice rolls including the modifier.
        rolls (list): List of individual die roll results.
    """

    def __str__(self):
        """
        Return a string representation of the dice roll in ndn notation, including modifiers if applicable.

        Returns:
            str: A string in ndn notation (e.g., '3d6', '1d20+5', '2d8-4').
        """
        base = f"{self.num_dice}d{self.num_sides}"
        if self.modifier > 0:
            return f"{base}+{self.modifier}"
        elif self.modifier < 0:
            return f"{base}{self.modifier}"
        else:
            return base

    def pretty_print(self):
        """Return a human-readable string representation of the dice roll, including the total roll and any modifiers.

        Returns:
            str: A string describing the dice roll and its outcome (e.g., 'Rolled 3d6 and got 11 (11)',
                 'Rolled 1d20+3 and got 9 (6 + 3)').
        """
        base_str = f"{self.total}"
        if self.modifier != 0:
            base_str += f" {'+' if self.modifier > 0 else '-'} {abs(self.modifier)}"
        return f"Rolled {self.total_with_modifier} on {self} ({base_str})"

def roll_dice(notation: str, modifier: int = 0, drop_lowest: bool = False) -> DiceRoll:
    """Roll dice based on the nDn or Dn notation and factor in optional modifiers.

    Examples:
        roll_dice('3d6') -> DiceRoll object representing a roll of three six-sided dice.
        roll_dice('1d20+5') -> DiceRoll object for rolling one twenty-sided die with a +5 modifier.
        roll_dice('20') -> DiceRoll object for a guaranteed roll of 20.

    Args:
        notation (str): A string representation of a dice roll in ndn format with optional modifiers like '3d6',
                        '1d20+5', or '2d8-4', or a string representing an integer, like '1', '20', or '18'.
        modifier (int): An optional additional integer modifier to add to the roll. Defaults to 0.
        drop_lowest (bool): Whether to drop the lowest dice roll. Defaults to False.

    Returns:
        DiceRoll: A named tuple containing the number of dice, number of sides, base roll, modifier, total roll
                  with modifier, and the individual rolls.

    Raises:
        ValueError: If the notation or dice sides are invalid.
    """
    notation = notation.replace(" ", "").lower()

    try:
        # First check to see if the notation string is a single integer passed as a string.
        # We need to support calls that pass in a specific value in order to guarantee that
        # the "roll" returns that value. You might do this in scenarios like specifying a
        # set number of monsters in an encounter or number of gold pieces in a reward. This
        # also enables unit tests that need a consistent roll results for their test cases.
        num_sides = int(notation)
        return DiceRoll(1, num_sides, num_sides, 0, num_sides, [num_sides])
    except ValueError:
        pass

    match = re.match(r"(\d*)d(\d+)([+-]\d+)?", notation, re.IGNORECASE)
    if not match:
        raise ValueError(
            "Invalid number of dice and sides. Use dn or ndn format like 'd6', '3d6', '3d6+2', or '3d6-2'."
        )

    num_dice, num_sides, notation_modifier = match.groups()
    num_dice = int(num_dice) if num_dice else 1
    num_sides = int(num_sides)
    modifier += int(notation_modifier) if notation_modifier else 0

    rand_gen = random.SystemRandom()
    die_rolls = [rand_gen.randint(1, num_sides) for _ in range(num_dice)]

    if drop_lowest and len(die_rolls) > 1:
        die_rolls.remove(min(die_rolls))

    total = sum(die_rolls)
    total_with_modifier = total + modifier

    return DiceRoll(
        num_dice, num_sides, total, modifier, total_with_modifier, die_rolls
    )

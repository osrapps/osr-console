import random
import re
from collections import namedtuple


class DiceRoll(
    namedtuple(
        "RollResultBase",
        ["num_dice", "num_sides", "total", "modifier", "total_with_modifier", "rolls"],
    )
):
    def __str__(self):
        """
        Returns a string representation of the dice roll based on the ndn notation, including modifiers if applicable.

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
        """
        Returns a human-readable string representation of the dice roll, including the total roll and any modifiers.

        Returns:
            str: A string describing the dice roll and its outcome (e.g., 'Rolled 3d6 and got 11 (11)', 'Rolled 1d20+3 and got 9 (6 + 3)').
        """
        base_str = f"{self.total}"
        if self.modifier != 0:
            base_str += f" {'+' if self.modifier > 0 else '-'} {abs(self.modifier)}"
        return f"Rolled {self.total_with_modifier} on {self} ({base_str})"


def roll_dice(notation: str, modifier: int = 0, drop_lowest: bool = False):
    """
    Rolls dice based on the nDn or Dn notation, supporting modifiers.

    Args:
        notation (str): The dice notation in ndn format with optional modifiers (e.g., '3d6', '1d20+5', '2d8-4').
        modifier (int): An optional additional integer modifier to add to the roll. Defaults to 0.
        drop_lowest (bool): Whether to drop the lowest dice roll. Defaults to False.

    Returns:
        DiceRoll: A named tuple containing the number of dice, number of sides, base roll, modifier, total roll with modifier, and the individual rolls.

    Raises:
        ValueError: If the notation or dice sides are invalid.

    Example usage:
        >>> result = roll_dice('3d6')
        >>> print(result.pretty_print())

        >>> result = roll_dice('1d20+5')
        >>> print(result.pretty_print())

        >>> result = roll_dice('4d6', drop_lowest=True)
        >>> print(result.pretty_print())
    """
    rand_gen = random.SystemRandom()

    notation = notation.replace(" ", "")
    notation = _add_modifier_to_dice_notation(notation, modifier)

    match = re.match(r"(\d*)d(\d+)([+-]\d+)?", notation, re.IGNORECASE)

    num_dice, num_sides, modifier = match.groups()
    num_dice = int(num_dice) if num_dice else 1
    num_sides = int(num_sides)
    modifier = int(modifier) if modifier else 0

    if num_sides not in [4, 6, 8, 10, 12, 20, 100]:
        raise ValueError("Invalid number of dice sides. Choose from 4, 6, 8, 10, 12, 20, 100.")

    die_rolls = [rand_gen.randint(1, num_sides) for _ in range(num_dice)]

    if drop_lowest and len(die_rolls) > 1:
        die_rolls.remove(min(die_rolls))

    total = sum(die_rolls)
    total_with_modifier = total + modifier

    return DiceRoll(num_dice, num_sides, total, modifier, total_with_modifier, die_rolls)


def _add_modifier_to_dice_notation(notation: str, modifier: int) -> str:
    """
    Adds a modifier to a dice notation string.

    Args:
        notation (str): Existing dice notation string, like '1d6' or '1d6+1'.
        modifier (int): The integer modifier to add.

    Returns:
        str: The modified dice notation string.

    Raises:
        ValueError: If the input notation is invalid.
    """
    match = re.match(r"(\d*)d(\d+)([+-]\d+)?", notation, re.IGNORECASE)
    if not match:
        raise ValueError(
            "Invalid number of dice and sides. Use dn or ndn format like 'd6', '3d6', '3d6+2', or '3d6-2'."
        )

    num_dice, num_sides, existing_modifier = match.groups()

    existing_modifier = int(existing_modifier) if existing_modifier else 0

    new_modifier = existing_modifier + modifier
    if new_modifier == 0:
        return f"{num_dice}d{num_sides}"
    elif new_modifier > 0:
        return f"{num_dice}d{num_sides}+{new_modifier}"
    else:
        return f"{num_dice}d{num_sides}{new_modifier}"


# Example usage
if __name__ == "__main__":
    dice_roll = roll_dice("3d6")
    print(dice_roll.pretty_print())

    dice_roll = roll_dice("1d20+3")
    print(dice_roll.pretty_print())

    dice_roll = roll_dice("2D8 - 3")
    print(dice_roll.pretty_print())

    dice_roll = roll_dice("4d6", drop_lowest=True)
    print(dice_roll.pretty_print() + " (dropped lowest)")

    dice_roll = roll_dice("d20")
    print(dice_roll.pretty_print())

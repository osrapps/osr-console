import logging
from unittest.mock import patch

import pytest

from osrlib.dice_roller import DiceRoll, roll_dice

logger = logging.getLogger(__name__)
logger.debug("Testing dice_roller.py")


def test_valid_notation():
    """Tests valid dice notation.

    Checks whether the roll_dice function correctly handles a valid dice notation '3d6'.
    Mocks randint to always return 3 for consistent testing.
    """
    with patch("random.SystemRandom.randint", return_value=3):
        result = roll_dice("3d6")
    assert result == DiceRoll(3, 6, 9, 0, 9, [3, 3, 3])


def test_invalid_notation():
    """Tests invalid dice notation.

    Checks whether the roll_dice function raises a ValueError for an invalid dice notation '3dd6'.
    """
    with pytest.raises(ValueError):
        roll_dice("3dd6")

def test_with_modifier():
    """Tests dice notation with a positive modifier.

    Checks whether the roll_dice function correctly adds the positive modifier to the total roll.
    Mocks randint to always return 3 for consistent testing.
    """
    with patch("random.SystemRandom.randint", return_value=3):
        result = roll_dice("3d6+2")
    assert result == DiceRoll(3, 6, 9, 2, 11, [3, 3, 3])


def test_drop_lowest():
    """Tests dropping the lowest dice roll.

    Checks whether the roll_dice function correctly drops the lowest dice when the flag is set.
    Mocks randint to return specific values [1, 3, 5, 7] for consistent testing.
    """
    with patch("random.SystemRandom.randint", side_effect=[1, 3, 5, 7]):
        result = roll_dice("4d6", drop_lowest=True)
    assert result == DiceRoll(4, 6, 15, 0, 15, [3, 5, 7])


def test_str_representation():
    """Tests the string representation of DiceRoll.

    Checks whether the string representation of the DiceRoll object is as expected.
    """
    result = DiceRoll(3, 6, 9, 0, 9, [3, 3, 3])
    assert str(result) == "3d6"


def test_pretty_print():
    """Tests the pretty print of DiceRoll.

    Checks whether the pretty print of the DiceRoll object correctly displays the full roll information.
    """
    result = DiceRoll(3, 6, 9, 2, 11, [3, 3, 3])
    assert result.pretty_print() == "Rolled 11 on 3d6+2 (9 + 2)"

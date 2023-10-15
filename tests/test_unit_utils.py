import logging

from osrlib import ModifierType
from osrlib.utils import format_modifiers

logger = logging.getLogger(__name__)


def test_format_modifiers():
    """Test function for the format_modifiers() utility function.

    This function tests the format_modifiers() function with various input values and verifies that the output is as expected.
    """
    logger.info("Testing empty modifiers: '" + format_modifiers({}) + "'")
    assert format_modifiers({}) == ""

    logger.info("Testing single modifier with positive value: '" + format_modifiers({ModifierType.TO_HIT: 1}) + "'")
    assert format_modifiers({ModifierType.TO_HIT: 1}) == "To hit: +1"

    logger.info("Testing single modifier with negative value: '" + format_modifiers({ModifierType.DAMAGE: -1}) + "'")
    assert format_modifiers({ModifierType.DAMAGE: -1}) == "Damage: -1"

    logger.info(
        "Testing single modifier with no (zero) value: '" + format_modifiers({ModifierType.OPEN_DOORS: 0}) + "'"
    )
    assert format_modifiers({ModifierType.OPEN_DOORS: 0}) == "Open doors: 0"

    logger.info(
        "Testing multiple modifiers with positive and negative values: '"
        + format_modifiers(
            {
                ModifierType.TO_HIT: 1,
                ModifierType.DAMAGE: -1,
                ModifierType.OPEN_DOORS: 0,
            }
        )
        + "'"
    )
    assert (
        format_modifiers(
            {
                ModifierType.TO_HIT: 1,
                ModifierType.DAMAGE: -1,
                ModifierType.OPEN_DOORS: 0,
            }
        )
        == "To hit: +1, Damage: -1, Open doors: 0"
    )

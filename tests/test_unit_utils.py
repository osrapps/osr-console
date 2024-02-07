from osrlib.ability import ModifierType
from osrlib.utils import format_modifiers
from osrlib.utils import logger

def test_format_modifiers():
    """Test function for the format_modifiers() utility function.

    This function tests the format_modifiers() function with various input values and verifies that the output is as expected.
    """
    logger.debug("Testing empty modifiers: '" + format_modifiers({}) + "'")
    assert format_modifiers({}) == ""

    logger.debug("Testing single modifier with positive value: '" + format_modifiers({ModifierType.TO_HIT: 1}) + "'")
    assert format_modifiers({ModifierType.TO_HIT: 1}) == "To hit: +1"

    logger.debug("Testing single modifier with negative value: '" + format_modifiers({ModifierType.DAMAGE: -1}) + "'")
    assert format_modifiers({ModifierType.DAMAGE: -1}) == "Damage: -1"

    logger.debug(
        "Testing single modifier with no (zero) value: '" + format_modifiers({ModifierType.OPEN_DOORS: 0}) + "'"
    )
    assert format_modifiers({ModifierType.OPEN_DOORS: 0}) == "Open doors: 0"

    logger.debug(
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

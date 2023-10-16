from osrlib import ModifierType


def format_modifiers(modifiers: dict[ModifierType, int]) -> str:
    """Get a string representation of the given modifiers.

    The formatted modifier string returned by this function is a comma-delimited list of the given modifiers. Each
    modifier includes its name and value. The value string includes its polarity if it's positive or negative.

    Example:

        >>> # This should return "Strength: +1, Dexterity: -1"
        >>> format_modifiers({ModifierType.STRENGTH: 1, ModifierType.DEXTERITY: -1})

    Args:
        modifiers: A dictionary of modifiers to format.

    Returns:
        A comma-delimited string representation of the modifiers.
    """
    return ", ".join(f"{mod.value}: {'+' if val > 0 else ''}{val}" for mod, val in modifiers.items())

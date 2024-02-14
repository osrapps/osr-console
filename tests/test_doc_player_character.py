"""Testable code examples for `PlayerCharacter` and related classes.

The code in this module is ingested by and displayed in documentation for the `osrlib` package.
"""

import pytest

# --8<-- [start:player_character_create]
from osrlib.enums import CharacterClassType
from osrlib.player_character import PlayerCharacter

def test_doc_player_character_create():

    # Create a fighter PC and roll their abilities and hit points (HP)
    fighter_pc = PlayerCharacter("Sckricko", CharacterClassType.FIGHTER)
    fighter_pc.roll_abilities()
    fighter_pc.roll_hp()
# --8<-- [end:player_character_create]

    assert len(fighter_pc.abilities) > 0
    assert fighter_pc.hit_points >= 1
    assert fighter_pc.name == "Sckricko"

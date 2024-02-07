"""Integration tests for the DungeonAssistant class.

Tests include starting a session and moving the party in a dungeon.

These tests expect an OPENAI_API_KEY environment variable has been set.
"""
import pytest
from osrlib.dungeon import Dungeon, Location, Exit, Direction
from osrlib.dungeon_assistant import DungeonAssistant
from osrlib.adventure import Adventure
from osrlib.utils import logger

@pytest.mark.optin
@pytest.mark.flaky(reruns=0, reruns_delay=0)
@pytest.mark.integration
def test_dungeon_master_start_session_real_api():
    adventure = Adventure("Test Adventure")
    adventure.introduction = "In a land shrouded by mist and haunted by forgotten gods, your party stands before the gaping maw of Darkfang Cavern. Rumors abound of an ancient artifact of terrible power hidden deep within, guarded by spectral knights and nightmarish beasts. Will you claim the artifact and ascend to untold glory, or fall like so many before you, your names etched into the cavern's endless walls of sorrow? The choice is yours, brave adventurers. Venture forth!"
    dm = DungeonAssistant(adventure)

    message = dm.start_session()
    logger.debug(message)
    assert len(message) > 0

@pytest.mark.optin
@pytest.mark.flaky(reruns=0, reruns_delay=0)
@pytest.mark.integration
def test_dungeon_master_move_party():
    adventure = Adventure("Test Adventure")
    adventure.introduction = "Deep within the heart of the Ironclad Mountains lies the long-forgotten mine of Dwurin's Hold, a once-prosperous dwarven establishment now reduced to whispered rumors and tavern tales. Legend holds that a fearsome dragon named Ebonflame has claimed the labyrinthine tunnels as its lair, its fiery breath illuminating the darkened corridors once chiseled with dwarven precision. The beleaguered town of Stonehearth has suffered a series of devastating raids, livestock and treasure vanishing in plumes of smoke and flame. Mayor Thoric Ironfist, desperate and out of options, has commissioned your party to delve into the mine, confirm the presence of the mythical beast, and eliminate the threat that hangs like a dark cloud over the land."

    loc0 = Location(9999, 10, 10, [Exit(Direction.NORTH, 1)], ["inn", "town"], None)
    loc1 = Location(1, 40, 30, [Exit(Direction.SOUTH, 0), Exit(Direction.NORTH, 2)], ["just outside", "dwarven mines", "ancient", "entrance", "cold wind", "dragon rumors"], None)
    loc2 = Location(2, 10, 10, [Exit(Direction.SOUTH, 1), Exit(Direction.NORTH, 3)], ["vestibule", "large entry doors", "dirty stone", "carvings"], None)
    loc3 = Location(3, 5, 5, [Exit(Direction.SOUTH, 2)], ["guard station", "broken weapons", "bat droppings"], None)
    dungeon = Dungeon("Dungeon of Bread", "An ancient lost dwarven mine.", [loc0, loc1, loc2, loc3], 9999)
    adventure.add_dungeon(dungeon)
    adventure.set_active_dungeon(dungeon)
    dm = DungeonAssistant(adventure)

    message = dm.start_session()
    logger.debug(message)
    assert len(message) > 0

    loc_desc = dm.move_party(Direction.NORTH)
    logger.debug(loc_desc)
    assert len(loc_desc) > 0

    loc_desc = dm.move_party(Direction.NORTH)
    logger.debug(loc_desc)
    assert len(loc_desc) > 0

    loc_desc = dm.move_party(Direction.NORTH)
    logger.debug(loc_desc)
    assert len(loc_desc) > 0

    loc_desc = dm.move_party(Direction.SOUTH)
    logger.debug(loc_desc)
    assert len(loc_desc) > 0
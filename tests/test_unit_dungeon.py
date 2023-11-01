from random import randint, sample, choice
import json
import pytest
from osrlib.dungeon import Dungeon, Location, Exit, Direction, LocationNotFoundError, get_random_dungeon
from osrlib.encounter import Encounter

# --- Test Exit class ---


def test_exit_initialization():
    exit_north = Exit(Direction.NORTH, 1)
    assert exit_north.direction == Direction.NORTH
    assert exit_north.destination == 1
    assert exit_north.locked == False


def test_exit_lock_unlock():
    exit_north = Exit(Direction.NORTH, 1)
    exit_north.lock()
    assert exit_north.locked == True
    exit_north.unlock()
    assert exit_north.locked == False


# --- Test Location class ---


def test_location_initialization():
    exit_north = Exit(Direction.NORTH, 1)
    encounter = Encounter()  # TODO: Set this up with real encounter
    location = Location(1, 10, 10, [exit_north], ["keyword1"], encounter)

    assert location.id == 1
    assert location.dimensions == {"width": 10, "length": 10}
    assert location.exits == [exit_north]
    assert location.keywords == ["keyword1"]
    assert location.encounter == encounter

def test_location_json():
    # Create an Exit object
    exit1 = Exit(Direction.NORTH, 2)
    exit2 = Exit(Direction.SOUTH, 1)

    # Create a Location object
    location = Location(
        id=1,
        width=10,
        length=10,
        exits=[exit1, exit2],
        keywords=["test", "location"]
    )

    # Get the JSON representation
    location_json = location.json

    # Parse it back to Python object
    location_dict = json.loads(location_json)

    # Validate individual fields
    assert location_dict["id"] == 1
    assert location_dict["dimensions"]["width"] == 10
    assert location_dict["dimensions"]["length"] == 10
    assert location_dict["keywords"] == ["test", "location"]

    # Validate exits
    assert len(location_dict["exits"]) == 2
    assert location_dict["exits"][0]["direction"] == "N"
    assert location_dict["exits"][0]["destination"] == 2
    assert location_dict["exits"][0]["locked"] == False

    # Validate that 'encounter' is None
    assert location_dict["encounter"] is None

# --- Test Dungeon class ---


def test_dungeon_initialization():
    exit_north = Exit(Direction.NORTH, 1)
    encounter = (
        Encounter()
    )  # You would set this up properly according to your Encounter class
    location1 = Location(1, 10, 10, [exit_north], ["keyword1"], encounter)
    location2 = Location(2, 6, 6, [], ["keyword2"], None)
    dungeon = Dungeon("Test Dungeon", "A test dungeon.", [location1, location2])

    assert dungeon.name == "Test Dungeon"
    assert dungeon.description == "A test dungeon."
    assert dungeon.locations == [location1, location2]


def test_set_start_location():
    exit1 = Exit(Direction.NORTH, 2)
    location1 = Location(1, exits=[exit1])
    dungeon = Dungeon(locations=[location1])

    with pytest.raises(LocationNotFoundError):
        dungeon.set_start_location(99)

    start_location = dungeon.set_start_location(1)
    assert start_location.id == 1


def test_move():
    exit1 = Exit(Direction.NORTH, 2)
    exit2 = Exit(Direction.SOUTH, 1)
    location1 = Location(1, exits=[exit1])
    location2 = Location(2, exits=[exit2])
    dungeon = Dungeon(locations=[location1, location2])
    dungeon.set_start_location(1)

    new_location = dungeon.move(Direction.NORTH)
    assert new_location.id == 2

    new_location = dungeon.move(Direction.SOUTH)
    assert new_location.id == 1

    assert dungeon.move(Direction.EAST) is None


# --- Test Dungeon integrity ---


# --- SUCCESS conditions
def test_locations_have_exits():
    loc1 = Location(1, 10, 10, [Exit(Direction.NORTH, 2)])
    loc2 = Location(2, 10, 10, [Exit(Direction.SOUTH, 1)])
    dungeon = Dungeon("Test Dungeon", "A test description", [loc1, loc2])
    assert dungeon.validate_locations_have_exits()


def test_exits_have_valid_destinations():
    loc1 = Location(1, 10, 10, [Exit(Direction.NORTH, 2)])
    loc2 = Location(2, 10, 10, [Exit(Direction.SOUTH, 1)])
    dungeon = Dungeon("Test Dungeon", "A test description", [loc1, loc2])
    assert dungeon.validate_exits_have_valid_destinations()


def test_unique_exit_directions():
    loc1 = Location(1, 10, 10, [Exit(Direction.NORTH, 2), Exit(Direction.SOUTH, 3)])
    loc2 = Location(2, 10, 10, [Exit(Direction.SOUTH, 1)])
    loc3 = Location(3, 10, 10, [Exit(Direction.NORTH, 1)])
    dungeon = Dungeon("Test Dungeon", "A test description", [loc1, loc2, loc3])
    assert dungeon.validate_unique_exit_directions()


def test_no_island_locations():
    loc1 = Location(1, 10, 10, [Exit(Direction.NORTH, 2)])
    loc2 = Location(2, 10, 10, [Exit(Direction.SOUTH, 1), Exit(Direction.EAST, 3)])
    loc3 = Location(3, 10, 10, [Exit(Direction.WEST, 2)])
    dungeon = Dungeon("Test Dungeon", "A test description", [loc1, loc2, loc3])
    assert dungeon.validate_no_island_locations()


def test_no_island_locations_2():
    loc1 = Location(1, 10, 10, [Exit(Direction.NORTH, 2)])
    loc2 = Location(2, 10, 10, [Exit(Direction.SOUTH, 1), Exit(Direction.EAST, 3)])
    loc3 = Location(3, 10, 10, [Exit(Direction.NORTH, 4), Exit(Direction.WEST, 2)])
    loc4 = Location(4, 10, 10, [Exit(Direction.SOUTH, 3)])
    dungeon = Dungeon("Test Dungeon", "A test description", [loc1, loc2, loc3, loc4])
    assert dungeon.validate_no_island_locations()


# --- FAILURE conditions
def test_locations_have_exits_failure():
    loc1 = Location(1, 10, 10, [])
    dungeon = Dungeon("Test Dungeon", "A test description", [loc1])
    assert not dungeon.validate_locations_have_exits()


def test_exits_have_valid_destinations_failure():
    loc1 = Location(1, 10, 10, [Exit(Direction.NORTH, 999)])
    dungeon = Dungeon("Test Dungeon", "A test description", [loc1])
    assert not dungeon.validate_exits_have_valid_destinations()


def test_unique_exit_directions_failure():
    loc1 = Location(1, 10, 10, [Exit(Direction.NORTH, 2), Exit(Direction.NORTH, 3)])
    loc2 = Location(2, 10, 10, [Exit(Direction.SOUTH, 1)])
    loc3 = Location(3, 10, 10, [Exit(Direction.SOUTH, 1)])
    dungeon = Dungeon("Test Dungeon", "A test description", [loc1, loc2, loc3])
    assert not dungeon.validate_unique_exit_directions()


def test_no_island_locations_failure():
    # Location ID 2 is an island - there are exits TO it, but not FROM it.
    loc1 = Location(1, 10, 10, [Exit(Direction.NORTH, 2)])
    loc2 = Location(2, 10, 10, [Exit(Direction.NORTH, 3)])  # No exit back to 1
    loc3 = Location(3, 10, 10, [Exit(Direction.NORTH, 4)])  # No exit to ID 2
    loc4 = Location(4, 10, 10, [Exit(Direction.SOUTH, 3)])
    dungeon = Dungeon("Test Dungeon", "A test description", [loc1, loc2, loc3, loc4])
    assert not dungeon.validate_no_island_locations()


@pytest.mark.flaky(reruns=5)
def test_random_dungeon():
    # Create a random dungeon
    dungeon = get_random_dungeon()

    # Validate Dungeon
    assert dungeon.validate_location_connections()

from osrlib.dungeon import Dungeon, Location, Exit, Direction
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
    encounter = Encounter() # TODO: Set this up with real encounter
    location = Location(1, 10, 10, [exit_north], ["keyword1"], encounter)

    assert location.id == 1
    assert location.dimensions == {"width": 10, "length": 10}
    assert location.exits == [exit_north]
    assert location.keywords == ["keyword1"]
    assert location.encounter == encounter

# --- Test Dungeon class ---

def test_dungeon_initialization():
    exit_north = Exit(Direction.NORTH, 1)
    encounter = Encounter()  # You would set this up properly according to your Encounter class
    location1 = Location(1, 10, 10, [exit_north], ["keyword1"], encounter)
    location2 = Location(2, 6, 6, [], ["keyword2"], None)
    dungeon = Dungeon("Test Dungeon", "A test dungeon.", [location1, location2])

    assert dungeon.name == "Test Dungeon"
    assert dungeon.description == "A test dungeon."
    assert dungeon.locations == [location1, location2]

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
    loc2 = Location(2, 10, 10, [Exit(Direction.SOUTH, 3)]) # No exit back to ID 1
    loc3 = Location(3, 10, 10, [Exit(Direction.NORTH, 4)]) # No exit back to ID 2
    loc4 = Location(4, 10, 10, [Exit(Direction.SOUTH, 3)])
    dungeon = Dungeon("Test Dungeon", "A test description", [loc1, loc2, loc3, loc4])
    assert not dungeon.validate_no_island_locations()
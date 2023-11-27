import pytest
from osrlib.adventure import Adventure
from osrlib.dungeon import Location, Exit, Direction, Dungeon

@pytest.fixture
def setup_adventure():
    # Setup
    adventure = Adventure("Castle of the Copper Maiden")
    adventure.introduction = "In the secluded vale of  Lurimara, the palace of Duchess Elara stood tall, crafted from moonlit alabaster echoing the brilliance of winter's dawn. This land, filled with creatures of whispered legends, flourished under Elara's watchful eyes, and was particularly famed for its intricate artifacts and armaments, at the heart of which was a gleaming sapphire termed 'The Luminous Gem.' On an evening bathed in starlight, during a majestic carnival, envy took root amidst celebration. Although the palace boasted chambers painted in hues of crimson and azure, and a terrace granting views of enchanting flora and lustrous vines, it was 'The Luminous Gem' that ensnared every gaze. Rumors speak of mages and sprites, consumed by its beauty, orchestrating its disappearance. When dawn broke, the sapphire was lost, and  Lurimara's peace with it. Now, wyvern's silhouettes darken the skies, with tales of a solitary knight astride it, in pursuit of the lost treasure, echoing through time."

    loc_description_9  = ["small room", "hangers", "hooks", "chest", "drawers", "east wall"]
    loc_description_10 = ["bathing room", "scenes", "spring", "summer", "enamel", "oval bathtub", "towels", "vase", "red", "blue", "yellow"]
    loc_description_11 = ["massive beds", "three chairs", "huge south wall", "table", "fireplace", "food", "wine", "dishes"]
    loc_description_12 = ["small", "stool", "table", "north wall", "wheel", "south wall"]
    loc_description_13 = ["garden", "weeds", "paths", "underbrush", "statue", "vines", "water"]
    loc_description_14 = ["double doors", "wooden throne", "statues", "warriors", "columns", "fire places", "tapestries", "pomp", "feasts"]
    loc_description_15 = ["couches", "marble table", "marble bench", "fire place", "dust"]
    loc_description_16 = ["narrow bridge", "logs", "chasm", "bottomless", "water", "dripping", "no handrails", "slick", "moisture"]
    loc_description_17 = ["ornate fountain", "mermaid", "giant shell", "water", "blue glow", "cool", "refreshing"]
    loc_description_18 = ["iron cages", "exotic creature", "growl", "cower", "desk", "papers", "experiments"]
    loc_description_19 = ["circular platform", "center", "runes", "floor", "teleportation device"]
    loc_description_20 = ["giant mushrooms", "spores", "luminescent glow", "large fungi"]
    loc_description_21 = ["corridor", "archway"]
    loc_description_22 = ["young woman", "ceiling", "men", "swords", "hair", "U shaped table", "fireplace", "north wall"]
    loc_description_23 = ["empty room"]
    loc_description_24 = ["statue", "girl", "dove", "bookcase", "benches", "windows", "scrolls", "dead tree"]
    loc_description_25 = ["canopy bed", "curtains", "dresser", "chest of drawers", "easy chair", "rugs"]
    loc_description_26 = ["copper vats", "fire", "tubes", "wall", "liquid", "distilled"]
    loc_description_27 = ["high ceiling", "chains", "hooks", "meat", "faint odor"]
    loc_description_28 = ["wizard's study", "books", "bookshelves", "scrolls", "desk", "devices", "cage", "blue bird"]
    loc_description_29 = ["green moss", "walls", "pool", "water", "dripping sound"]
    loc_description_30 = ["statues", "humanoids", "poses", "fear", "horror", "lifelike", "stone"]
    loc_description_31 = ["quaint little room", "game table", "chess set", "large map", "wine decanter", "log", "fireplace", "chess pieces gold and silver plated", "pipe", "wine glass", "peacock fan"]


    dungeon = Dungeon("Castle of the Copper Maiden", "Upper level of the Copper Maiden's castle.")
    dungeon.add_location(Location(99, 10, 10, [Exit(Direction.NORTH, 9)], ["Randoville", "tavern", "The Beer and Whine"], None))
    dungeon.add_location(Location( 9, 20, 20, [Exit(Direction.NORTH, 10), Exit(Direction.SOUTH, 99)], [loc_description_9], None))
    dungeon.add_location(Location(10, 20, 20, [Exit(Direction.NORTH, 11), Exit(Direction.SOUTH,  9)], [loc_description_10], None))
    dungeon.add_location(Location(11, 20, 20, [Exit(Direction.SOUTH, 10), Exit(Direction.NORTH, 12)], [loc_description_11], None))
    dungeon.add_location(Location(12, 20, 20, [Exit(Direction.SOUTH, 11), Exit(Direction.WEST,  13)], [loc_description_12], None))
    dungeon.add_location(Location(13, 20, 20, [Exit(Direction.EAST,  12)],                            [loc_description_13], None))
    dungeon.add_location(Location(14, 30, 30, [Exit(Direction.WEST,  15)],                            [loc_description_14], None))
    dungeon.add_location(Location(15, 20, 20, [Exit(Direction.EAST,  14), Exit(Direction.WEST,  16)], [loc_description_15], None))
    dungeon.add_location(Location(16, 20, 20, [Exit(Direction.EAST,  15), Exit(Direction.NORTH, 17), Exit(Direction.SOUTH, 18)], [loc_description_16], None))
    dungeon.add_location(Location(17, 20, 20, [Exit(Direction.SOUTH, 16)],                            [loc_description_17], None))
    dungeon.add_location(Location(18, 20, 20, [Exit(Direction.NORTH, 16), Exit(Direction.WEST,  19)], [loc_description_18], None))
    dungeon.add_location(Location(19, 20, 20, [Exit(Direction.NORTH, 20), Exit(Direction.EAST,  18)], [loc_description_19], None))
    dungeon.add_location(Location(20, 20, 20, [Exit(Direction.SOUTH, 19)],                            [loc_description_20], None))
    dungeon.add_location(Location(21, 30, 20, [Exit(Direction.WEST,  22), Exit(Direction.NORTH, 23)], [loc_description_21], None))
    dungeon.add_location(Location(22, 20, 20, [Exit(Direction.EAST,  21)],                            [loc_description_22], None))
    dungeon.add_location(Location(23, 20, 30, [Exit(Direction.SOUTH, 21), Exit(Direction.WEST,  24)], [loc_description_23], None))
    dungeon.add_location(Location(24, 20, 30, [Exit(Direction.EAST,  23), Exit(Direction.WEST,  25)], [loc_description_24], None))
    dungeon.add_location(Location(25, 20, 30, [Exit(Direction.EAST,  24), Exit(Direction.WEST,  26)], [loc_description_25], None))
    dungeon.add_location(Location(26, 20, 20, [Exit(Direction.EAST,  25), Exit(Direction.SOUTH, 27)], [loc_description_26], None))
    dungeon.add_location(Location(27, 20, 30, [Exit(Direction.NORTH, 26), Exit(Direction.SOUTH, 28)], [loc_description_27], None))
    dungeon.add_location(Location(28, 20, 20, [Exit(Direction.NORTH, 27), Exit(Direction.WEST,  29)], [loc_description_28], None))
    dungeon.add_location(Location(29, 40, 40, [Exit(Direction.WEST,  30), Exit(Direction.EAST,  28)], [loc_description_29], None))
    dungeon.add_location(Location(30, 20, 20, [Exit(Direction.WEST,  31), Exit(Direction.EAST,  29)], [loc_description_30], None))
    dungeon.add_location(Location(31, 20, 20, [Exit(Direction.EAST,  30)],                            [loc_description_31], None))
    dungeon.set_start_location(99)

    adventure.add_dungeon(dungeon)
    adventure.set_active_dungeon(dungeon)

    yield adventure

    # Teardown
    adventure.end_adventure()

def test_adventure_dungeon_integrity(setup_adventure):
    assert setup_adventure.active_dungeon.validate_location_connections()
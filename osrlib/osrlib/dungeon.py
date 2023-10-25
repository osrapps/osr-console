from typing import List, Dict, Union
from enum import Enum
from osrlib.encounter import Encounter


class Direction(Enum):
    NORTH = "N"
    SOUTH = "S"
    EAST = "E"
    WEST = "W"
    UP = "U"
    DOWN = "D"


class Exit:
    def __init__(self, direction: Direction, destination: int, locked: bool = False):
        self.direction = direction
        self.destination = destination
        self.locked = locked

    def lock(self):
        self.locked = True

    def unlock(self):
        self.locked = False


class Location:
    """Represents a location of import within a ``Dungeon``."""

    def __init__(
        self,
        id: int,
        keywords: List[str],
        width: int,
        length: int,
        exits: List[Exit],
        encounter: Encounter = None,
    ):
        self.id = id
        self.dimensions = {"width": width, "length": length}
        self.keywords = keywords
        self.exits = exits
        self.encounter = encounter


class Dungeon:
    """Contains a collection of locations.

    You can use a ``Dungeon`` to represent a single dungeon or use several ``Dungeon``
    instances to represent multiple levels of a dungeon.

    Attributes:
        name (str): The name of the dungeon.
        description (str): The description of the dungeon (location, environment, etc.).
        locations (list): A list of the locations in the dungeon.
    """

    def __init__(
        self, name: str = None, description: str = None, locations: Location = []
    ) -> None:
        self.name = name
        self.description = description
        self.locations = locations

    pass

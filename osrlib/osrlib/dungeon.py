from typing import List
from enum import Enum
from osrlib import game_manager as gm
from osrlib.encounter import Encounter


class Direction(Enum):
    """Enumeration for directions a player can go within a location.

    Attributes:
        NORTH, SOUTH, EAST, WEST, UP, DOWN: Cardinal directions and vertical movements.
    """
    NORTH = "N"
    SOUTH = "S"
    EAST = "E"
    WEST = "W"
    UP = "U"
    DOWN = "D"


class Exit:
    """Represents an exit leading from one location to another within a dungeon.

    Attributes:
        direction (Direction): The direction of the exit. Each location can have only one exit per direction.
        destination (int): The ID of the destination location. Must exist within the dungeon.
        locked (bool): Indicates if the exit is locked or not.

    Example:
        >>> exit1 = Exit(Direction.NORTH, 2)
        >>> exit2 = Exit(Direction.SOUTH, 1)
        >>> exit1.lock()
        >>> exit2.unlock()
    """

    def __init__(self, direction: Direction, destination: int, locked: bool = False):
        self.direction = direction
        self.destination = destination
        self.locked = locked

    def lock(self):
        """Locks the exit."""
        self.locked = True

    def unlock(self):
        """Unlocks the exit."""
        self.locked = False

    def to_dict(self):
        return {
            'direction': self.direction.value,
            'destination': self.destination,
            'locked': self.locked
        }

    @classmethod
    def from_dict(cls, data):
        return cls(Direction(data['direction']), data['destination'], data['locked'])


class Location:
    """Represents a location of importance within a ``Dungeon``.

    Attributes:
        id (int): Unique identifier for the location. Must be unique within the dungeon.
        dimensions (dict): Dimensions of the location in a `{"width": int, "length": int}` format. Default dimensions are 10x10.
        exits (List[Exit]): List of exits leading to other locations. Each location must have at least one exit and each exit must have a unique direction.
        keywords (List[str]): Keywords associated with the location for search or identification.
        encounter (Encounter): An optional encounter that exists within this location.

    Example:
        >>> exit1 = Exit(Direction.NORTH, 2)
        >>> exit2 = Exit(Direction.SOUTH, 1)
        >>> location1 = Location(1, 10, 10, [exit1])
        >>> location2 = Location(2, 8, 8, [exit2], keywords=["treasure", "armory"])
        >>> dungeon = Dungeon("Example Dungeon", "An example dungeon.", [location1, location2])

        >>> # Validate the dungeon before proceeding with the game logic
        >>> if dungeon.validate_dungeon():
        >>>     print("Dungeon is valid.")
        >>> else:
        >>>     print("Dungeon is invalid.")
    """

    def __init__(
        self,
        id: int,
        width: int = 10,
        length: int = 10,
        exits: List[Exit] = [],
        keywords: List[str] = [],
        encounter: Encounter = None,
    ):
        self.id = id
        self.dimensions = {"width": width, "length": length}
        self.exits = exits
        self.keywords = keywords
        self.encounter = encounter

    def to_dict(self):
        return {
            'id': self.id,
            'dimensions': self.dimensions,
            'exits': [exit.to_dict() for exit in self.exits],
            'keywords': self.keywords,
            'encounter': self.encounter.to_dict() if self.encounter else None
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            data['id'],
            data['dimensions']['width'],
            data['dimensions']['length'],
            [Exit.from_dict(exit_data) for exit_data in data['exits']],
            data['keywords'],
            Encounter.from_dict(data['encounter']) if data['encounter'] else None
        )

class Dungeon:
    """Contains a collection of interconnected locations. Validates the integrity of these connections.

    Attributes:
        name (str): The name of the dungeon.
        description (str): A brief description providing context or history for the dungeon.
        locations (List[Location]): List of locations within the dungeon. A location must have at least one exit, and all exits must have valid destinations within the dungeon. No locations should be islands unless the dungeon only contains that single location.

    Example:
        >>> dungeon = Dungeon("Example Dungeon", "An example dungeon.", [location])
        >>> dungeon.validate_dungeon()
    """

    def __init__(
        self, name: str = None, description: str = None, locations: List[Location] = []
    ) -> None:
        self.name = name
        self.description = description
        self.locations = locations

    def validate_locations_have_exits(self) -> bool:
        """Checks if every location in the dungeon has at least one exit.

        Returns:
            bool: True if all locations have exits, False otherwise.
        """
        for loc in self.locations:
            if len(loc.exits) == 0:
                gm.logger.critical(f"Dungeon validation FAILED: Location with ID {loc.id} has no exits.")
                return False
        return True

    def validate_exits_have_valid_destinations(self) -> bool:
        """Checks if all exits in all locations have a valid destination.

        Returns:
            bool: True if all exits have valid destinations, False otherwise.
        """
        location_ids = {loc.id for loc in self.locations}
        for loc in self.locations:
            for exit in loc.exits:
                if exit.destination not in location_ids:
                    gm.logger.critical(f"Dungeon validation FAILED: Exit from location ID {loc.id} has an invalid destination ID {exit.destination}.")
                    return False
        return True

    def validate_unique_exit_directions(self) -> bool:
        """Checks if all locations have unique exit directions.

        Returns:
            bool: True if all locations have unique exit directions, False otherwise.
        """
        for loc in self.locations:
            directions = [exit.direction for exit in loc.exits]
            if len(directions) != len(set(directions)):
                gm.logger.critical(f"Dungeon validation FAILED: Location ID {loc.id} has duplicate exit directions.")
                return False
        return True

    def validate_no_island_locations(self) -> bool:
        """Checks that no locations are isolated.

        Returns:
            bool: True if no locations are islands, False otherwise.
        """
        if len(self.locations) == 1:
            return True  # Single location is valid

        location_ids = {loc.id for loc in self.locations}
        for loc_id in location_ids:
            accessible = {loc_id}
            to_visit = [loc_id]
            while to_visit:
                current_loc = to_visit.pop()
                for exit in [loc.exits for loc in self.locations if loc.id == current_loc][0]:
                    if exit.destination not in accessible:
                        accessible.add(exit.destination)
                        to_visit.append(exit.destination)

            if accessible != location_ids:
                gm.logger.critical(f"Dungeon validation FAILED: Location ID {loc_id} is an island.")
                return False
        return True

    def validate_dungeon(self) -> bool:
        """Runs all validation methods and logs any failures.

        Returns:
            bool: True if all validations pass, False otherwise.
        """
        validations = [
            ("Not all locations have exits.", self.validate_locations_have_exits),
            ("Not all exits have valid destinations.", self.validate_exits_have_valid_destinations),
            ("Two or more exits are in same direction.", self.validate_unique_exit_directions),
            ("One or more locations are islands.", self.validate_no_island_locations)
        ]

        for description, method in validations:
            if not method():
                gm.logger.critical(f"Dungeon validation FAILED: {description}")
                return False
        return True

    def to_dict(self):
        return {
            'name': self.name,
            'description': self.description,
            'locations': [location.to_dict() for location in self.locations]
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            data['name'],
            data['description'],
            [Location.from_dict(location_data) for location_data in data['locations']]
        )

from random import randint, sample
from typing import List
from enum import Enum
import json
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
        opposite_direction (Direction): The direction directly opposite this exit's direction. There is no contract that there is an exit in that direction.

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
        self.opposite_direction = self.set_opposite_direction(self.direction)

    def set_opposite_direction(self, direction) -> Direction:
        if direction == Direction.NORTH:
            return Direction.SOUTH
        elif direction == Direction.SOUTH:
            return Direction.NORTH
        elif direction == Direction.EAST:
            return Direction.WEST
        elif direction == Direction.WEST:
            return Direction.EAST
        elif direction == Direction.UP:
            return Direction.DOWN
        elif direction == Direction.DOWN:
            return Direction.UP

    def lock(self):
        """Locks the exit."""
        self.locked = True

    def unlock(self):
        """Unlocks the exit."""
        self.locked = False

    def to_dict(self):
        return {
            "direction": self.direction.value,
            "destination": self.destination,
            "locked": self.locked,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(Direction(data["direction"]), data["destination"], data["locked"])


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
        >>> location2 = Location(2, 8, 8, [exit2], keywords=["rust", "armory"])
        >>> dungeon = Dungeon("Example Dungeon", "An example dungeon.", [location1, location2])
        >>> # Validate the dungeon before proceeding with the game logic
        >>> dungeon.validate_dungeon()
        True
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
        # TODO: Add support for a has_been_visited flag to indicate if the party has already visited this location.

    def __str__(self):
        return f"Location ID: {self.id} Dimensions: {self.dimensions} Exits: {self.exits} Keywords: {self.keywords}"

    @property
    def json(self):
        """Returns a JSON representation of the location."""
        #json_location = json.dumps(self.to_dict(), default=lambda o: o.__dict__, indent=4)
        json_location = json.dumps(self.to_dict(), default=lambda o: o.__dict__, separators=(',', ':'))
        gm.logger.debug(f"Location JSON:\n{json_location}")
        return json_location

    def to_dict(self):
        return {
            "id": self.id,
            "dimensions": self.dimensions,
            "exits": [exit.to_dict() for exit in self.exits],
            "keywords": self.keywords,
            "encounter": self.encounter.to_dict() if self.encounter else None,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            data["id"],
            data["dimensions"]["width"],
            data["dimensions"]["length"],
            [Exit.from_dict(exit_data) for exit_data in data["exits"]],
            data["keywords"],
            Encounter.from_dict(data["encounter"]) if data["encounter"] else None,
        )


class LocationNotFoundError(Exception):
    """Raised when a location cannot be found in a dungeon."""

    pass


class Dungeon:
    """Contains a collection of interconnected locations. Validates the integrity of these connections.

    Attributes:
        name (str): The name of the dungeon.
        description (str): A brief description providing context or history for the dungeon.
        locations (List[Location]): List of locations within the dungeon. A location must have at least one exit, and all exits must have valid destinations within the dungeon. No locations should be islands unless the dungeon only contains that single location.

    Example:
        >>> location1 = Location(1, 10, 10, [Exit(Direction.NORTH, 2)], keywords=["rust", "armory"])
        >>> location2 = Location(2, 3, 40, [Exit(Direction.SOUTH, 1)], keywords=["cold", "corridor", "narrow"])
        >>> dungeon = Dungeon("Example Dungeon", "An example dungeon.", [location1, location2])
        >>> if dungeon.validate_dungeon():
        ...     start_location = dungeon.set_start_location(1)
        ...     new_location = dungeon.move(Direction.NORTH)
        ...     new_location.id
        2
    """

    def __init__(
        self,
        name: str = None,
        description: str = None,
        locations: List[Location] = [],
        start_location_id: int = None,
    ) -> None:
        self.name = name
        self.description = description
        self.locations = locations
        if start_location_id:
            self.set_start_location(start_location_id)
        else:
            self.current_location = None

    def set_start_location(self, location_id: int) -> Location:
        """Sets the starting location for the dungeon.

        Args:
            location_id (int): The ID of the location to set as the starting location.

        Returns:
            Location: The starting location.

        Raises:
            LocationNotFoundError: If the location ID does not exist in the dungeon.
        """
        gm.logger.debug(f"Setting starting location to location with ID {location_id}.")
        try:
            start_location = [loc for loc in self.locations if loc.id == location_id][0]
        except IndexError:
            gm.logger.exception(
                f"Location with ID {location_id} does not exist in the dungeon."
            )
            raise LocationNotFoundError(
                f"Location with ID {location_id} does not exist in the dungeon."
            )

        self.current_location = start_location
        gm.logger.debug(f"Starting location set to {start_location}.")

        return start_location

    def move(self, direction: Direction) -> Location:
        """Moves the party to the location in the specified direction if there's an exit in that direction.

        Example:
            >>> exit1 = Exit(Direction.NORTH, 2)
            >>> exit2 = Exit(Direction.SOUTH, 1)
            >>> location1 = Location(1, 10, 10, [exit1])
            >>> location2 = Location(2, 10, 10, [exit2], keywords=["rust", "armory"])
            >>> dungeon = Dungeon("Example Dungeon", "An example dungeon.", [location1, location2])
            >>> start_location = dungeon.set_start_location(1)
            >>> new_location = dungeon.move(Direction.NORTH)
            >>> dungeon.current_location.id == location2.id
            True

        Args:
            direction (Direction): The direction of the exit the party should move through.

        Returns:
            Location: The location the party moved to, or None if there is no exit in the specified direction.
        """
        gm.logger.debug(f"Moving party {direction.name} from {self.current_location}.")
        try:
            exit = [exit for exit in self.current_location.exits if exit.direction == direction][0]
        except IndexError:
            gm.logger.debug(
                f"No exit to the {direction.name} from {self.current_location}. The only exits are {self.current_location.exits}."
            )
            return None

        self.current_location = [loc for loc in self.locations if loc.id == exit.destination][0]
        gm.logger.debug(f"Party moved to {self.current_location}.")

        return self.current_location

    def validate_locations_have_exits(self) -> bool:
        """Checks if every location in the dungeon has at least one exit.

        Returns:
            bool: True if all locations have exits, False otherwise.
        """
        for loc in self.locations:
            if len(loc.exits) == 0:
                gm.logger.critical(
                    f"Dungeon validation FAILED: Location with ID {loc.id} has no exits."
                )
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
                    gm.logger.critical(
                        f"Dungeon validation FAILED: Exit from location ID {loc.id} has an invalid destination ID {exit.destination}."
                    )
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
                gm.logger.critical(
                    f"Dungeon validation FAILED: Location ID {loc.id} has duplicate exit directions."
                )
                return False
        return True

    def validate_no_island_locations(self) -> bool:
        """Checks that no locations are isolated or are one-way dead ends by using Depth-First Search (DFS).

        Each location must be part of a larger interconnected graph where it's
        possible to reach a location from at least one other location, and between
        which the reverse connection exists. That is, every location can be reached
        by some path, and every path can be traveled in reverse.

        Returns:
            bool: True if no locations are islands, False otherwise.
        """

        # Single location dungeons are valid by default.
        if len(self.locations) == 1:
            return True

        # Collect all location IDs.
        location_ids = {loc.id for loc in self.locations}

        # Iterate through each location to perform DFS.
        for loc_id in location_ids:
            # Set to keep track of accessible locations from the current 'loc_id'.
            accessible = {loc_id}

            # Stack for DFS traversal, initialized with the current 'loc_id'.
            to_visit = [loc_id]

            while to_visit:
                # Pop a location from stack.
                current_loc = to_visit.pop()

                # Find exits for the current location.
                current_exits = [
                    loc.exits for loc in self.locations if loc.id == current_loc
                ][0]

                for exit in current_exits:
                    # If the destination is not yet accessible, mark it and queue it for visit.
                    if exit.destination not in accessible:
                        accessible.add(exit.destination)
                        to_visit.append(exit.destination)

            # If some locations are not accessible from 'loc_id', it's an island.
            if accessible != location_ids:
                gm.logger.critical(
                    f"Dungeon validation FAILED: Location ID {loc_id} is an island."
                )
                return False

        return True

    def validate_dungeon(self) -> bool:
        """Runs all validation methods and logs any failures.

        Returns:
            bool: True if all validations pass, False otherwise.
        """
        validations = [
            ("Not all locations have exits.", self.validate_locations_have_exits),
            (
                "Not all exits have valid destinations.",
                self.validate_exits_have_valid_destinations,
            ),
            (
                "Two or more exits are in same direction.",
                self.validate_unique_exit_directions,
            ),
            ("One or more locations are islands.", self.validate_no_island_locations),
        ]

        for description, method in validations:
            if not method():
                gm.logger.critical(f"Dungeon validation FAILED: {description}")
                return False
        return True

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "locations": [location.to_dict() for location in self.locations],
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            data["name"],
            data["description"],
            [Location.from_dict(location_data) for location_data in data["locations"]],
        )

def get_random_dungeon():
    # Initialize empty list for locations
    locations = []

    # Generate 10 locations
    for i in range(1, 11):
        width = randint(1, 5) * 10  # Size between 10 and 50, in increments of 10
        height = randint(1, 5) * 10  # Size between 10 and 50, in increments of 10
        keywords = ["placeholder1", "placeholder2", "placeholder3"]

        # Generate random exits
        possible_directions = list(Direction)
        num_exits = randint(1, len(possible_directions))  # At least one exit
        directions = sample(possible_directions, num_exits)

        exits = []
        for direction in directions:
            destination = randint(1, 10)  # Random destination ID between 1 and 10
            while (
                destination == i
            ):  # Ensure destination is not the same as the location itself
                destination = randint(1, 10)
            exits.append(Exit(direction, destination))

        location = Location(i, width, height, exits, keywords)
        locations.append(location)

    # Ensure all locations are reachable from each other
    for loc in locations:
        for exit in loc.exits:
            dest_id = exit.destination
            dest_location = next((l for l in locations if l.id == dest_id), None)

            # Check if there's an exit back to the original location
            if not any(e.destination == loc.id for e in dest_location.exits):
                # Check if there is already an exit in the reverse direction to avoid duplicates
                if not any(
                    e.direction == exit.opposite_direction for e in dest_location.exits
                ):
                    dest_location.exits.append(Exit(exit.opposite_direction, loc.id))

    # Initialize Dungeon
    return Dungeon("Random Dungeon", f"A randomly generated dungeon with {len(locations)} locations.", locations)
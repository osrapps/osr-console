from typing import List
from enum import Enum
import random
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

    def __str__(self):
        return f"{self.direction.name}:{self.destination}{(':locked' if self.locked else '')}"

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


class ExitAlreadyExistsError(Exception):
    """Raised when trying to add an exit to a location, but an exit in that direction already exists."""

    pass


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
        is_visited: bool = False,
    ):
        self.id = id
        self.dimensions = {"width": width, "length": length}
        self.exits = exits
        self.keywords = keywords
        self.encounter = encounter
        self.is_visited = is_visited

    def __str__(self):
        exits_str = ", ".join(str(exit) for exit in self.exits)
        return f"Location ID: {self.id} Dimensions: {self.dimensions} Exits: [{exits_str}] Keywords: {self.keywords}"


    @property
    def json(self):
        """Returns a JSON representation of the location."""
        #json_location = json.dumps(self.to_dict(), default=lambda o: o.__dict__, indent=4)
        json_location = json.dumps(self.to_dict(), default=lambda o: o.__dict__, separators=(',', ':'))
        gm.logger.debug(f"Location JSON:\n{json_location}")
        return json_location

    def get_exit(self, direction: Direction):
        """Returns the exit in the specified direction, if it exists.

        Args:
            direction (Direction): The direction of the exit to return.

        Returns:
            Exit: The exit in the specified direction, or None if there is no exit in that direction.
        """
        return next((exit for exit in self.exits if exit.direction == direction), None)

    def add_exit(self, exit: Exit):
        """Adds an exit to the location.

        Args:
            exit (Exit): The exit to add to the location.

        Raises:
            ValueError: If an exit already exists in the same direction.
        """
        if self.get_exit(exit.direction):
            raise ExitAlreadyExistsError(
                f"An exit already exists in the {exit.direction.name} direction."
            )
        self.exits.append(exit)

    def to_dict(self):
        return {
            "id": self.id,
            "dimensions": self.dimensions,
            "exits": [exit.to_dict() for exit in self.exits],
            "keywords": self.keywords,
            "encounter": self.encounter.to_dict() if self.encounter else None,
            "is_visited": self.is_visited,
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
            data["is_visited"],
        )


class LocationNotFoundError(Exception):
    """Raised when a location cannot be found in a dungeon."""

    pass


class NoMatchingExitError(Exception):
    """Raised when an ``Exit`` in a ``Location`` doesn't have a corresponding ``Exit`` back to the source ``Location``."""

    pass



class DestinationLocationNotFoundError(Exception):
    """Raised when a destination ``Location`` of an ``Exit`` doesn't exist in the ``Dungeon``."""

    pass


class ReturnConnectionDestinationIncorrectError(Exception):
    """Raised when an ``Exit`` in a ``Location`` leads to a destination ``Location`` whose corresponding return ``Exit`` direction is correct, but its destination ``Location`` is incorrect."""

    pass


class LocationAlreadyExistsError(Exception):
    """Raised when trying to add a location to the dungeon's locations collection, but a location with the same ID already exists."""

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

    def add_location(self, location: Location) -> None:
        """Adds a location to the dungeon.

        Args:
            location (Location): The location to add to the dungeon.
        """
        if location.id not in [loc.id for loc in self.locations]:
            self.locations.append(location)
        else:
            exception = LocationAlreadyExistsError(
                f"Location with ID {location.id} already exists in the dungeon."
            )
            gm.logger.exception(exception)
            raise exception

    def get_location(self, location_id: int) -> Location:
        """Returns the location with the specified ID.

        Args:
            location_id (int): The ID of the location to return.

        Returns:
            Location: The location with the specified ID, otherwise None if the location with that ID doesn't exist.
        """
        return next((loc for loc in self.locations if loc.id == location_id), None)

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
                f"No exit to the {direction.name} from {self.current_location}. The only exits are: "
                + ", ".join(str(exit) for exit in self.current_location.exits) + "."
            )
            return None

        self.current_location = [loc for loc in self.locations if loc.id == exit.destination][0]

        if self.current_location.is_visited:
            gm.logger.debug(f"Party moved to previously visited location {self.current_location}.")
        else:
            gm.logger.debug(f"Party moved to new location {self.current_location}.")
            self.current_location.is_visited = True

        return self.current_location

    def validate_location_connections(self) -> bool:
        """Verifies whether every location in the dungeon is connected to at least one other location and that a connection in the opposite direction exists. For example, if location A has an exit EAST to location B, then location B must have an exit WEST to location A.

        Every location in a dungeon must be part of an interconnected graph where each "source" location has at least one
        exit leading a "destination" location in the dungeon. Each destination location must also have a corresponding
        exit in the opposite direction whose destination is the source location.

        Empty dungeons and those with only one location are considered valid.

        Returns:
            bool: True if all locations in the dungeon are connected by at least one bi-directional exit to another location, otherwise False.
        """
        # Empty dungeons and those with only one location are considered valid
        if len(self.locations) <= 1:
            return True

        validation_errors = []

        for src_loc in self.locations:
            for src_exit in src_loc.exits:

                # Exit must lead to existing destination Location
                dst_loc = self.get_location(src_exit.destination)
                if not dst_loc:
                    validation_error = DestinationLocationNotFoundError(
                        f"[L:{src_loc.id} {src_exit}] points to [L:{src_exit.destination}] which does NOT exist."
                    )
                    gm.logger.error(validation_error)
                    validation_errors.append(validation_error)

                # Destination location must have corresponding Exit whose destination is this Location
                return_exit = dst_loc.get_exit(src_exit.opposite_direction)
                if not return_exit:
                    validation_error = NoMatchingExitError(
                        f"[L:{src_loc.id} {src_exit}] return exit [L:{dst_loc.id} {src_exit.opposite_direction.name}:{src_loc.id}] does NOT exist."
                    )
                    gm.logger.error(validation_error)
                    validation_errors.append(validation_error)
                elif return_exit.destination != src_loc.id:
                    validation_error = ReturnConnectionDestinationIncorrectError(
                        f"[LOC:{src_loc.id} {src_exit}] return exit should be [L:{dst_loc.id} {src_exit.opposite_direction.name}:{src_loc.id}] not [L:{dst_loc.id} {return_exit}]."
                    )
                    gm.logger.error(validation_error)
                    validation_errors.append(validation_error)

        return len(validation_errors) == 0

    @staticmethod
    def get_random_dungeon(name: str = "Random Dungeon", description: str = "", num_locations: int = 10) -> "Dungeon":
        """Generates a random dungeon with the specified number of locations.

        Args:
            name (str): The name of the dungeon.
            description (str): A brief description providing context or history for the dungeon.
            num_locations (int): The number of locations to generate in the dungeon.

        Returns:
            Dungeon: A randomly generated dungeon with the specified number of locations.
        """
        if num_locations < 1:
            raise ValueError("Dungeon must have at least one location.")

        locations = []
        for i in range(1, num_locations + 1):
            length = random.choice([10, 20, 30, 40])
            width = random.choice([10, 20, 30, 40])
            locations.append(Location(id=i, exits=[], length=length, width=width))

        directions = [d for d in Direction if d not in (Direction.UP, Direction.DOWN)]

        for i in range(num_locations - 1):
            src = locations[i]
            dst = locations[i + 1]

            random.shuffle(directions)

            for direction in directions:
                if not src.get_exit(direction):
                    src_exit = Exit(direction, dst.id)
                    dst_return_exit = Exit(src_exit.opposite_direction, src.id)

                    gm.logger.debug(f"Adding L:{src.id} {src_exit}")
                    src.add_exit(src_exit)
                    gm.logger.debug(f"Adding L:{dst.id} {dst_return_exit}")
                    dst.add_exit(dst_return_exit)
                    break

        if description == "":
            description = f"A randomly generated dungeon with {num_locations} locations."

        return Dungeon(name, description, locations)

    def to_json(self):
        """Returns a JSON representation of the dungeon."""
        return json.dumps(self.to_dict(), default=lambda o: o.__dict__)

    def to_dict(self):
        """Returns a dictionary representation of the dungeon. Useful as a pre-serialization step when saving to a permanent data store."""
        return {
            "name": self.name,
            "description": self.description,
            "locations": [location.to_dict() for location in self.locations],
        }

    @classmethod
    def from_dict(cls, data):
        """Returns a ``Dungeon`` instance from a dictionary representation of the dungeon. Useful as a post-deserialization step when loading from a permanent data store."""
        return cls(
            data["name"],
            data["description"],
            [Location.from_dict(location_data) for location_data in data["locations"]],
        )
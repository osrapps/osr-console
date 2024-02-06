"""The `dungeon` module contains the [Dungeon][osrlib.dungeon.Dungeon], [Location][osrlib.dungeon.Location], and [Exit][osrlib.dungeon.Exit] classes, and some custom exceptions related to working with them.

A `Dungeon` contains one or more locations, each of which contains one or more exits leading to other locations in the
dungeon.

## Stock a dungeon

To create and stock a dungeon, a typical order of operations might be:

1. Create the [Location][osrlib.dungeon.Location] objects you'll add to a `Dungeon` you'll create in a later step.
2. Add [Exit][osrlib.dungeon.Exit] objects to the locations. Each location must be bidirectionally connected to at least
   one other location by an exit.
3. Create [Encounter][osrlib.encounter.Encounter] objects and add a [MonsterStatsBlock][osrlib.monster.MonsterStatsBlock]
   to the encounters that should result in battle (or, depending on the block's properties, the *chance* of a battle).
4. Add the encounters to the locations.
5. Create the [Dungeon][osrlib.dungeon.Dungeon] and add the locations to it.

Tip:
    Before you send a party in to explore a dungeon, ensure the party can navigate to its location by calling the
    dungeon's `validate_connection_locations()` method. Doing so returns a bool indicating whether the dungeon's
    locations are each bidirectionally connected to at least one other `Location`.


"""
from typing import List
import random, json, uuid
from openai import OpenAI
from osrlib.enums import Direction, OpenAIModelVersion
from osrlib.game_manager import logger
from osrlib.encounter import Encounter
from osrlib.dice_roller import roll_dice


class Exit:
    """Represents an exit leading from one [Location][osrlib.dungeon.Location] to another in a [Dungeon][osrlib.dungeon.Dungeon].

    An exit can be `locked`, which allows you to control access to its destination based on some condition. For
    example, you could require that one of the player's characters has a specific [Item][osrlib.item.Item] in their
    [Inventory][osrlib.inventory.Inventory] that acts as the "key" before allowing them to move to the exit's
    destination.

    Attributes:
        direction (Direction): The direction of the exit. Each location can have only one exit per direction.
        destination (int): The ID of the destination [Location][osrlib.dungeon.Location]. Must exist within the dungeon.
        locked (bool): Indicates if the exit is locked or not.
        opposite_direction (Direction): The direction directly opposite this exit's direction. There is **no** contract
                                        that guarantees a corresponding return exit exists in the destination location's
                                        exits collection.

    Example:
    ```python
    --8<-- "tests/test_unit_dungeon.py:dungeon_exit_create"
    ```
    """

    def __init__(self, direction: Direction, destination: int, locked: bool = False):
        """Creates an `Exit` in the given `Direction` and with the specified [Location][osrlib.dungeon.Location] ID as its destination.

        Args:
            direction (Direction): The direction in which the exit faces. For example, the wall the exit is on in a room
                                   or the direction in which a tunnel turns.
            destination (int): The ID of the [Location][osrlib.dungeon.Location] the exits leads to.
            locked (bool, optional): Whether the party is prevented from to going through the exit. Defaults to `False`.
        """
        self.direction = direction
        self.destination = destination
        self.locked = locked
        self.opposite_direction = self._set_opposite_direction(self.direction)

    def __str__(self) -> str:
        """Gets a string representation of the `Exit`.

        Returns:
            str: A human-readable string representation of the `Exit`.
        """
        return f"{self.direction.name}:{self.destination}{(':locked' if self.locked else '')}"

    def _set_opposite_direction(self, direction) -> Direction:
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
        """Serializes the `Exit` to a dictionary, typically in preparation for writing it to persistent storage in a downstream operation."""
        return {
            "direction": self.direction.value,
            "destination": self.destination,
            "locked": self.locked,
        }

    @classmethod
    def from_dict(cls, data):
        """Deserializes a dictionary representation of an `Exit` object. Typically done after getting the dictionary from persistent storage."""
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

    ```python
     >>> exit1 = Exit(Direction.NORTH, 2)
     >>> exit2 = Exit(Direction.SOUTH, 1)
     >>> location1 = Location(1, 10, 10, [exit1])
     >>> location2 = Location(2, 8, 8, [exit2], keywords=["rust", "armory"])
     >>> dungeon = Dungeon("Example Dungeon", "An example dungeon.", [location1, location2])
     >>> # Validate the dungeon before proceeding with the game logic
     >>> dungeon.validate_connection_locations()
     True
    ```
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
        """Creates an instance of a `Location`.

        Args:
            id (int): The ID of the `Location`; must be unique within a `Dungeon`.
            width (int, optional): The width of the location in feet.
            length (int, optional): The length of the location in feet.
            exits (List[Exit], optional): The collection of exits leading from the location.
            keywords (List[str], optional): The keywords that describe the location.
            encounter (Encounter, optional): An encounter the party can interact with when it arrives at the location.
            is_visited (bool, optional): Whether the party has previously been to the location.
        """
        self.id = id
        self.dimensions = {"width": width, "length": length}
        self.exits = exits
        self.keywords = keywords
        self.encounter = encounter
        self.is_visited = is_visited

    def __str__(self) -> str:
        """Gets a human-readable string representation of the `Location`.

        Returns:
            str: A string representation of the `Location`.
        """
        exits_str = ", ".join(str(exit) for exit in self.exits)
        return f"LOC ID: {self.id} Size: {str(self.dimensions['width'])}'W x {str(self.dimensions['length'])}'L Exits: [{exits_str}] Keywords: {self.keywords}"

    @property
    def json(self):
        """Returns a JSON representation of the location."""
        json_location = json.dumps(self.to_dict(), default=lambda o: o.__dict__, separators=(",", ":"))
        logger.debug(json_location)
        return json_location

    def get_exit(self, direction: Direction) -> Exit:
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
            raise ExitAlreadyExistsError(f"An exit already exists in the {exit.direction.name} direction.")
        self.exits.append(exit)

    def to_dict(self):
        """Serializes the `Location` to a dictionary, typically in preparation for writing it to persistent storage in a downstream operation."""
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
        """Deserializes a dictionary representation of a `Location` object. Typically done after getting the dictionary from persistent storage."""
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
    """Contains a collection of interconnected `Location` objects and can validate the integrity of those connections.

    Attributes:
        id (uuid.UUID): Unique identifier for the dungeon.
        name (str): The name of the dungeon.
        description (str): A brief description providing context or history for the dungeon.
        locations (List[Location]): List of locations within the dungeon. A location must have at least one exit, and all exits must have valid destinations within the dungeon. No locations should be islands unless the dungeon only contains that single location.

    Example:

    ```python
    >>> location1 = Location(1, 10, 10, [Exit(Direction.NORTH, 2)], keywords=["rust", "armory"])
    >>> location2 = Location(2, 3, 40, [Exit(Direction.SOUTH, 1)], keywords=["cold", "corridor", "narrow"])
    >>> dungeon = Dungeon("Example Dungeon", "An example dungeon.", [location1, location2])
    >>> if dungeon.validate_connection_locations():
    ...     start_location = dungeon.set_start_location(1)
    ...     new_location = dungeon.move(Direction.NORTH)
    ...     new_location.id
    2
    ```
    """

    def __init__(
        self,
        name: str = None,
        description: str = None,
        locations: List[Location] = [],
        start_location_id: int = None,
        id: str = str(uuid.uuid4()),
    ) -> None:
        """Creates an instance of a `Dungeon`.

        Args:
            name (str, optional): The name of the dungeon. Should be unique within an `Adventure`.
            description (str, optional): A description of the dungeon appropriate for display to the player.
            locations (List[Location], optional): The collection of locations within the dungeon.
            start_location_id (int, optional): The ID of the `Location` the `Party` should begin exploration of the
                                               dungeon. If you supply this argument, the `current_party_location` is set
                                               to this location automatically.
            id (str, optional): The ID of the dungeon; must be unique within the `Adventure`.
        """
        self.name = name
        self.description = description
        self.locations = locations
        self.current_party_location = self.set_start_location(start_location_id)
        self.party_is_exploring = False
        self.id = id

    def set_start_location(self, location_id: int) -> Location:
        """Sets the `Location` where `Party` starts exploring the dungeon if a location with the specified ID exists within the dungeon.

        If it exists, this method also sets the `current_party_location` to that location.

        Args:
            location_id (int): The ID of the `Location` where the party should begin their exploration of the dungeon.

        Returns:
            Location: The starting location if it exists, otherwise `None`.
        """
        logger.debug(f"Setting starting location to location with ID {location_id}.")
        self.start_location = self.get_location_by_id(location_id)
        if self.start_location:
            logger.debug(f"Starting location set to {self.start_location}.")
            self.current_party_location = self.start_location
            return self.start_location
        else:
            return None

    def add_location(self, location: Location) -> None:
        """Adds the location to the dungeon.

        Args:
            location (Location): The location to add to the dungeon.
        """
        if location.id not in [loc.id for loc in self.locations]:
            self.locations.append(location)
        else:
            exception = LocationAlreadyExistsError(f"Location with ID {location.id} already exists in the dungeon.")
            logger.exception(exception)
            raise exception

    def get_location_by_id(self, location_id: int) -> Location:
        """Get the location with the specified ID.

        Args:
            location_id (int): The ID of the location to return.

        Returns:
            Location: The location with the specified ID if it exists, otherwise `None`.
        """
        return next((loc for loc in self.locations if loc.id == location_id), None)

    def get_location_by_direction(self, location: Location, direction: Direction) -> Location:
        """Get the location in the specified direction from the given location.

        Args:
            location (Location): The location containing the exit whose destination should be returned.
            direction (Direction): The direction of the give location's exit whose destination should be returned.

        Returns:
            Location: The location that is the destination of the exit in the specified direction, otherwise `None` if there is no exit in that direction.
        """
        exit = location.get_exit(direction)
        if exit:
            return self.get_location_by_id(exit.destination)
        else:
            return None

    def move(self, direction: Direction) -> Location:
        """Moves the party to the location in the specified direction if there's an exit in that direction and sets the dungeon's current location to the new location.

        You should set the new location's `is_visited` attribute to `True` after you've completed any processing you like
        when the party arrives at a location for the first time.

        Example:

        An example of using the `is_visited` property is to present a detailed description of the location when a party
        arrives at a location with `is_visited == False' and a brief one-liner description on subsequent visits when
        `is_visited == true`.

        ```python
        >>> exit1 = Exit(Direction.NORTH, 2)
        >>> exit2 = Exit(Direction.SOUTH, 1)
        >>> location1 = Location(1, 10, 10, [exit1])
        >>> location2 = Location(2, 10, 10, [exit2], keywords=["rust", "armory"])
        >>> dungeon = Dungeon("Example Dungeon", "An example dungeon.", [location1, location2])
        >>> start_location = dungeon.set_start_location(1)
        >>> new_location = dungeon.move(Direction.NORTH)
        >>> if new_location:
        ...     if new_location.is_visited:
        ...         print(f"Party moved to previously visited location {new_location}.")
        ...     else:
        ...         print(f"The party moved to new location {new_location}, and here's a super detailed description...")
        ...         new_location.is_visited = True
        Party moved to new location LOC ID: 2 Size: 10'W x 10'L Exits: [NORTH:1] Keywords: ['rust', 'armory'], and here's a super detailed description...
        >>> dungeon.current_party_location == new_location
        True
        ```

        Args:
            direction (Direction): The direction of the exit the party should move through.

        Returns:
            Location: The location the party moved to if they were able to move in the specified direction, otherwise `None`.
        """
        new_location = self.get_location_by_direction(self.current_party_location, direction)
        if not new_location:
            logger.debug(
                f"No location {direction.name} of {self.current_party_location}. The only exits are: "
                + ", ".join(str(exit) for exit in self.current_party_location.exits)
                + "."
            )
            return None

        self.current_party_location = new_location

        # NOTE: We do NOT set is_visited to True here because we need to give the caller the opportunity to check and
        # perform any actions that need to be done when the party enters a location for the first time. They can then
        # set is_visited to True when they're done performing those actions.
        if self.current_party_location.is_visited:
            logger.debug(
                f"Party moved to previously visited (is_visited = True) location {self.current_party_location}."
            )
        else:
            logger.debug(f"Party moved to new (is_visited = False) location {self.current_party_location}.")

        return self.current_party_location

    def validate_location_connections(self) -> bool:
        """Verifies whether every [Location][osrlib.dungeon.Location] in the dungeon is connected to at least one other location and that a connection in the opposite direction exists. For example, if location A has an exit EAST to location B, then location B must have an exit WEST to location A.

        Every location in a dungeon must be part of an interconnected graph where each "source" location has at least one
        exit leading a "destination" location in the dungeon. Each destination location must also have a corresponding
        exit in the opposite direction whose destination is the source location.

        Empty dungeons and those with only one location are considered valid.

        Returns:
            bool: `True` if all locations in the dungeon are connected by at least one bi-directional exit to another location, otherwise `False`.
        """
        # Empty dungeons and those with only one location are considered valid
        if len(self.locations) <= 1:
            return True

        validation_errors = []

        for src_loc in self.locations:
            for src_exit in src_loc.exits:
                # Exit must lead to existing destination Location
                dst_loc = self.get_location_by_id(src_exit.destination)
                if not dst_loc:
                    validation_error = DestinationLocationNotFoundError(
                        f"[L:{src_loc.id} {src_exit}] points to [L:{src_exit.destination}] which does NOT exist."
                    )
                    logger.error(validation_error)
                    validation_errors.append(validation_error)

                # Destination location must have corresponding Exit whose destination is this Location
                return_exit = dst_loc.get_exit(src_exit.opposite_direction)
                if not return_exit:
                    validation_error = NoMatchingExitError(
                        f"[L:{src_loc.id} {src_exit}] return exit [L:{dst_loc.id} {src_exit.opposite_direction.name}:{src_loc.id}] does NOT exist."
                    )
                    logger.error(validation_error)
                    validation_errors.append(validation_error)
                elif return_exit.destination != src_loc.id:
                    validation_error = ReturnConnectionDestinationIncorrectError(
                        f"[LOC:{src_loc.id} {src_exit}] return exit should be [L:{dst_loc.id} {src_exit.opposite_direction.name}:{src_loc.id}] not [L:{dst_loc.id} {return_exit}]."
                    )
                    logger.error(validation_error)
                    validation_errors.append(validation_error)

        return len(validation_errors) == 0

    @staticmethod
    def _get_location_keywords_from_llm(
        dungeon: "Dungeon",
        openai_model: OpenAIModelVersion = OpenAIModelVersion.DEFAULT,
    ) -> str:
        """Get the keywords for each `Location` in the dungeon from the OpenAI API.

        Provided a `Dungeon`, gets a list of keywords for its locations from the OpenAI API. The list of keywords for
        each location are formatted as a JSON collection and returned to the caller. The OpenAI language model uses the
        description of the dungeon as context when generating the keywords so that they make sense in the context of the
        dungeon's description and the other locations' keywords.

        Returns:
            str: JSON string obtained from the OpenAI API containing a collection of the dungeon's locations and their
                 keywords.
        """
        system_message = [
            {
                "role": "system",
                "content": "You are the Dungeon Creator component in a turn-based RPG. You help adventurers picture the "
                "locations they visit iin the game world. You will be provided a dungeon's name and description as well "
                "as the number of locations in the dungeon. Your task is "
                "to generate three single keywords describing each location in the dungeon. Your response must be in "
                "in JSON. Maintain the theme of the dungeon and always consider previous location's keywords, especially "
                "those of adjacent locations. Adjacent integers typically represent adjacent locations, and their "
                "keywords should reflect a logical architectual relationship. The JSON response should be a collection "
                "of key-value pairs where the key is the location ID and the value is the collection of keywords for "
                "that location. The JSON must include keywords for every location and no two locations should share "
                "keywords. You should only include keywords that describe characteristics of the physical environment. "
                "Use single keywords. These keywords are banned and you should not include them or any form of them: "
                "whisper, drip, monster, echo, stairs, staircase, door, treasure, cursed, enchanted, sinister, "
                "ominous, mysterious, forgotten, creepy, stairway",
            },
        ]
        user_message = [
            {
                "role": "user",
                "content": f"{dungeon.name}\n{dungeon.description}\n{len(dungeon.locations)}",
            },
        ]
        logger.debug(f"Getting keywords for dungeon '{dungeon.name}' from OpenAI API...")

        client = OpenAI()
        openai_model = openai_model.value

        completion = client.chat.completions.create(
            model=openai_model,
            response_format={"type": "json_object"},
            messages=system_message + user_message,
        )
        llm_response = completion.choices[0].message.content

        decoded_json_string = bytes(llm_response, "utf-8").decode("unicode_escape").strip('"')
        logger.debug(f"Keywords for dungeon {dungeon.name} from OpenAI API: {decoded_json_string}")
        return decoded_json_string

    @staticmethod
    def get_random_dungeon(
        name: str = "Random Dungeon",
        description: str = "",
        num_locations: int = 10,
        level: int = 1,
        openai_model: OpenAIModelVersion = OpenAIModelVersion.DEFAULT,
    ) -> "Dungeon":
        """Generates a random dungeon with the specified number of locations.

        Args:
            name (str): The name of the dungeon.
            description (str): A brief description providing context or history for the dungeon.
            num_locations (int): The number of locations to generate in the dungeon.
            level (int): The level of the dungeon. Determines the hit die (and thus the difficulty) of monsters in encounters in the dungeon.
            openai_model (OpenAIModelVersion): The OpenAI model to use when generating keywords for the locations in the dungeon.

        Returns:
            Dungeon: A randomly generated dungeon with the specified number of locations, each with a random size and
                     possibly containing an [Encounter][osrlib.encounter.Encounter].

        Examples:
        ```python
        --8<-- "tests/test_unit_dungeon.py:dungeon_get_random_no_keywords"
        ```

        ```python
        --8<-- "tests/test_unit_dungeon.py:dungeon_get_random_with_ai_keywords"
        ```
        """
        if num_locations < 1:
            raise ValueError("Dungeon must have at least one location.")

        locations = []
        # Set a random room size
        for i in range(1, num_locations + 1):
            length = random.choice([10, 20, 30, 40])
            width = random.choice([10, 20, 30, 40])

            location = Location(id=i, exits=[], length=length, width=width)

            # Roll 1d6 to check for wandering monsters (1-2 on 1d6)
            if roll_dice("1d6").total <= 2:
                encounter = Encounter.get_random_encounter(level)
                location.encounter = encounter
                logger.debug(f"Added {encounter} to {location}.")

            locations.append(location)

        # Only want to connect locations in the cardinal directions for random dungeons
        directions = [d for d in Direction if d not in (Direction.UP, Direction.DOWN)]

        # Connect the locations with random exits
        for i in range(num_locations - 1):
            src = locations[i]
            dst = locations[i + 1]

            random.shuffle(directions)

            for direction in directions:
                if not src.get_exit(direction):
                    src_exit = Exit(direction, dst.id)
                    dst_return_exit = Exit(src_exit.opposite_direction, src.id)

                    logger.debug(f"Adding L:{src.id} {src_exit}")
                    src.add_exit(src_exit)
                    logger.debug(f"Adding L:{dst.id} {dst_return_exit}")
                    dst.add_exit(dst_return_exit)
                    break

        if description == "":
            description = f"A randomly generated dungeon with {num_locations} locations."

        dungeon = Dungeon(name, description, locations, start_location_id=1)

        Dungeon._populate_location_keywords(dungeon, openai_model)

        return dungeon

    @staticmethod
    def _populate_location_keywords(dungeon: "Dungeon", openai_model: OpenAIModelVersion = OpenAIModelVersion.NONE):
        """Populates each location in the dungeon with keywaords obtained from the OpenAI API.

        Args:
            dungeon (Dunegon): The `Dungeon` whose locations should be populated with keyords.
            openai_model (OpenAIModelVersion): The version of the OpenAI model to use when generating keywords.
        """
        if openai_model is not OpenAIModelVersion.NONE:
            location_keywords_json = Dungeon._get_location_keywords_from_llm(dungeon, openai_model)
            location_keywords_dict = json.loads(location_keywords_json)
            for location_id_str, keywords in location_keywords_dict.items():
                location_id = int(location_id_str)
                location = dungeon.get_location_by_id(location_id)
                if location:
                    location.keywords = keywords

    def to_json(self) -> str:
        """Gets a JSON string representation of the `Dungeon` instance.

        This method uses the `to_dict` method to first convert the dungeon instance into a
        dictionary, which is then serialized into a JSON string using `json.dumps`. ]]

        Returns:
            str: A JSON string representation of the dungeon instance.

        Example:
        ```python
        --8<-- "tests/test_unit_dungeon.py:dungeon_to_from_json"
        ```
        """
        return json.dumps(self.to_dict(), default=lambda o: o.__dict__)


    def to_dict(self) -> dict:
        """Returns a dictionary representation of the dungeon. Useful as a pre-serialization step when saving to a permanent data store."""
        return {
            "name": self.name,
            "description": self.description,
            "locations": [location.to_dict() for location in self.locations],
            "start_location_id": self.current_party_location.id,  # save the current location as the start location on load
            "id": self.id,
        }

    @classmethod
    def from_dict(cls, data):
        """Returns a `Dungeon` instance from a dictionary representation of the dungeon. Useful as a post-deserialization step when loading from a permanent data store."""
        return cls(
            data["name"],
            data["description"],
            [Location.from_dict(location_data) for location_data in data["locations"]],
            data["start_location_id"],  # will be the location that was current when the dungeon was saved
            data["id"],
        )

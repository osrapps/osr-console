"""The `adventure` module provides the [Adventure][osrlib.adventure.Adventure] class, which represents a scenario to be played through by the adventuring [Party][osrlib.party.Party].

The `Adventure` class is intended to encapsulate a set of thematically related dungeons and quests the player's
`Party` can explore and complete. It's the thing a game game designer would typically present as a
cohesive story or portion of a story for the player to experience.

Classes:
    Adventure: Manages the `Dungeon` and `Quest` collections in a game scenario and the progress of the player's `Party` through the scenario.
    DungeonNotFoundError: Raised for missing dungeons.
    DungeonAlreadyExistsError: Raised for duplicate dungeon additions.
"""
import json, os, datetime
from osrlib.utils import logger
from osrlib.dungeon import Dungeon
from osrlib.party import Party
from osrlib.quest import Quest
from osrlib.utils import get_data_dir_path, create_dir_tree_if_not_exist


class DungeonNotFoundError(Exception):
    """Exception raised when a given dungeon isn't in the adventure's list of dungeons."""

    pass


class DungeonAlreadyExistsError(Exception):
    """Exception raised when a given dungeon already exists in the adventure's list of dungeons."""

    pass


class Adventure:
    """An `Adventure`has a collection of dungeons that can be played through and quests that can be completed by a party of characters.

    To start an adventure, add a ``Party`` to the adventure with ``set_active_party`` and then call ``start_adventure``.
    Once you've started an adventure, you can't add or remove the party or its characters until you call ``end_adventure``
    or all the characters in the party have been killed.

    Only one party can play through (be added to) an adventure at a time.

    Attributes:
        name (str): The name of the adventure.
        short_description (str): A short description of the adventure.
        introduction (str): A longer introduction in the form typically found in the beginning of a module.
        dungeons (list): A list of the dungeons in the adventure.
        quests (list): A list of the quests in the adventure.
        party (Party): The party playing through the adventure.
    """

    def __init__(
        self,
        name: str,
        description: str = "",
        introduction: str = "",
        dungeons: list = [],
        quests: list = [],
    ):
        self.name = name
        self.description = description
        self.introduction = introduction
        self.dungeons = dungeons if dungeons is not None else []
        self.quests = quests if quests is not None else []
        self.active_party = None
        self.active_dungeon = None
        self.is_started = False

    def add_dungeon(self, dungeon: Dungeon):
        """Add a dungeon to the adventure.

        Args:
            dungeon (Dungeon): The dungeon to add to the adventure.

        Raises:
            DungeonAlreadyExistsError: If the dungeon already exists in the adventure.
        """
        if dungeon in self.dungeons:
            logger.error(f"Dungeon {dungeon.name} already exists in the adventure.")
            raise DungeonAlreadyExistsError(
                f"Dungeon {dungeon.name} already exists in the adventure."
            )
        self.dungeons.append(dungeon)
        logger.debug(f"Added dungeon {dungeon.name} to adventure {self.name}.")

    def set_active_dungeon(self, dungeon: Dungeon):
        """Set the active dungeon for the adventure.

        The active dungeon is the dungeon that the party is currently exploring.

        Args:
            dungeon (Dungeon): The dungeon to set as active.

        Raises:
            DungeonNotFoundError: If the dungeon isn't in the adventure.
        """
        if dungeon not in self.dungeons:
            logger.error(f"Dungeon {dungeon.name} is not in the adventure.")
            raise DungeonNotFoundError(
                f"Dungeon {dungeon.name} is not in the adventure."
            )
        self.active_dungeon = dungeon
        logger.debug(f"Active dungeon set to {dungeon.name}.")

    def set_active_party(self, party):
        """Set the party of player characters that will play through the adventure.

        Args:
            party (Party): The adventuring party for the adventure.
        """
        self.active_party = party
        logger.debug(f"Active adventuring party set to {party.name}.")

    def start_adventure(self):
        """Start the adventure.

        Call this method only after you've added a party to the adventure and set the active dungeon.
        """
        self.is_started = True
        logger.debug(f"Started adventure {self.name}.")

    def to_dict(self) -> dict:
        """Convert the adventure to a dict.

        Returns:
            dict: A dict representation of the adventure.
        """
        adventure_dict = {
            "name": self.name,
            "description": self.description,
            "introduction": self.introduction,
            "dungeons": [dungeon.to_dict() for dungeon in self.dungeons],
            "active_dungeon": self.active_dungeon.to_dict(),
            "active_party": self.active_party.to_dict(),
            # "quests": [quest.to_dict() for quest in self.quests],
        }
        return adventure_dict

    @classmethod
    def from_dict(cls, adventure_dict):
        name = adventure_dict["name"]
        description = adventure_dict["description"]
        introduction = adventure_dict["introduction"]
        dungeons = [
            Dungeon.from_dict(dungeon_dict)
            for dungeon_dict in adventure_dict["dungeons"]
        ]
        # quests = [Quest.from_dict(quest_dict) for quest_dict in adventure_dict["quests"]] # TODO: Implement quests

        # Create the Adventure instance with the list of rehydrated dungeons
        adventure_from_dict = cls(name, description, introduction, dungeons)

        # Find and set the active dungeon by matching it with one of the rehydrated dungeons
        active_dungeon_id = adventure_dict["active_dungeon"]["id"]
        active_dungeon = next(
            (dungeon for dungeon in dungeons if dungeon.id == active_dungeon_id), None
        )
        if active_dungeon:
            adventure_from_dict.set_active_dungeon(active_dungeon)
        else:
            raise DungeonNotFoundError(
                f"Active dungeon with ID {active_dungeon_id} not found in the adventure."
            )

        # Set the active party
        active_party = Party.from_dict(adventure_dict["active_party"])
        adventure_from_dict.set_active_party(active_party)

        return adventure_from_dict

    def end_adventure(self):
        """End the adventure.

        Call this method when the adventure is over.
        """
        self.is_started = False
        logger.debug(f"Ended adventure {self.name}.")

    def save_adventure(self, file_path: str = None) -> str:
        """
        Saves the adventure to a JSON file.

        Args:
            file_path (str, optional): The path where the file will be saved.
                                       If None, saves in the default data directory.

        Returns:
            str: The path where the file was saved.

        Raises:
            OSError: If the file cannot be written.
        """
        adventure_data = self.to_dict()
        json_data = json.dumps(adventure_data, indent=4)

        if file_path is None:
            now = datetime.datetime.now()
            timestamp = now.strftime("%Y%m%d_%H%M%S") # YYYYMMDD_HHMMSS
            filename = f"{self.name}_{timestamp}.json".replace(" ", "_").lower()
            save_dir = get_data_dir_path("osrlib") / "adventures"
            create_dir_tree_if_not_exist(save_dir)
            file_path = save_dir / filename

        try:
            with open(file_path, "w") as file:
                file.write(json_data)
            logger.debug(f"Adventure saved to {file_path}")
        except OSError as e:
            logger.error(f"Failed to save adventure to {file_path}: {e}")
            raise

        return str(file_path)

    @staticmethod
    def load_adventure(file_path: str = None) -> "Adventure":
        """
        Loads the adventure from a JSON file.

        Args:
            file_path (str): The path of the file to load the adventure from.

        Returns:
            Adventure: An instance of the Adventure class loaded from the file.

        Raises:
            FileNotFoundError: If the specified file does not exist.
            PermissionError: If there are issues with file access permissions.
            json.JSONDecodeError: If the file content is not valid JSON.
            Exception: For any other issues that may occur.
        """
        try:
            with open(file_path, "r") as file:
                adventure_data = json.load(file)
            logger.debug(f"Adventure loaded from {file_path}")
            return Adventure.from_dict(adventure_data)
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            raise
        except PermissionError:
            logger.error(f"Permission denied: {file_path}")
            raise
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in file: {file_path}")
            raise
        except Exception as e:
            logger.error(f"Error loading adventure from {file_path}: {e}")
            raise
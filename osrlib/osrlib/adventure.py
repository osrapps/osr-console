from osrlib.game_manager import logger
from osrlib.dice_roller import DiceRoll, roll_dice
from osrlib.dungeon import Dungeon
from osrlib.quest import Quest


class DungeonNotFoundError(Exception):
    """Exception raised when a given dungeon isn't in the adventure's list of dungeons."""

    pass


class DungeonAlreadyExistsError(Exception):
    """Exception raised when a given dungeon already exists in the adventure's list of dungeons."""

    pass


class Adventure:
    """An Adventure is a collection of dungeons that can be played through by a party of characters.

    To start an adventure, add a party to the adventure and then call `start_adventure()`. Once an adventure has started,
    you can't add or remove the party or its characters until you call `end_adventure()` or the all characters in the
    party have been killed.

    Only one party can play through an adventure at a time.

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
        dungeons: list = [Dungeon],
        quests: list = [Quest],
    ):
        self.name = name
        self.description = description
        self.introduction = introduction
        self.dungeons = dungeons
        self.quests = quests
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
        logger.debug(f"Set active dungeon to {dungeon.name}.")


    def set_active_party(self, party):
        """Set the party of player characters that will play through the adventure.

        Args:
            party (Party): The adventuring party for the adventure.
        """
        self.party = party
        logger.debug(f"Set adventuring party to {party.name}.")

    def start_adventure(self):
        """Start the adventure.

        Call this method only after you've added a party to the adventure and set the active dungeon.
        """
        self.is_started = True
        logger.debug(f"Started adventure {self.name}.")

    def end_adventure(self):
        """End the adventure.

        Call this method when the adventure is over.
        """
        self.is_started = False
        logger.debug(f"Ended adventure {self.name}.")
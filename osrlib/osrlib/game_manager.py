"""The GameManager module provides the main API surface for the game."""
from enum import Enum
import json
import logging
import warnings
import logging
import queue
import threading


class LastMessageHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.last_message = None

    def emit(self, record):
        self.last_message = self.format(record)

    def format(self, record):
        # Return only the message part of the log record
        return record.getMessage()

# Configure logging
logging.basicConfig(
    format="%(asctime)s [%(levelname)s][%(module)s::%(funcName)s] %(message)s",
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
last_message_handler = LastMessageHandler()
logger.addHandler(last_message_handler)


class StorageType(Enum):
    JSON = "json"
    YAML = "yaml"
    TOML = "toml"


class GameManager:
    """The GameManager class provides facilities for working with parties and their adventures. It's the main API entry point for the game.

    Access the GameManager singleton via the `game_manager.game_manager` module-level variable.

    Example:

        >>> from osrlib import game_manager, adventure
        >>> gm = game_manager.game_manager
        >>> gm.parties.append(Party("The B-Team"))
        >>> search_for_the_unknown = adventure.Adventure("Search for the Unknown")
        >>> gm.start_adventure(search_for_the_unknown, gm.parties[0])


    Attributes:
        parties (list): A list of the available parties.
        adventures (list): A list of the available adventures.
    """

    def __init__(
        self,
        parties: list = [],
        adventures: list = [],
    ):
        logger.debug("Initializing the GameManager...")
        self.adventures = adventures
        self.parties = parties
        logger.debug(
            f"GameManager initialized. There are {len(self.adventures)} adventures available."
        )

    def save_game(self, storage_type: StorageType = StorageType.JSON):
        """Save the game state to persistent storage in the given format.

        Args:
            storage_type (StorageType): The format to use for saving the game state.
        """
        logger.debug(
            f"Saving the game to persistent storage in {storage_type} format..."
        )
        if storage_type == StorageType.JSON:
            with open("game_manager.json", "w") as f:
                json.dump({"parties": self.parties, "adventures": self.adventures}, f)
        else:
            warnings.warn(f"Storage type {storage_type} not yet supported.")

    def load_game(self):
        """Load the game state from disk."""
        warnings.warn("Game LOAD is not yet implemented.", UserWarning)


game_manager = GameManager()
"""This module-level variable is the main API entry point for the game - use it instead of instantiating a new GameManager."""

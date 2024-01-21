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


class GameManager:
    """The GameManager class provides facilities for working with parties and their adventures.

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
            f"GameManager initialized."
        )

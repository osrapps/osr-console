from osrlib.game_manager import logger
from osrlib.dice_roller import DiceRoll, roll_dice
from osrlib.dungeon import Dungeon
from osrlib.quest import Quest


class Adventure:
    """An Adventure is a collection of dungeons that can be played through by a party of characters.

    To start an adventure, add a party to the adventure and then call `start_adventure()`. Once an adventure has started,
    you can't add or remove the party or its characters until you call `end_adventure()` or the all characters in the
    party have been killed.

    Only one party can play through an adventure at a time.

    Attributes:
        name (str): The name of the adventure.
        short_description (str): A short description of the adventure.
        long_description (str): A long description of the adventure.
        dungeons (list): A list of the dungeons in the adventure.
        quests (list): A list of the quests in the adventure.
        party (Party): The party playing through the adventure.
    """

    def __init__(
        self, name: str, short_description: str = "", long_description: str = "", dungeons: list = [Dungeon], quests: list = [Quest]
    ):
        self.name = name
        self.short_description = short_description
        self.long_description = long_description
        self.dungeons = dungeons
        self.quests = quests
        self.party = None

from osrlib.game_manager import logger


class AdventureAlreadyStartedError(Exception):
    """Raised when attempting to start an adventure that has already been started."""

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
        long_description (str): A long description of the adventure.
        dungeons (list): A list of the dungeons in the adventure.
        quests (list): A list of the quests in the adventure.
        party (Party): The party playing through the adventure.
        is_started (bool): Whether the adventure has started.
    """

    def __init__(
        self, name: str, short_description: str = "", long_description: str = "", dungeons: list = [], quests: list = []
    ):
        self.name = name
        self.short_description = short_description
        self.long_description = long_description
        self.dungeons = dungeons
        self.quests = quests
        self.party = None
        self.is_started = False

    def start_adventure(self, party: "Party"):
        """Add a party to the adventure and start the adventure.

        Once the adventure has started, you can't add or remove the adventuring party, and the party can't be added to
        any other adventures.

        Args:
            party (Party): The party of characters who'll play through the adventure.

        Raises:
            AdventureAlreadyStartedError: If the adventure has already been started.
        """
        logger.info(f"The party '{party.name}' is starting Adventure '{self.name}'...")
        if self.is_started:
            raise AdventureAlreadyStartedError(f"This adventure ('{self.name}') has already been started.")

        if self.party is not None:
            raise AdventureAlreadyStartedError(f"This adventure ('{self.name}') already has a party assigned to it.")

        self.party = party
        self.is_started = True
        logger.info(f"Party '{party.name}' has started Adventure '{self.name}'.")


class Dungeon:
    """Contains a collection of encounters.

    The encounters in a dungeon can represent a location like a room or cavern and can contain monsters, traps, treasure,
    and quest pieces.

    Attributes:
        name (str): The name of the dungeon.
        description (str): The description of the dungeon (location, environment, etc.).
        encounters (list): A list of the encounters in the dungeon.
    """

    pass


class Encounter:
    """An encounter represents a location like a room or cavern and can contain monsters, traps, treasure, and quest pieces.

    Attributes:
        name (str): The name or ID of the encounter.
        description (str): The description of the encounter (location, environment, etc.).
        monsters (list): A list of the monsters in the encounter.
        traps (list): A list of the traps in the encounter.
        treasure (list): A list of the treasure in the encounter. The treasure can be any item like weapons, armor, quest pieces, or gold pieces (or gems or other valuables).
    """

    pass


class Monster:
    """A Monster is a creature the party can encounter in a dungeon and defeat to obtain experience points and optionally treasure.

    Attributes:
        name (str): The name of the monster.
        monster_type (MonsterType): The type of monster (DEMON, DRAGON, HUMANOID, MAGICAL, UNDEAD, etc.)
        description (str): The monster's description.
        hit_dice (str): The hit dice of the monster in NdN format, like "1d8" or "2d6".
        hit_points (int): The number of hit points the monster has.
        weapon (Weapon): The weapon that the monster uses for attacks.
        armor_class (int): The armor class of the monster.
        treasure (list): A list of the treasure that the monster is carrying. The treasure can be any item like weapons, armor, quest pieces, or gold pieces (or gems or other valuables).
    """

    pass


class Quest:
    """Stub class for Quest."""

    pass


class QuestPiece:
    """Stub class for QuestPiece."""

    pass

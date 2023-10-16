"""The Party module contains the Party class and functions related to managing a party of player characters (collection
of type PlayerCharacter)."""

from typing import List

from osrlib import player_character, game_manager as gm
from osrlib.adventure import Adventure, AdventureAlreadyStartedError
from osrlib.character_classes import CharacterClassType


class PartyAtCapacityError(Exception):
    """Raised when attempting to add a player character to a party that already has the maximum number of members."""

    pass


class CharacterAlreadyInPartyError(Exception):
    """Raised when attempting to add a player character to a party that already has that character as a member.

    Example:
        Before trying to add a character to a party, check whether the character is already in the party by using the in
        operator:

        .. code-block:: python
            if not party.is_member(some_new_character):
                party.add_character(some_new_character)
    """

    pass


class CharacterNotInPartyError(Exception):
    """Raised when attempting to remove a player character from a party that does not have the character as a member.

    Example:
        Before trying to remove a character from a party, check whether the character is in the party by using the ``in``
        operator:

        .. code-block:: python
            if character in party:
            party.remove_character(character)
    """

    pass


class PartyInStartedAdventureError(Exception):
    """Raised when attempting to modify a party's roster when the party is in an adventure that's already been started."""

    pass


class Party:
    """Manages a collection of player characters (PCs) that comprise an adventuring party.

    If the party has been added to an adventure and the adventure has been started, you can't modify the party roster by
    adding or removing characters.

    Args:
        name (str): The name of the party.
        max_party_members (int): The maximum number of characters allowed in the party. Defaults to 6.
        characters (List[PlayerCharacter]): The characters in the party. Defaults to an empty list.

    Attributes:
        name (str): The name of the party.
        max_party_members (int): The maximum number of characters allowed in the party.
        characters (List[PlayerCharacter]): The characters in the party.
        active_character (PlayerCharacter): The currently active, or selected, character in the party.
        is_adventuring (bool): Whether the party has been added to an Adventure that has been started.
        current_adventure (Adventure): The adventure the party is currently in, or None if the party is not in an
            adventure.
    """

    def __init__(
        self,
        name: str,
        max_party_members: int = 6,
        characters: List[player_character.PlayerCharacter] = None,
    ):
        """Initialize a new Party instance."""
        self.name = name
        self.max_party_members = max_party_members
        self.characters = characters if characters is not None else []
        self.active_character = None
        self.current_adventure = None

    def __str__(self):
        """Get a string representation of the Party instance.

        Returns:
            str: A string representation of the Party instance.
        """
        return f"Party: {self.name}"

    @property
    def num_characters(self) -> int:
        """Get the number of characters in the party.

        Returns:
            int: The number of characters in the party.
        """
        return len(self.characters)

    @property
    def is_adventuring(self) -> bool:
        """Returns True if the party has been added to an adventure that has been started.

        Returns:
            bool: True if the party has been added to an adventure that has been started.
        """
        return self.current_adventure is not None and self.current_adventure.is_started

    @property
    def is_alive(self) -> bool:
        """Returns True if any character in the party is alive.

        Returns:
            bool: True if any character in the party is alive.
        """
        return any(character.is_alive for character in self.characters)

    def create_character(
        self, name: str, character_class: CharacterClassType, level: int = 1
    ) -> player_character.PlayerCharacter:
        """Initialize a new character, add them to the party, set as the active character for the party, and return the
        character.

        Example:
            Create a new character and add them to the party:

            .. code-block:: python
                party.create_character("Sckricko", character_classes.CharacterClassType.FIGHTER, 1)

        Args:
            name (str): The name of the character.
            character_class (character_classes.CharacterClassType): The character's class.
            level (int): The character's level. Defaults to 1.

        Returns:
            player_character.PlayerCharacter: The character that was created and added to the party.

        Raises:
            PartyInStartedAdventureError: If the party has been added to an adventure that has already been started.
        """
        if self.is_adventuring:
            raise PartyInStartedAdventureError(
                f"Can't create a new character in the party because the party is already adventuring."
            )

        character = player_character.PlayerCharacter(name, character_class, level)
        self.add_character(character)
        return character

    def add_character(
        self,
        character: player_character.PlayerCharacter,
        set_as_active_character: bool = True,
    ):
        """Add a character to the party.

        A character can be added to a party only once, and a party has a maximum number of characters.

        Example:
            Add a character to a party and allow them to be set as the active character:

            .. code-block:: python
                fighter = player_character.PlayerCharacter("Sckricko", character_classes.CharacterClassType.FIGHTER, 1)
                thief = player_character.PlayerCharacter("Slick", character_classes.CharacterClassType.THIEF, 1)
                party.add_character(fighter)  # sets the character as active for the party character by default
                party.add_character(thief, set_as_active_character=False)  # don't set the character as active for the
                                                                        # party
                if party.active_character == fighter:
                    print(f"Character '{character.name}' is the active character in the party.")

        Args:
            character (PlayerCharacter): The PC to add to the party.

        Raises:
            CharacterAlreadyInPartyError: If the character is already in the party.
            PartyAtCapacityError: If the party already has the maximum number of characters.

        Returns:
            PlayerCharacter: The character that was added to the party.
        """
        if self.is_adventuring:
            raise PartyInStartedAdventureError(
                f"Can't add '{character.name}' to the party because the party is already adventuring."
            )

        if len(self.characters) >= self.max_party_members:
            raise PartyAtCapacityError(
                f"Party cannot have more than {self.max_party_members} characters."
            )

        if character in self.characters:
            raise CharacterAlreadyInPartyError(
                f"Character '{character.name}' already in party."
            )

        if character.name in (character.name for character in self.characters):
            raise CharacterAlreadyInPartyError(
                f"A character with that name ('{character.name}') is already in party."
            )

        gm.logger.info(f"Adding '{character.name}' to party '{self.name}'...")
        self.characters.append(character)

        if set_as_active_character:
            gm.logger.info(
                f"Setting '{character.name}' as the active character in party '{self.name}'..."
            )
            self.set_active_character(character)

        return character

    def is_member(self, character: player_character.PlayerCharacter) -> bool:
        """Returns True if the character is in the party.

        Example:

            Check whether a character is in the party:

            .. code-block:: python
                if party.is_member(some_player_character):
                    print(f"{some_player_character.name} is in the party.")
                else:
                    print(f"{some_player_character.name} is not in the party.")

        Args:
            character (player_character.PlayerCharacter): The character to check for.

        Returns:
            bool: True if the character is in the party, False otherwise.
        """
        return character in self.characters

    def set_active_character(self, character: player_character.PlayerCharacter):
        """Sets the given character as the active, or "selected," character in the party.

        The character must be a member of the party before you can set them as the active character.

        Args:
            character (player_character.PlayerCharacter): The party member to set as the active or currently selected character

        Raises:
            CharacterNotInPartyError: Raised if the character is not in the party.
        """
        if self.is_member(character):
            self.active_character = character
            gm.logger.info(
                f"Set '{character.name}' as the active character in the party."
            )
        else:
            raise CharacterNotInPartyError(
                f"Character '{character.name}' not in party."
            )

    def remove_character(self, character: player_character.PlayerCharacter):
        """Removes a character from the party.

        Example:
        .. code-block:: python
            try:
                party.remove_character(character)
            except CharacterNotInPartyError:
                print(f"Character '{character.name}' wasn't in the party and thus be removed from it.")

        Args:
            character (player_character.PlayerCharacter): The PC to remove from the party.
        """
        if self.is_member(character):
            self.characters.remove(character)
        else:
            raise CharacterNotInPartyError(
                f"Character '{character.name}' not in party."
            )

    def get_character_by_name(self, name: str) -> player_character.PlayerCharacter:
        """Get a character from the party by name or None if the character is not in the party.

        Example:

                .. code-block:: python
                    character = party.get_character_by_name("Sckricko")
                    if character is not None:
                        print(f"Character '{character.name}' has {character.hit_points} hit points.")

        Args:
            name (str): The name of the character to return.

        Returns:
            player_character.PlayerCharacter: The character with the given name or None if the character is not in the party.
        """
        return next(
            (character for character in self.characters if character.name == name),
            None,
        )

    def get_character_by_index(self, index: int) -> player_character.PlayerCharacter:
        """Get a character from the party by index, or None if there's no character at that index.

        Example:

            .. code-block:: python
                if len(party.characters) > 0:
                    # Get the first character in the party
                    first_character = party.get_character_by_index(0)

                    # Get the last character in the party
                    last_character = party.get_character_by_index(-1)

        Args:
            index (int): The index of the character to return.

        Returns:
            player_character.PlayerCharacter: The character with the given index, or None if the index is out of range.
        """
        try:
            return self.characters[index]
        except IndexError:
            return None

    def get_character_index(self, character: player_character.PlayerCharacter) -> int:
        """Get the index of a character in the party.

        Example:

                Get the index of a character in the party without checking whether the character is in the party (not
                recommended):

                .. code-block:: python
                    character = party.get_character_by_name("Sckricko")
                    if party.is_member(character):
                        index = party.get_character_index(character)
                        print(f"Character '{character.name}' is number {index + 1} in the party's marching order.")

        Args:
            character (player_character.PlayerCharacter): The character to get the index of

        Returns:
            int: The index of the character in the party.

        Raises:
            CharacterNotInPartyError: If the character is not in the party.
        """
        if not self.is_member(character):
            raise CharacterNotInPartyError(
                f"Character '{character.name}' not in party."
            )

        return self.characters.index(character)

    def move_character_to_index(
        self, character: player_character.PlayerCharacter, index: int
    ):
        """Moves a character to a new slot in the in party's marching order.

        Use this method to adjust the marching order of the party.

        Example:

            .. code-block:: python
                # Move a character from fourth in line (index 3) to the front of the party at index 0.
                character = party.get_character_by_name("Sckricko")
                if party.is_member(character):
                    party.move_character_to_index(character, 0)

        Args:
            character (player_character.PlayerCharacter): The character to move.
            index (int): The index to move the character to.

        Raises:
            CharacterNotInPartyError: If the character is not in the party.
            IndexError: If the index is out of range.
        """
        if not self.is_member(character):
            raise CharacterNotInPartyError(
                f"Can't move '{character.name}' because they're not in the party."
            )

        if index >= len(self.characters):
            raise IndexError(
                f"Can't move '{character.name}' to index {index} because it's out of range."
            )

        # Don't move the character if they're already at the index.
        if index == self.get_character_index(character):
            return

        self.characters.remove(character)
        self.characters.insert(index, character)

    def clear_party(self):
        """Removes all characters from the party."""
        self.characters.clear()

    def start_adventure(self, adventure: Adventure):
        """Add the party to an adventure and starts the adventure.

        Once the adventure has started, you can't add or remove the adventuring party, and the party can't be added to
        any other adventures.

        Args:
            adventure (Adventure): The adventure to start.

        Raises:
            AdventureAlreadyStartedError: If the adventure has already been started.
        """
        if adventure.is_started:
            raise AdventureAlreadyStartedError(
                f"Adventure '{adventure.name}' has already been started."
            )

        adventure.start_adventure(self)
        self.current_adventure = adventure
        gm.logger.info(
            f"Started adventure '{adventure.name}' with party '{self.name}'."
        )


def get_default_party():  # pragma: no cover
    """Get a party of six (6) first-level characters: a Fighter, Elf, Dwarf, Thief, Halfling, and Magic User.

    Returns:
        Party: A party with six (6) player characters at first level (zero experience points).
    """
    party = Party("Six Player Characters")
    party.create_character("Sckricko", CharacterClassType.FIGHTER, 1)
    party.create_character("Mazpar", CharacterClassType.ELF, 1)
    party.create_character("Blarg The Destructor", CharacterClassType.DWARF, 1)
    party.create_character("Slick", CharacterClassType.THIEF, 1)
    party.create_character("Dimp Beefeeder", CharacterClassType.HALFLING, 1)
    party.create_character("Merlin", CharacterClassType.MAGIC_USER, 1)
    return party

"""The Party module contains the Party class and functions related to managing a party of player characters (collection
of type PlayerCharacter)."""

from typing import List

from osrlib.player_character import PlayerCharacter
from osrlib.game_manager import logger
from osrlib.enums import CharacterClassType
from osrlib.item_factories import equip_party
from osrlib.dice_roller import roll_dice


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
        characters: List[PlayerCharacter] = None,
    ):
        """Initialize a new Party instance."""
        self.name = name
        self.max_party_members = max_party_members
        self.members = characters if characters is not None else []
        self.active_character = None
        self.current_adventure = None
        # TODO: Marching order (two or three abreast)
        self.is_surprised = False

    def __str__(self):
        """Get a string representation of the Party instance, including its name and members.

        Returns:
            str: A string representation of the Party instance.
        """
        character_strs = [str(character) for character in self.members]
        character_list_str = '\n\t'.join(character_strs)

        return f"Party: {self.name}\nMembers:\n\t[{character_list_str}]"

    @property
    def num_characters(self) -> int:
        """Get the number of characters in the party.

        Returns:
            int: The number of characters in the party.
        """
        return len(self.members)

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
        return any(character.is_alive for character in self.members)

    def create_character(
        self, name: str, character_class: CharacterClassType, level: int = 1
    ) -> PlayerCharacter:
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
            PlayerCharacter: The character that was created and added to the party.

        Raises:
            PartyInStartedAdventureError: If the party has been added to an adventure that has already been started.
        """
        if self.is_adventuring:
            raise PartyInStartedAdventureError(
                f"Can't create a new character in the party because the party is already adventuring."
            )

        character = PlayerCharacter(name, character_class, level)
        self.add_character(character)
        return character

    def add_character(
        self,
        character: PlayerCharacter,
        set_as_active_character: bool = True,
    ):
        """Add a character to the party.

        A character can be added to a party only once, and a party has a maximum number of characters.

        Example:
            Add a character to a party and allow them to be set as the active character:

            .. code-block:: python
                fighter = PlayerCharacter("Sckricko", character_classes.CharacterClassType.FIGHTER, 1)
                thief = PlayerCharacter("Slick", character_classes.CharacterClassType.THIEF, 1)
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

        if len(self.members) >= self.max_party_members:
            raise PartyAtCapacityError(
                f"Party cannot have more than {self.max_party_members} characters."
            )

        if character in self.members:
            raise CharacterAlreadyInPartyError(
                f"Character '{character.name}' already in party."
            )

        if character.name in (character.name for character in self.members):
            raise CharacterAlreadyInPartyError(
                f"A character with that name ('{character.name}') is already in party."
            )

        logger.info(f"Adding '{character.name}' to party '{self.name}'...")
        self.members.append(character)

        if set_as_active_character:
            logger.info(
                f"Setting '{character.name}' as the active character in party '{self.name}'..."
            )
            self.set_active_character(character)

        return character

    def is_member(self, character: PlayerCharacter) -> bool:
        """Returns True if the character is in the party.

        Example:

            Check whether a character is in the party:

            .. code-block:: python
                if party.is_member(some_player_character):
                    print(f"{some_name} is in the party.")
                else:
                    print(f"{some_name} is not in the party.")

        Args:
            character (PlayerCharacter): The character to check for.

        Returns:
            bool: True if the character is in the party, False otherwise.
        """
        return character in self.members

    def set_active_character(self, character: PlayerCharacter):
        """Sets the given character as the active, or "selected," character in the party.

        The character must be a member of the party before you can set them as the active character.

        Args:
            character (PlayerCharacter): The party member to set as the active or currently selected character

        Raises:
            CharacterNotInPartyError: Raised if the character is not in the party.
        """
        if self.is_member(character):
            self.active_character = character
            logger.info(
                f"Set '{character.name}' as the active character in the party."
            )
        else:
            raise CharacterNotInPartyError(
                f"Character '{character.name}' not in party."
            )

    def remove_character(self, character: PlayerCharacter):
        """Removes a character from the party.

        Example:
        .. code-block:: python
            try:
                party.remove_character(character)
            except CharacterNotInPartyError:
                print(f"Character '{character.name}' wasn't in the party and thus be removed from it.")

        Args:
            character (PlayerCharacter): The PC to remove from the party.
        """
        if self.is_member(character):
            self.members.remove(character)
        else:
            raise CharacterNotInPartyError(
                f"Character '{character.name}' not in party."
            )

    def get_character_by_name(self, name: str) -> PlayerCharacter:
        """Get a character from the party by name or None if the character is not in the party.

        Example:

                .. code-block:: python
                    character = party.get_character_by_name("Sckricko")
                    if character is not None:
                        print(f"Character '{character.name}' has {character.hit_points} hit points.")

        Args:
            name (str): The name of the character to return.

        Returns:
            PlayerCharacter: The character with the given name or None if the character is not in the party.
        """
        return next(
            (character for character in self.members if character.name == name),
            None,
        )

    def get_character_by_index(self, index: int) -> PlayerCharacter:
        """Get a character from the party by index, or None if there's no character at that index.

        Example:

            .. code-block:: python
                if len(party.members) > 0:
                    # Get the first character in the party
                    first_character = party.get_character_by_index(0)

                    # Get the last character in the party
                    last_character = party.get_character_by_index(-1)

        Args:
            index (int): The index of the character to return.

        Returns:
            PlayerCharacter: The character with the given index, or None if the index is out of range.
        """
        try:
            return self.members[index]
        except IndexError:
            return None

    def get_character_index(self, character: PlayerCharacter) -> int:
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
            character (PlayerCharacter): The character to get the index of

        Returns:
            int: The index of the character in the party.

        Raises:
            CharacterNotInPartyError: If the character is not in the party.
        """
        if not self.is_member(character):
            raise CharacterNotInPartyError(
                f"Character '{character.name}' not in party."
            )

        return self.members.index(character)

    def move_character_to_index(
        self, character: PlayerCharacter, index: int
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
            character (PlayerCharacter): The character to move.
            index (int): The index to move the character to.

        Raises:
            CharacterNotInPartyError: If the character is not in the party.
            IndexError: If the index is out of range.
        """
        if not self.is_member(character):
            raise CharacterNotInPartyError(
                f"Can't move '{character.name}' because they're not in the party."
            )

        if index >= len(self.members):
            raise IndexError(
                f"Can't move '{character.name}' to index {index} because it's out of range."
            )

        # Don't move the character if they're already at the index.
        if index == self.get_character_index(character):
            return

        self.members.remove(character)
        self.members.insert(index, character)

    def clear_party(self):
        """Removes all characters from the party."""
        self.members.clear()

    def grant_xp(self, xp: int):
        """Divide and award experience points to the living characters in the party.

        Example:

            Award experience points to the living characters in the party:

            .. code-block:: python
                party.award_xp(100)

        Args:
            xp (int): The number of experience points to award to each character in the party.
        """
        # Divided XP evenly among all living members of the party
        xp_per_character = xp // len(self.get_living_members())
        for character in self.get_living_members():
            character.grant_xp(xp_per_character)
            logger.debug(f"Awarded {xp_per_character} experience points to {character}.")

    def get_surprise_roll(self) -> int:
        """Rolls a 1d6 and returns the result for the party's surprise roll."""
        roll = roll_dice("1d6")
        logger.debug(f"Player party rolled {roll} for surprise and got {roll.total_with_modifier}.")
        return roll.total_with_modifier

    def get_living_members(self) -> List[PlayerCharacter]:
        """Returns a list of all living members of the party.

        Returns:
            List[PlayerCharacter]: A list of all living members of the party.
        """
        return [character for character in self.members if character.is_alive]

    def to_dict(self):
        party_dict = {
            "characters": [character.to_dict() for character in self.members],
            "name": self.name,
        }
        return party_dict

    @classmethod
    def from_dict(cls, party_dict):
        characters_from_dict = [
            PlayerCharacter.from_dict(character_dict)
            for character_dict in party_dict["characters"]
        ]
        name = party_dict["name"]
        return cls(name, characters=characters_from_dict)

def get_default_party(party_name: str = "Default Party") -> Party:  # pragma: no cover
    """Get a party of six (6) first-level characters: a Fighter, Elf, Dwarf, Thief, Halfling, and Magic User.

    Returns:
        Party: A party with six (6) player characters at first level (zero experience points).
    """
    party = Party(party_name)
    party.create_character("Sckricko", CharacterClassType.FIGHTER, 1)
    party.create_character("Mazpar", CharacterClassType.ELF, 1)
    party.create_character("Blarg The Destructor", CharacterClassType.DWARF, 1)
    party.create_character("Slick", CharacterClassType.THIEF, 1)
    party.create_character("Dimp Beefeeder", CharacterClassType.HALFLING, 1)
    party.create_character("Merlin", CharacterClassType.MAGIC_USER, 1)

    equip_party(party)

    return party

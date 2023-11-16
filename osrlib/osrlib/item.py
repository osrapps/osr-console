"""Classes that represent items in the game and player character (PC) inventory."""
from enum import Enum
from typing import Optional, Set

from osrlib.enums import CharacterClassType


class ItemType(Enum):
    """Enumerates the types of items in the game.

    The item type determines whether the item can be used by a player character (PC) and, if so, whether it can be
    equipped by the PC.
    """

    ARMOR = ("Armor", "Armor, helmet, gloves, or boots")
    WEAPON = ("Weapon", "Bladed, blunt, or ranged weapon")
    SPELL = ("Spell", "Spell or scroll")
    EQUIPMENT = ("Equipment", "Piece of adventurers' equipment")
    MAGIC_ITEM = (
        "Magic item",
        "Potion, ring, or other item imbued with magical properties",
    )
    ITEM = ("Normal item", "Normal (non-magical) item")


class ItemAlreadyHasOwnerError(Exception):
    """Exception raised when an item already has an owner."""

    pass


class ItemAlreadyInInventoryError(Exception):
    """Exception raised when trying to add an item to a player character's (PC) inventory already in the inventory."""

    pass


class ItemEquippedError(Exception):
    """Exception raised when trying to equip an item the player character (PC) already has equipped."""

    pass


class ItemNotEquippedError(Exception):
    """Exception raised when trying to unequip an item the player character (PC) doesn't have equipped."""

    pass


class ItemNotInInventoryError(Exception):
    """Exception raised when trying to remove an item from a player character's (PC) inventory that's not in the inventory."""

    pass


class ItemNotUsableError(Exception):
    """Exception raised when trying to use an item that the player character (PC) can't use.

    The inability to use an item is typically due to a character class restriction. For example, a magic user can't use
    a sword and a thief can't wear plate mail armor."""

    pass


class ItemAlreadyInQuestError(Exception):
    """Exception raised when trying to assign an item to a quest that's already been assigned to a quest."""

    pass


class Item:
    """An item represents a piece of equipment, a weapon, spell, quest piece, any other item that can be owned by a player character (PC).

    You can specify that an item can be equipped by a PC and that more than one of that item type can be equipped.

    Any item can be marked as a quest piece by setting its quest attribute. Quest pieces are items required to be
    obtained as part of a quest. An item can be both a quest piece and usable by a PC, for example, an enchanted (or cursed!) sword or magic ring.

    Attributes:
        name (str): Name of the item.
        item_type (ItemType): Type of the item. Defaults to ItemType.ITEM.
        owner (Optional[PlayerCharacter]): The owner of the item.
        usable_by_classes (Set[CharacterClassType]): Classes that can use the item.
        max_equipped (int): Max number of this item that can be equipped.
        is_equipped (bool): Whether the item is currently equipped.
        gp_value (int): The value of the item in gold pieces (gp).
        quest (Optional[Quest]): The quest that the item is a part of.

    Example:
        >>> usable_by = {CharacterClassType.FIGHTER, CharacterClassType.THIEF}
        >>> item = Item("Sword", ItemType.WEAPON, usable_by, max_equipped=1, gp_value=10)
    """

    def __init__(
        self,
        name: str,
        item_type: ItemType = ItemType.ITEM,
        usable_by_classes: Optional[Set[CharacterClassType]] = None,
        max_equipped: int = 0,
        gp_value: int = 0,
        quest: Optional["Quest"] = None,
    ):
        """Initialize an item with the specified properties.

        Don't call the methods on this class directory. Instead, use a PlayerCharacter's InventoryManager (pc.inventory)
        to add/remove this item from a PC's inventor or add it to a Quest.

        Args:
            name (str): Name of the item.
            item_type (ItemType): Type of the item.
            usable_by_classes (Set[CharacterClassType]): Classes that can use the item.
            max_equipped (int, optional): Max number that can be equipped. Defaults to 0.
            gp_value (int, optional): Value of the item in gold pieces (gp). Defaults to 0.
            quest (Optional[Quest], optional): The quest that the item is a part of. Defaults to None.
        """
        self.name = name
        self.item_type = item_type
        self.owner = None
        self.usable_by_classes = (
            usable_by_classes if usable_by_classes is not None else set()
        )
        self.max_equipped = max_equipped
        self.gp_value = gp_value
        self.is_equipped = False
        if quest is not None:
            self._set_quest(quest)

    def __str__(self):
        return f"{self.name} ({self.item_type.name})"

    def _set_owner(self, player_character: "PlayerCharacter"):
        """Sets the owner of the item to the specified player character.

        Args:
            pc (PlayerCharacter): The player character to set as the owner.
        """
        self.owner = player_character

    def _set_quest(self, quest: "Quest"):
        """Sets the quest the item is a part of.

        When this and the other items in the quest are obtained (the item's owner is set), the quest is completed.

        Args:
            quest (Quest): The quest that the item is a part of.
        """
        if self.quest is not None:
            raise ItemAlreadyInQuestError(
                f"Item '{self.name}' already been assigned to quest '{quest.name}'."
            )
        self.quest = quest

    @property
    def is_usable_by_owner(self) -> bool:
        """Whether the item is usable by its owner.

        The item is usable if the owner is not None and the owning player character's class is in the set of classes in
        the item's usable_by_classes attribute. If the item is usable and also has a max_equipped value greater than 0,
        it can be equipped.

        Returns:
            bool: True if the CharacterClassType of the owning PlayerCharacter can use the item, otherwise False.
        """
        if self.owner is None:
            return False
        return self.owner.character_class.class_type in self.usable_by_classes

    @property
    def is_equipable(self) -> bool:
        """Whether the item is equipable by its owner.

        Returns:
            bool: True if the item is usable by the owner's character class and at least one of the item can be
            equipped, otherwise False.
        """
        if self.is_usable_by_owner and self.max_equipped > 0:
            return True
        return False

    @property
    def is_quest_piece(self) -> bool:
        """Whether the item is a quest piece.

        This is a convenience property that checks whether the item's quest attribute is not None.

        Returns:
            bool: True if the item is associated with a quest, otherwise False.
        """
        return self.quest is not None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "item_type": self.item_type.value[
                0
            ],  # Store only the first element of the tuple
            "usable_by_classes": [
                cls.value for cls in self.usable_by_classes
            ],  # Assuming CharacterClassType is an Enum
            "max_equipped": self.max_equipped,
            "is_equipped": self.is_equipped,
            "gp_value": self.gp_value,
            # TODO: serialize quest attribute (or ID or ...?)
            #'quest': self.quest.name if self.quest else None  # Assuming Quest has a name attribute
        }

    @classmethod
    def from_dict(cls, item_dict: dict) -> "Item":
        item_type = ItemType(
            next(filter(lambda x: x.value[0] == item_dict["item_type"], ItemType))
        )  # Convert back to Enum
        usable_by_classes = {
            CharacterClassType(value) for value in item_dict["usable_by_classes"]
        }  # Convert back to Enum Set

        item = cls(
            item_dict["name"],
            item_type,
            usable_by_classes,
            item_dict["max_equipped"],
            item_dict["gp_value"],
            # TODO: deserialize quest attribute
            # Quest(item_dict['quest']) if item_dict.get('quest') else None
        )
        item.is_equipped = item_dict["is_equipped"]

        return item


class Armor(Item):
    """An Armor item modifies the armor class (AC) of a player character (PC).

    Inherits all attributes from the Item class and introduces an additional attribute for AC modification.

    The bonus of any non-cursed magic armor or shield is subtracted from the character's AC. For example, a fighter
    wearing plate mail armor and using a shield (but with no Dexterity modifier) has an AC of 2. If the fighter uses a
    shield + 1, their AC = 1.

    Attributes:
        ac_modifier (int): Armor class (AC) bonus or penalty provided by this armor. A positive number reduces AC (good)
        and a negative number increases AC (bad). Defaults to 1.

    Example:
        >>> armor = Armor("Plate Mail", ac_modifier=7)
    """

    def __init__(self, name: str, ac_modifier: int = -1, **kwargs):
        """Initialize an armor item with the specified properties.

        Args:
            name (str): Name of the item.
            ac_modifier (int, optional): AC modifier. Lower is better. Defaults to -1.
            **kwargs: Additional arguments to pass to the parent class.
        """
        super().__init__(name, ItemType.ARMOR, **kwargs)
        self.ac_modifier = ac_modifier
        self.max_equipped = kwargs.get("max_equipped", 1) # Armor is typically 1 per PC

    def __str__(self):
        """Get a string representation of the armor item.

        Returns:
            str: A string with the armor name and AC modifier.
        """
        return f"{self.name} (AC: {9 + self.ac_modifier})"

    def to_dict(self) -> dict:
        armor_dict = super().to_dict()
        armor_dict["ac_modifier"] = self.ac_modifier
        return armor_dict

    @classmethod
    def from_dict(cls, armor_dict: dict) -> "Armor":
        base_item = Item.from_dict(armor_dict)
        ac_modifier = armor_dict.get("ac_modifier", -1)
        return cls(
            name=base_item.name,
            ac_modifier=ac_modifier,
            usable_by_classes=base_item.usable_by_classes,
            max_equipped=base_item.max_equipped,
            gp_value=base_item.gp_value,
        )


class Weapon(Item):
    """Represents a weapon item in the game.

    Args:
        name (str): The name of the weapon.
        to_hit_damage_die (str, optional): The to-hit and damage roll for the weapon. Defaults to '1d4'.
        range (Optional[int], optional): The range of the weapon in feet. Defaults to None for melee weapons.
        **kwargs: Arbitrary keyword arguments inherited from the Item class.

    Attributes:
        damage_die (str): The damage die for the weapon, formatted like '1d8', '2d4', '1d6+1', etc.
        range (Optional[int]): The range of the weapon in feet.

    Note:
        The Weapon class extends the Item class to represent weapons in the game.
        It specifies damage die and may have a range indicating how far it can attack.
        Melee weapons typically have `None` as their range value.

    Example:
        >>> sword = Weapon(name="Longsword", to_hit_damage_die="1d8")
        >>> enchanted_bow = Weapon(name="Longbow of Accuracy", to_hit_damage_die="1d8+1", range=150)
    """

    def __init__(
        self,
        name: str,
        to_hit_damage_die: str = "1d4",
        range: Optional[int] = None,  # melee weapons do not have a range
        **kwargs,
    ):
        """Initialize a weapon item with the specified properties."""
        super().__init__(name, ItemType.WEAPON, **kwargs)
        self.owner = kwargs.get("owner", None)
        self.damage_die = (
            to_hit_damage_die  # format like "1d8", "1d6+1", "1d4-1" etc.
        )
        self.range = range  # in feet (None for melee weapons)
        self.max_equipped = kwargs.get("max_equipped", 1) # Weapons are typically 1 per PC

    def __str__(self):
        return f"{self.name} (Damage: {self.damage_die}, Range: {self.range})"

    def to_dict(self) -> dict:
        weapon_dict = super().to_dict()
        weapon_dict["to_hit_damage_die"] = self.damage_die
        weapon_dict["range"] = self.range
        return weapon_dict

    @classmethod
    def from_dict(cls, weapon_dict: dict) -> "Weapon":
        base_item = Item.from_dict(weapon_dict)
        to_hit_damage_die = weapon_dict.get("to_hit_damage_die", "1d4")
        range = weapon_dict.get("range", None)
        return cls(
            name=base_item.name,
            to_hit_damage_die=to_hit_damage_die,
            range=range,
            usable_by_classes=base_item.usable_by_classes,
            max_equipped=base_item.max_equipped,
            gp_value=base_item.gp_value,
        )


class Spell(Item):
    """Represents a spell item in the game.

    The Spell class extends the Item class to represent spells in the game. Spells have a level and may have a range,
    damage die, and duration. Unlike weapons, spells do not have a to-hit roll (they always hit if the spellcaster
    successfully cast the spell).

    Args:
        name (str): The name of the spell.
        spell_level (int): The level of the spell.
        damage_die (Optional[str], optional): The damage roll for the spell. Defaults to None.
        range (Optional[int], optional): The range of the spell in feet. Defaults to None for touch spells.
        duration_turns (Optional[int], optional): The duration of the spell in turns (1 turn = 10 minutes). Defaults to
        None for instantaneous spells.
        **kwargs: Arbitrary keyword arguments inherited from the Item class.

    Attributes:
        spell_level (int): The level of the spell.
        damage_die (Optional[str]): The damage die for the spell, formatted like '1d8', '2d6', etc.
        range (Optional[int]): The range of the spell in feet.
        duration_minutes (Optional[int]): The duration of the spell in minutes. Defaults to None which indicates an
        instantaneous spell.

    Example:
        >>> fireball = Spell(name="Fireball", spell_level=3, damage_die="8d6", range=150, duration_minutes=None)
        >>> heal = Spell(name="Heal", spell_level=6, damage_die=None, range=None, duration_minutes=10)
    """

    def __init__(
        self,
        name: str,
        spell_level: int,
        damage_die: Optional[str] = None,
        range: Optional[int] = None,  # 'touch' spells do not have a range
        duration_turns: Optional[int] = None,  # 'instantaneous' spells have no duration
        **kwargs,
    ):
        """Initialize a spell item with the specified properties."""
        super().__init__(name, ItemType.SPELL, **kwargs)
        self.spell_level = spell_level
        self.range = range  # None for 'touch' spells
        self.damage_die = damage_die  # Optional - format like "1d8", "2d6", etc.
        self.duration_turns = duration_turns  # None for 'instantaneous' spells

    def to_dict(self) -> dict:
        spell_dict = super().to_dict()
        spell_dict["spell_level"] = self.spell_level
        spell_dict["range"] = self.range
        spell_dict["damage_die"] = self.damage_die
        spell_dict["duration_turns"] = self.duration_turns
        return spell_dict

    @classmethod
    def from_dict(cls, spell_dict: dict) -> "Spell":
        base_item = Item.from_dict(spell_dict)
        spell_level = spell_dict.get("spell_level", 1)
        range = spell_dict.get("range", None)
        damage_die = spell_dict.get("damage_die", None)
        duration_turns = spell_dict.get("duration_turns", None)
        return cls(
            name=base_item.name,
            spell_level=spell_level,
            range=range,
            damage_die=damage_die,
            duration_turns=duration_turns,
            usable_by_classes=base_item.usable_by_classes,
            max_equipped=base_item.max_equipped,
            gp_value=base_item.gp_value,
        )

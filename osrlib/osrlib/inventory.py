"""The `inventory` module includes the [Inventory][osrlib.inventory.Inventory] class which backs the `inventory` attribute of a [PlayerCharacter][osrlib.player_character.PlayerCharacter]."""

from collections import defaultdict
from typing import List

from osrlib.enums import ItemType
from osrlib.item import (
    Item,
    ItemAlreadyHasOwnerError,
    ItemAlreadyInInventoryError,
    ItemEquippedError,
    ItemNotEquippedError,
    ItemNotInInventoryError,
    ItemNotUsableError,
    Armor,
    Weapon,
    Spell
)


class Inventory:
    """A container to hold items owned by a player character (PC).

    You should not create an InventoryManager directly. When you initialize a PlayerCharacter, an inventory is created as a
    property of the PC. You can then add and remove items to and from the inventory using methods on the
    PlayerCharacter.

    Attributes:
        item_dict (defaultdict[ItemType, List[Item]]): List of items in the inventory.
        owner (PlayerCharacter): Owner of the inventory.

    Example:

    ```python
    >>> pc = PlayerCharacter()
    >>> inv = Inventory(pc)
    ```
    """

    def __init__(self, player_character_owner: "PlayerCharacter"):
        """Creates a `PlayerCharacter` instance.

        Args:
            player_character_owner (PlayerCharacter): The player character that owns the inventory.
        """
        self.items: defaultdict[ItemType, List[Item]] = defaultdict(list)
        self.owner = player_character_owner

    def add_item(self, item: Item):
        """Add an item to the inventory and sets its owner.

        Args:
            item (Item): Item to add.
        """
        if item.owner is not None and item.owner != self.owner:
            raise ItemAlreadyHasOwnerError(
                f"Can't add item '{item.name}' to inventory because it's already owned by '{item.owner.name}'."
            )

        if item not in self.items[item.item_type]:
            item._set_owner(self.owner)
            self.items[item.item_type].append(item)
            return True  # Successfully added
        else:
            raise ItemAlreadyInInventoryError(
                f"Can't add item '{item.name}' to inventory of '{self.owner.name}' because it's already in their inventory."
            )

    def get_item(self, item: Item):
        """Gets an item from the inventory.

        Args:
            item (Item): Item to get from the inventory.

        Returns:
            Item: The item if it exists in the inventory, otherwise an Exception is thrown.

        Raises:
            Exception: If the item does not exist in the inventory.
        """
        if item in self.items[item.item_type]:
            return item
        else:
            raise ItemNotInInventoryError(
                f"Can't get item '{item.name}' from inventory of '{self.owner.name}' because it's not in their inventory."
            )

    def remove_item(self, item: Item):
        """Removes an item from the inventory and resets its owner to None.

        Args:
            item (Item): Item to remove.

        Returns:
            bool: True if the item was successfully removed.

        Raises:
            Exception: If the item is currently equipped.
        """
        if item.is_equipped:
            raise ItemEquippedError(
                f"Can't remove item '{item.name}' from inventory of '{self.owner.name}' because it's currently equipped."
            )

        if item in self.items[item.item_type]:
            item._set_owner(None)
            self.items[item.item_type].remove(item)
            return True  # Successfully removed
        else:
            raise ItemNotInInventoryError(
                f"Can't remove item '{item.name}' from inventory of '{self.owner.name}' because it's not in their inventory."
            )

    def equip_item(self, item: Item):
        """Equips an item if it can be equipped.

        Args:
            item (Item): Item to equip.

        Returns:
            bool: True if the item was successfully equipped. False if the item could not be equipped.

        Raises:
            ItemNotUsableError: If the item is not usable by the owner's character class.
        """
        if item.is_equipable:
            currently_equipped = sum(1 for i in self.items[item.item_type] if i.is_equipped)
            if currently_equipped < item.max_equipped:
                item.is_equipped = True
                return True  # Successfully equipped
            else:
                return False  # Could not equip because max number already equipped
        else:
            raise ItemNotUsableError(f"Can't equip item '{item.name}' because it is not usable by {self.owner.name}.")

    def unequip_item(self, item: Item):
        """Unequips an item if it is currently equipped.

        Args:
            item (Item): Item to unequip.

        Returns:
            bool: True if the item was successfully unequipped.

        Raises:
            Exception: If the item is not currently equipped.
        """
        if item.is_equipped:
            item.is_equipped = False
            return True  # Successfully unequipped
        else:
            raise ItemNotEquippedError(f"Can't unequip item '{item.name}' because it is not currently equipped.")

    def drop_all_items(self) -> List[Item]:
        """Remove all items from the inventory and return a collection of the items that were removed.

        Equipped items are unequipped prior to being removed.

        Returns:
            List of all items that were removed.
        """
        removed_items = []
        for item in self.all_items:
            if item.is_equipped:
                self.unequip_item(item)

            if self.remove_item(item):
                removed_items.append(item)

        return removed_items

    @property
    def all_items(self) -> List[Item]:
        """Gets all items stored in the items defaultdict inventory property.

        Returns:
            List of all items in the inventory.
        """
        return [item for sublist in self.items.values() for item in sublist]

    @property
    def equipped_items(self) -> List[Item]:
        """Get all equipped items in the inventory.

        Returns:
            List of equipped items. Returns an empty list if no equipped items are present.
        """
        return [item for item in self.all_items if item.is_equipped]

    @property
    def armor(self) -> List[Armor]:
        """Gets all armor items stored in the items defaultdict inventory property.

        Returns:
            List of armor items. Returns an empty list if no armor items are present.
        """
        return self.items[ItemType.ARMOR]

    @property
    def weapons(self) -> List[Weapon]:
        """Gets all weapon items stored in the items defaultdict inventory property.

        Returns:
            List of weapon items. Returns an empty list if no weapon items are present.
        """
        return self.items[ItemType.WEAPON]

    def get_equipped_weapon(self) -> Weapon:
        """Gets the first equipped weapon in the inventory.

        Returns:
            Weapon: The equipped weapon. Returns "Fists" (1 HP damage) if no other weapon is equipped.
        """
        return next((weapon for weapon in self.weapons if weapon.is_equipped), Weapon("Fists", "1d1"))

    @property
    def spells(self) -> List[Spell]:
        """Gets all spell items stored in the items defaultdict inventory property.

        Returns:
            List of spell items. Returns an empty list if no spell items are present.
        """
        return self.items[ItemType.SPELL]

    @property
    def equipment(self) -> List[Item]:
        """Gets all equipment items stored in the items defaultdict inventory property.

        Returns:
            List of equipment items. Returns an empty list if no equipment items are present.
        """
        return self.items[ItemType.EQUIPMENT]

    @property
    def magic_items(self) -> List[Item]:
        """Gets all magic items stored in the items defaultdict inventory property.

        Returns:
            List of magic items. Returns an empty list if no magic items are present.
        """
        return self.items[ItemType.MAGIC_ITEM]

    @property
    def misc_items(self) -> List[Item]:
        """Gets all miscellaneous items stored in the items defaultdict inventory property.

        Miscellaneous items include items that are not armor, weapons, spells, equipment, or magic items.

        Returns:
            List of miscellaneous items. Returns an empty list if no miscellaneous items are present.
        """
        return self.items[ItemType.ITEM]

    def to_dict(self) -> dict:
        """Serializes the `Inventory` to a dictionary, typically in preparation for writing it to persistent storage in a downstream operation."""
        return {
            "items": [item.to_dict() for item in self.all_items],
            "owner": self.owner.name,
        }

    @classmethod
    def from_dict(cls, inventory_dict: dict, player_character_owner: "PlayerCharacter") -> "Inventory":
        """Deserializes a dictionary representation of an `Inventory` object. Typically done after getting the dictionary from persistent storage.

        Args:
            inventory_dict (dict): Dictionary representation of the inventory.
            player_character_owner (PlayerCharacter): The player character that owns the inventory.
        """
        player_character_owner.inventory = Inventory(player_character_owner)

        for item_dict in inventory_dict["items"]:
            item_type = item_dict.get("item_type")
            is_equipped = item_dict.get("is_equipped", False)

            # Create the appropriate object based on ItemType
            if item_type == ItemType.ARMOR.value[0]:
                item = Armor.from_dict(item_dict)
            elif item_type == ItemType.WEAPON.value[0]:
                item = Weapon.from_dict(item_dict)
            elif item_type == ItemType.SPELL.value[0]:
                item = Spell.from_dict(item_dict)
            else:
                item = Item.from_dict(item_dict)

            player_character_owner.inventory.add_item(item)

            if is_equipped:
                player_character_owner.inventory.equip_item(item)

        return player_character_owner.inventory

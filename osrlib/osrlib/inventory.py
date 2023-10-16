from collections import defaultdict
from typing import List

from osrlib.item import (
    Item,
    ItemAlreadyHasOwnerError,
    ItemAlreadyInInventoryError,
    ItemEquippedError,
    ItemNotEquippedError,
    ItemNotInInventoryError,
    ItemNotUsableError,
    ItemType,
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
        >>> pc = PlayerCharacter()
        >>> inv = Inventory(pc)
    """

    # TODO: Add a drop_all_items() method to remove all items from the inventory (unequip and set owner to None)

    def __init__(self, player_character_owner: "PlayerCharacter"):
        """Initialize a PlayerCharacter's inventory.

        Args:
            owner (PlayerCharacter): The player character that owns the inventory.
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

    @property
    def all_items(self):
        """Gets all items stored in the items defaultdict inventory property.

        Returns:
            list[Item]: List of all items.
        """
        return [item for sublist in self.items.values() for item in sublist]

    @property
    def armor(self):
        """Gets all armor items stored in the items defaultdict inventory property.

        Returns:
            list[Item]: List of armor items. Returns an empty list if no armor items are present.
        """
        return self.items[ItemType.ARMOR]

    @property
    def weapons(self):
        """Gets all weapon items stored in the items defaultdict inventory property.

        Returns:
            list[Item]: List of weapon items. Returns an empty list if no weapon items are present.
        """
        return self.items[ItemType.WEAPON]

    @property
    def spells(self):
        """Gets all spell items stored in the items defaultdict inventory property.

        Returns:
            list[Item]: List of spell items. Returns an empty list if no spell items are present.
        """
        return self.items[ItemType.SPELL]

    @property
    def equipment(self):
        """Gets all equipment items stored in the items defaultdict inventory property.

        Returns:
            list[Item]: List of equipment items. Returns an empty list if no equipment items are present.
        """
        return self.items[ItemType.EQUIPMENT]

    @property
    def magic_items(self):
        """Gets all magic items stored in the items defaultdict inventory property.

        Returns:
            list[Item]: List of magic items. Returns an empty list if no magic items are present.
        """
        return self.items[ItemType.MAGIC_ITEM]

    @property
    def misc_items(self):
        """Gets all miscellaneous items stored in the items defaultdict inventory property.

        Miscellaneous items include items that are not armor, weapons, spells, equipment, or magic items.

        Returns:
            list[Item]: List of miscellaneous items. Returns an empty list if no miscellaneous items are present.
        """
        return self.items[ItemType.ITEM]

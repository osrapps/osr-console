from osrlib.inventory import Inventory
from osrlib.item import Item
from osrlib.player_character import PlayerCharacter, CharacterClassType
from osrlib.item import ItemType
import pytest


@pytest.fixture
def inventory():
    pc = PlayerCharacter("Test PC", CharacterClassType.FIGHTER)
    return Inventory(pc)


@pytest.fixture
def item():
    return Item(
        "Test Item", ItemType.ITEM, usable_by_classes=CharacterClassType.FIGHTER
    )


def test_add_item(inventory, item):
    assert inventory.add_item(item) == True
    assert item in inventory.all_items


def test_add_item_already_has_owner(inventory, item):
    item._set_owner(PlayerCharacter("Another PC", CharacterClassType.MAGIC_USER))
    with pytest.raises(Exception):
        inventory.add_item(item)


def test_add_item_already_in_inventory(inventory, item):
    inventory.add_item(item)
    with pytest.raises(Exception):
        inventory.add_item(item)


def test_get_item(inventory, item):
    inventory.add_item(item)
    assert inventory.get_item(item) == item


def test_get_item_not_in_inventory(inventory, item):
    with pytest.raises(Exception):
        inventory.get_item(item)


def test_remove_item(inventory, item):
    inventory.add_item(item)
    assert inventory.remove_item(item) == True
    assert item not in inventory.all_items


def test_remove_item_equipped(inventory):
    item1 = Item(
        "Test Item 1",
        ItemType.ITEM,
        max_equipped=1,
        usable_by_classes=[CharacterClassType.FIGHTER],
    )
    inventory.add_item(item1)
    inventory.equip_item(item1)
    with pytest.raises(Exception):
        inventory.remove_item(item1)


def test_remove_item_not_in_inventory(inventory, item):
    with pytest.raises(Exception):
        inventory.remove_item(item)


def test_drop_all_items(inventory):
    item1 = Item(
        "Test Item 1",
        ItemType.ITEM,
        max_equipped=1,
        usable_by_classes=[CharacterClassType.FIGHTER],
    )
    item2 = Item("Test Item 2", ItemType.ITEM)
    inventory.add_item(item1)
    inventory.add_item(item2)
    inventory.equip_item(item1)
    removed_items = inventory.drop_all_items()
    assert item1 not in inventory.all_items
    assert item2 not in inventory.all_items
    assert item1 in removed_items
    assert item2 in removed_items


def test_all_items(inventory):
    item1 = Item("Test Item 1", ItemType.ITEM)
    item2 = Item("Test Item 2", ItemType.ITEM)
    inventory.add_item(item1)
    inventory.add_item(item2)
    assert item1 in inventory.all_items
    assert item2 in inventory.all_items


def test_armor(inventory):
    item1 = Item("Test Item 1", ItemType.ARMOR)
    item2 = Item("Test Item 2", ItemType.ITEM)
    inventory.add_item(item1)
    inventory.add_item(item2)
    assert item1 in inventory.armor
    assert item2 not in inventory.armor


def test_weapons(inventory):
    item1 = Item("Test Item 1", ItemType.WEAPON)
    item2 = Item("Test Item 2", ItemType.ITEM)
    inventory.add_item(item1)
    inventory.add_item(item2)
    assert item1 in inventory.weapons
    assert item2 not in inventory.weapons


def test_spells(inventory):
    item1 = Item("Test Item 1", ItemType.SPELL)
    item2 = Item("Test Item 2", ItemType.ITEM)
    inventory.add_item(item1)
    inventory.add_item(item2)
    assert item1 in inventory.spells
    assert item2 not in inventory.spells


def test_equipment(inventory):
    item1 = Item("Test Item 1", ItemType.EQUIPMENT)
    item2 = Item("Test Item 2", ItemType.ITEM)
    inventory.add_item(item1)
    inventory.add_item(item2)
    assert item1 in inventory.equipment
    assert item2 not in inventory.equipment


def test_magic_items(inventory):
    item1 = Item("Test Item 1", ItemType.MAGIC_ITEM)
    item2 = Item("Test Item 2", ItemType.ITEM)
    inventory.add_item(item1)
    inventory.add_item(item2)
    assert item1 in inventory.magic_items
    assert item2 not in inventory.magic_items


def test_misc_items(inventory):
    item1 = Item("Test Item 1", ItemType.ITEM)
    item2 = Item("Test Item 2", ItemType.ARMOR)
    inventory.add_item(item1)
    inventory.add_item(item2)
    assert item1 in inventory.misc_items
    assert item2 not in inventory.misc_items

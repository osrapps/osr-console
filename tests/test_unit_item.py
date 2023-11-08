import logging

import pytest

from osrlib.enums import CharacterClassType
from osrlib.item import (
    ItemAlreadyHasOwnerError,
    ItemAlreadyInInventoryError,
    ItemEquippedError,
    ItemNotEquippedError,
    ItemNotInInventoryError,
    ItemNotUsableError,
    Weapon,
)
from osrlib.player_character import PlayerCharacter

logger = logging.getLogger(__name__)

CLASSES_THAT_CAN_USE_ALL_WEAPONS = {
    CharacterClassType.FIGHTER,
    CharacterClassType.THIEF,
    CharacterClassType.ELF,
    CharacterClassType.DWARF,
    CharacterClassType.HALFLING,
}

def create_weapon(name, damage_die, classes_that_can_use_it, max_equipped, gp_value, range=0):
    return Weapon(
        name,
        damage_die,
        usable_by_classes=classes_that_can_use_it,
        max_equipped=max_equipped,
        gp_value=gp_value,
        range=range,
    )

def generate_test_params():
    sword = create_weapon("sword", "1d6", CLASSES_THAT_CAN_USE_ALL_WEAPONS, 1, 40)
    mace = create_weapon("mace", "1d6", CLASSES_THAT_CAN_USE_ALL_WEAPONS | {CharacterClassType.CLERIC}, 1, 20)
    dagger = create_weapon("dagger", "1d4", CLASSES_THAT_CAN_USE_ALL_WEAPONS | {CharacterClassType.MAGIC_USER}, 1, 10)
    crossbow = create_weapon("crossbow", "1d6", CLASSES_THAT_CAN_USE_ALL_WEAPONS, 1, 60, 240)

    weapons = [sword, mace, dagger, crossbow]
    test_params = []

    for weapon in weapons:
        for char_class in CharacterClassType:
            test_params.append((weapon, char_class, char_class in weapon.usable_by_classes))

    return test_params


@pytest.fixture
def setup_pc(character_class):
    # Setup
    pc = PlayerCharacter(f"Test {character_class.value}", character_class)
    yield pc


@pytest.mark.parametrize("weapon, character_class, expected_result", generate_test_params())
def test_weapon_usability_per_character_class(setup_pc, weapon, expected_result):
    pc = setup_pc

    # Item should be successfully added to inventory regardless of usability
    logger.info(f"Adding {weapon.name} to {pc.name}'s inventory")
    assert pc.inventory.add_item(weapon), f"{weapon.name} not added to {pc.name}'s inventory"

    logger.info(f"Adding {weapon.name} to {pc.name}'s inventory again")
    with pytest.raises(ItemAlreadyInInventoryError):
        pc.inventory.add_item(weapon)

    # Item should be retrievable from inventory if it was previously added
    logger.info(f"Getting {weapon.name} from {pc.name}'s inventory")
    weapon_from_inv = pc.inventory.get_item(weapon)
    assert weapon_from_inv == weapon, f"Could NOT get {weapon.name} from {pc.name}'s inventory"

    # Error should be raised when trying to get an item from inventory that's not in the inventory
    with pytest.raises(ItemNotInInventoryError):
        some_other_weapon = create_weapon(
            "THIS WEAPON NOT IN INVENTORY", "1d6", CLASSES_THAT_CAN_USE_ALL_WEAPONS, 1, 40
        )
        pc.inventory.get_item(some_other_weapon)

    # Item should be usable by classes that can use it
    logger.info(f"Checking whether {pc.name} can use {weapon.name}")
    assert weapon.is_usable_by_owner == expected_result, (
        f"{pc.name} should be able to use {weapon.name}"
        if expected_result
        else f"{pc.name} should NOT be able to use {weapon.name}"
    )

    # Item should be equipable and unequipable if it's usable by owner
    if weapon.is_usable_by_owner:
        logger.info(f"Equipping {pc.name} with {weapon.name}")
        assert pc.inventory.equip_item(weapon), f"{pc.name} could NOT equip {weapon.name}"

        logger.info(f"Unequipping {pc.name}'s {weapon.name}")
        assert pc.inventory.unequip_item(weapon), f"{pc.name} could NOT unequip {weapon.name}"

        # Error should be raised when trying to unequip an item that's not equipped
        if not weapon.is_equipped:
            with pytest.raises(ItemNotEquippedError):
                pc.inventory.unequip_item(weapon)
    else:
        logger.info(f"{weapon.name} is NOT usable by {pc.name}, skipping equip/unequip test")

    # Item should be removable from inventory
    logger.info(f"Removing {weapon.name} from {pc.name}'s inventory")
    assert pc.inventory.remove_item(weapon), f"{weapon.name} could NOT be removed from {pc.name}'s inventory"

    # Error should be raised on attemping to remove an item not in inventory
    with pytest.raises(ItemNotInInventoryError):
        pc.inventory.remove_item(weapon)

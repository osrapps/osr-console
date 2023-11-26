import logging

import pytest

from osrlib.ability import AbilityType
from osrlib.character_classes import CharacterClassType
from osrlib.combat import ModifierType
from osrlib.item import Armor
from osrlib.player_character import PlayerCharacter

logger = logging.getLogger(__name__)

CLASSES_THAT_CAN_USE_ALL_ARMOR = {
    CharacterClassType.FIGHTER,
    CharacterClassType.CLERIC,
    CharacterClassType.ELF,
    CharacterClassType.DWARF,
    CharacterClassType.HALFLING,
}


def generate_armor(name, ac, classes, max_equipped, gp_value):
    return Armor(
        name,
        ac,
        usable_by_classes=classes,
        max_equipped=max_equipped,
        gp_value=gp_value,
    )


def generate_test_params():
    robes = generate_armor(
        "Robes", 0, CLASSES_THAT_CAN_USE_ALL_ARMOR | {CharacterClassType.MAGIC_USER} | {CharacterClassType.THIEF}, 1, 0
    )
    shield = generate_armor("Shield", -1, CLASSES_THAT_CAN_USE_ALL_ARMOR, 1, 60)
    leather_armor = generate_armor(
        "Leather Armor", -3, CLASSES_THAT_CAN_USE_ALL_ARMOR | {CharacterClassType.THIEF}, 1, 20
    )
    chain_mail_armor = generate_armor("Chain Mail Armor", -4, CLASSES_THAT_CAN_USE_ALL_ARMOR, 1, 40)
    plate_mail_armor = generate_armor("Plate Mail Armor", -6, CLASSES_THAT_CAN_USE_ALL_ARMOR, 1, 60)

    armors = [robes, shield, leather_armor, chain_mail_armor, plate_mail_armor]
    test_params = []

    for armor in armors:
        for char_class in CharacterClassType:
            test_params.append((armor, char_class, char_class in armor.usable_by_classes))

    return test_params


@pytest.fixture
def setup_pc(character_class, armor):
    # Setup
    pc = PlayerCharacter(f"Test {character_class.value}", character_class)
    yield pc

    # Teardown
    if armor.is_equipped:
        pc.inventory.unequip_item(armor)
    pc.inventory.remove_item(armor)


# Armor should have been added to the inventory
@pytest.mark.parametrize("armor, character_class, expected_result", generate_test_params())
def test_armor_added_to_inventory(setup_pc, armor, expected_result):
    pc = setup_pc
    pc.inventory.add_item(armor)
    assert armor is pc.inventory.get_item(armor)


# Armor should "know" whether it's usable by the owning character's class
@pytest.mark.parametrize("armor, character_class, expected_result", generate_test_params())
def test_armor_usability_by_owner(setup_pc, armor, expected_result):
    pc = setup_pc
    pc.inventory.add_item(armor)
    assert armor.is_usable_by_owner == expected_result


# Armor should be able to be equipped and should be shown as such if
# usable by the owning character's class and is then equipped.
@pytest.mark.parametrize("armor, character_class, expected_result", generate_test_params())
def test_armor_equip_status(setup_pc, armor, expected_result):
    pc = setup_pc
    pc.inventory.add_item(armor)
    if armor.is_usable_by_owner:
        dex = pc.abilities[AbilityType.DEXTERITY].score
        ac_mod = pc.abilities[AbilityType.DEXTERITY].modifiers[ModifierType.AC]
        logger.debug(f"{armor.name} is usable by {pc.name} [DEX: {dex} ({ac_mod}), AC: {pc.armor_class})]")
        pc.inventory.equip_item(armor)
        logger.debug(f"{armor.name} equipped  by {pc.name} [DEX: {dex} ({ac_mod}), AC: {pc.armor_class})]")
        assert armor.is_equipped
    else:
        logger.debug(f"{armor.name} is NOT usable by {pc.name}")
        assert not armor.is_equipped

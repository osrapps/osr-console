import pytest
from osrlib import (
    ArmorFactory,
    EquipmentFactory,
    WeaponFactory,
    CharacterClassType,
    ItemType,
    ItemDataNotFoundError,
)

def test_create_valid_armor():
    """Test successful creation of a valid armor."""
    armor_name = "Leather Armor"
    armor = ArmorFactory.create_armor(armor_name)

    assert armor.name == armor_name
    assert armor.item_type == ItemType.ARMOR
    assert armor.ac_modifier == -2
    assert armor.gp_value == 20
    assert CharacterClassType.FIGHTER in armor.usable_by_classes
    assert CharacterClassType.MAGIC_USER not in armor.usable_by_classes

def test_create_invalid_armor():
    """Test unsuccessful creation due to invalid armor name."""
    with pytest.raises(ItemDataNotFoundError):
        ArmorFactory.create_armor("InvalidArmorName")

def test_create_valid_equipment():
    """Test successful creation of a valid equipment."""
    item_name = "Backpack"
    equipment = EquipmentFactory.create_item(item_name)

    assert equipment.name == item_name
    assert equipment.item_type == ItemType.EQUIPMENT
    assert equipment.gp_value == 5


def test_create_invalid_equipment():
    """Test unsuccessful creation due to invalid equipment name."""
    with pytest.raises(ItemDataNotFoundError):
        EquipmentFactory.create_item("InvalidEquipmentName")


def test_create_valid_weapon():
    """Test successful creation of a valid weapon."""
    weapon_name = "Dagger"
    weapon = WeaponFactory.create_weapon(weapon_name)

    assert weapon.name == weapon_name
    assert weapon.damage_die == "1d4"
    assert weapon.gp_value == 3
    assert CharacterClassType.FIGHTER in weapon.usable_by_classes
    assert CharacterClassType.MAGIC_USER in weapon.usable_by_classes


def test_create_invalid_weapon():
    """Test unsuccessful creation due to invalid weapon name."""
    with pytest.raises(ItemDataNotFoundError):
        WeaponFactory.create_weapon("InvalidWeaponName")

def test_create_ranged_weapon():
    """Test successful creation of a valid weapon with range attribute."""
    weapon_name = "Short Bow"
    weapon = WeaponFactory.create_weapon(weapon_name)

    assert weapon.name == weapon_name
    assert weapon.damage_die == "1d6"
    assert weapon.gp_value == 25
    assert weapon.range == 100
    assert CharacterClassType.FIGHTER in weapon.usable_by_classes
    assert CharacterClassType.MAGIC_USER not in weapon.usable_by_classes


def test_create_weapon_without_range():
    """Test successful creation of a valid weapon without range attribute."""
    weapon_name = "Sword"
    weapon = WeaponFactory.create_weapon(weapon_name)

    assert weapon.name == weapon_name
    assert weapon.damage_die == "1d8"
    assert weapon.gp_value == 10
    assert weapon.range is None
    assert CharacterClassType.FIGHTER in weapon.usable_by_classes
    assert CharacterClassType.THIEF in weapon.usable_by_classes
    assert CharacterClassType.ELF in weapon.usable_by_classes
    assert CharacterClassType.DWARF in weapon.usable_by_classes
    assert CharacterClassType.HALFLING in weapon.usable_by_classes
    assert CharacterClassType.MAGIC_USER not in weapon.usable_by_classes
    assert CharacterClassType.CLERIC not in weapon.usable_by_classes
import pytest
from osrlib import EquipmentFactory, WeaponFactory, CharacterClassType, ItemType

def test_create_valid_equipment():
    """Test successful creation of a valid equipment."""
    item_name = "Backpack"
    equipment = EquipmentFactory.create_item(item_name)

    assert equipment.name == item_name
    assert equipment.item_type == ItemType.EQUIPMENT
    assert equipment.gp_value == 5

def test_create_invalid_equipment():
    """Test unsuccessful creation due to invalid equipment name."""
    with pytest.raises(ValueError) as exc_info:
        EquipmentFactory.create_item("InvalidEquipmentName")

    assert "No data available for item: InvalidEquipmentName" in str(exc_info.value)


def test_create_valid_weapon():
    """Test successful creation of a valid weapon."""
    weapon_name = "Dagger"
    weapon = WeaponFactory.create_weapon(weapon_name)

    assert weapon.name == weapon_name
    assert weapon.to_hit_damage_die == "1d4"
    assert weapon.gp_value == 3
    assert CharacterClassType.FIGHTER in weapon.usable_by_classes
    assert CharacterClassType.MAGIC_USER in weapon.usable_by_classes

def test_create_invalid_weapon():
    """Test unsuccessful creation due to invalid weapon name."""
    with pytest.raises(ValueError) as exc_info:
        WeaponFactory.create_weapon("InvalidWeaponName")

    assert "Weapon 'InvalidWeaponName' not found in weapons data." in str(exc_info.value)

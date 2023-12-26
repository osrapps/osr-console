import random

from osrlib.item import Armor, Item, Weapon
from osrlib.enums import CharacterClassType, ItemType

_armor_combat_classes = {
    CharacterClassType.CLERIC,
    CharacterClassType.DWARF,
    CharacterClassType.ELF,
    CharacterClassType.FIGHTER,
    CharacterClassType.HALFLING,
}

_weapon_combat_classes = {
    CharacterClassType.DWARF,
    CharacterClassType.ELF,
    CharacterClassType.FIGHTER,
    CharacterClassType.HALFLING,
    CharacterClassType.THIEF,
}

_all_classes = _weapon_combat_classes | {
    CharacterClassType.CLERIC,
    CharacterClassType.MAGIC_USER,
}

armor_data = {
    "Chain Mail": {"ac": -4, "gp_value": 40, "usable_by": _armor_combat_classes},
    "Leather Armor": {"ac": -2, "gp_value": 20, "usable_by": _armor_combat_classes | {CharacterClassType.THIEF}},
    "Plate Mail": {"ac": -6, "gp_value": 60, "usable_by": _armor_combat_classes},
    "Shield": {"ac": -1, "gp_value": 10, "usable_by": _armor_combat_classes},
    "Robes": {"ac": 0, "gp_value": 1, "usable_by": {CharacterClassType.MAGIC_USER}},
}

magic_armor_data = {
    "Chain Mail +1": {"ac": -5, "gp_value": 400, "usable_by": _armor_combat_classes},
    "Chain Mail +2": {"ac": -6, "gp_value": 800, "usable_by": _armor_combat_classes},
    "Chain Mail +3": {"ac": -7, "gp_value": 1600, "usable_by": _armor_combat_classes},
    "Leather Armor +1": {"ac": -3, "gp_value": 200, "usable_by": _armor_combat_classes | {CharacterClassType.THIEF}},
    "Leather Armor +2": {"ac": -4, "gp_value": 400, "usable_by": _armor_combat_classes | {CharacterClassType.THIEF}},
    "Leather Armor +3": {"ac": -5, "gp_value": 800, "usable_by": _armor_combat_classes | {CharacterClassType.THIEF}},
    "Plate Mail +1": {"ac": -7, "gp_value": 600, "usable_by": _armor_combat_classes},
    "Plate Mail +2": {"ac": -8, "gp_value": 1200, "usable_by": _armor_combat_classes},
    "Plate Mail +3": {"ac": -9, "gp_value": 2400, "usable_by": _armor_combat_classes},
    "Shield +1": {"ac": -2, "gp_value": 100, "usable_by": _armor_combat_classes},
    "Shield +2": {"ac": -3, "gp_value": 200, "usable_by": _armor_combat_classes},
    "Shield +3": {"ac": -4, "gp_value": 400, "usable_by": _armor_combat_classes},
}

equipment_data = {
    "Backpack": 5,
    "Flask of Oil": 2,
    "Hammer": 2, # (small)
    "Holy Symbol": 25,
    "Holy Water": 25, # (1 vial)
    "Iron Spike (12)": 1, # (12)
    "Lantern": 10,
    "Mirror": 5, # (hand-sized, steel)
    "Iron Rations": 15, #  (preserved food for 1 person/1 week)
    "Standard Rations": 1, # (unpreserved food for 1 person/1 week)
    "Rope (50')": 1,
    "Small Sack": 1,
    "Spell Book": 50,
    "Large Sack": 2,
    "Thieves' Tools": 25,
    "Tinder Box": 3, # (flint & steel)
    "Torches (6)": 1,
    "Water/Wine Skin": 1,
    "Wine (1 quart)": 1,
    "Wolfsbane": 1,
    "Wooden Pole (10')": 1,
}

weapon_data = {
    "Battle Axe": {"damage": "1d8", "gp_value": 7, "usable_by": _weapon_combat_classes},
    "Club": {"damage": "1d4", "gp_value": 3, "usable_by": _weapon_combat_classes | {CharacterClassType.CLERIC}},
    "Crossbow": {"damage": "1d4", "gp_value": 30, "usable_by": _weapon_combat_classes, "range": 160},
    "Dagger": {"damage": "1d4", "gp_value": 3, "usable_by": _weapon_combat_classes | {CharacterClassType.MAGIC_USER}, "range": 20},
    "Hand Axe": {"damage": "1d6", "gp_value": 4, "usable_by": _weapon_combat_classes, "range": 20},
    "Long Bow": {"damage": "1d6", "gp_value": 40, "usable_by": {CharacterClassType.FIGHTER, CharacterClassType.ELF}, "range": 140},
    "Mace": {"damage": "1d6", "gp_value": 5, "usable_by": _weapon_combat_classes | {CharacterClassType.CLERIC}},
    "Pole Arm": {"damage": "1d10", "gp_value": 7, "usable_by": {CharacterClassType.FIGHTER, CharacterClassType.ELF, CharacterClassType.DWARF}},
    "Short Bow": {"damage": "1d6", "gp_value": 25, "usable_by": _weapon_combat_classes, "range": 100},
    "Short Sword": {"damage": "1d6", "gp_value": 7, "usable_by": _weapon_combat_classes},
    "Silver Dagger": {"damage": "1d4", "gp_value": 30, "usable_by": _weapon_combat_classes | {CharacterClassType.MAGIC_USER}, "range": 20},
    "Sling": {"damage": "1d4", "gp_value": 2, "usable_by": _weapon_combat_classes | {CharacterClassType.CLERIC}, "range": 80},
    "Spear": {"damage": "1d6", "gp_value": 3, "usable_by": _weapon_combat_classes | {CharacterClassType.CLERIC}, "range": 40},
    "Sword": {"damage": "1d8", "gp_value": 10, "usable_by": _weapon_combat_classes},
    "Torch": {"damage": "1d4", "gp_value": 1, "usable_by": _all_classes},
    "Two-handed Sword": {"damage": "1d10", "gp_value": 15, "usable_by": {CharacterClassType.FIGHTER, CharacterClassType.ELF}},
    "War Hammer": {"damage": "1d6", "gp_value": 5, "usable_by": _weapon_combat_classes | {CharacterClassType.CLERIC}}
}

magic_weapon_data = {
    "Battle Axe +1": {"damage": "1d8+1", "gp_value": 70, "usable_by": _weapon_combat_classes},
    "Battle Axe +2": {"damage": "1d8+2", "gp_value": 140, "usable_by": _weapon_combat_classes},
    "Battle Axe +3": {"damage": "1d8+3", "gp_value": 280, "usable_by": _weapon_combat_classes},
    "Club +1": {"damage": "1d4+1", "gp_value": 30, "usable_by": _weapon_combat_classes | {CharacterClassType.CLERIC}},
    "Club +2": {"damage": "1d4+2", "gp_value": 60, "usable_by": _weapon_combat_classes | {CharacterClassType.CLERIC}},
    "Club +3": {"damage": "1d4+3", "gp_value": 120, "usable_by": _weapon_combat_classes | {CharacterClassType.CLERIC}},
    "Crossbow +1": {"damage": "1d4+1", "gp_value": 130, "usable_by": _weapon_combat_classes, "range": 160},
    "Crossbow +2": {"damage": "1d4+2", "gp_value": 260, "usable_by": _weapon_combat_classes, "range": 160},
    "Crossbow +3": {"damage": "1d4+3", "gp_value": 520, "usable_by": _weapon_combat_classes, "range": 160},
    "Dagger +1": {"damage": "1d4+1", "gp_value": 30, "usable_by": _weapon_combat_classes | {CharacterClassType.MAGIC_USER}, "range": 20},
    "Dagger +2": {"damage": "1d4+2", "gp_value": 60, "usable_by": _weapon_combat_classes | {CharacterClassType.MAGIC_USER}, "range": 20},
    "Dagger +3": {"damage": "1d4+3", "gp_value": 120, "usable_by": _weapon_combat_classes | {CharacterClassType.MAGIC_USER}, "range": 20},
    "Long Bow +1": {"damage": "1d6+1", "gp_value": 130, "usable_by": {CharacterClassType.FIGHTER, CharacterClassType.ELF}, "range": 140},
    "Long Bow +2": {"damage": "1d6+2", "gp_value": 260, "usable_by": {CharacterClassType.FIGHTER, CharacterClassType.ELF}, "range": 140},
    "Long Bow +3": {"damage": "1d6+3", "gp_value": 520, "usable_by": {CharacterClassType.FIGHTER, CharacterClassType.ELF}, "range": 140},
    "Mace +1": {"damage": "1d6+1", "gp_value": 70, "usable_by": _weapon_combat_classes | {CharacterClassType.CLERIC}},
    "Mace +2": {"damage": "1d6+2", "gp_value": 140, "usable_by": _weapon_combat_classes | {CharacterClassType.CLERIC}},
    "Mace +3": {"damage": "1d6+3", "gp_value": 280, "usable_by": _weapon_combat_classes | {CharacterClassType.CLERIC}},
    "Pole Arm +1": {"damage": "1d10+1", "gp_value": 70, "usable_by": {CharacterClassType.FIGHTER, CharacterClassType.ELF, CharacterClassType.DWARF}},
    "Pole Arm +2": {"damage": "1d10+2", "gp_value": 140, "usable_by": {CharacterClassType.FIGHTER, CharacterClassType.ELF, CharacterClassType.DWARF}},
    "Pole Arm +3": {"damage": "1d10+3", "gp_value": 280, "usable_by": {CharacterClassType.FIGHTER, CharacterClassType.ELF, CharacterClassType.DWARF}},
    "Short Bow +1": {"damage": "1d6+1", "gp_value": 80, "usable_by": _weapon_combat_classes, "range": 100},
    "Short Bow +2": {"damage": "1d6+2", "gp_value": 160, "usable_by": _weapon_combat_classes, "range": 100},
    "Short Bow +3": {"damage": "1d6+3", "gp_value": 320, "usable_by": _weapon_combat_classes, "range": 100},
    "Silver Dagger +1": {"damage": "1d4+1", "gp_value": 130, "usable_by": _weapon_combat_classes | {CharacterClassType.MAGIC_USER}, "range": 20},
    "Silver Dagger +2": {"damage": "1d4+2", "gp_value": 260, "usable_by": _weapon_combat_classes | {CharacterClassType.MAGIC_USER}, "range": 20},
    "Silver Dagger +3": {"damage": "1d4+3", "gp_value": 520, "usable_by": _weapon_combat_classes | {CharacterClassType.MAGIC_USER}, "range": 20},
    "Sling +1": {"damage": "1d4+1", "gp_value": 130, "usable_by": _weapon_combat_classes | {CharacterClassType.CLERIC}, "range": 80},
    "Sling +2": {"damage": "1d4+2", "gp_value": 260, "usable_by": _weapon_combat_classes | {CharacterClassType.CLERIC}, "range": 80},
    "Sling +3": {"damage": "1d4+3", "gp_value": 520, "usable_by": _weapon_combat_classes | {CharacterClassType.CLERIC}, "range": 80},
    "Spear +1": {"damage": "1d6+1", "gp_value": 30, "usable_by": _weapon_combat_classes | {CharacterClassType.CLERIC}, "range": 40},
    "Spear +2": {"damage": "1d6+2", "gp_value": 60, "usable_by": _weapon_combat_classes | {CharacterClassType.CLERIC}, "range": 40},
    "Spear +3": {"damage": "1d6+3", "gp_value": 120, "usable_by": _weapon_combat_classes | {CharacterClassType.CLERIC}, "range": 40},
    "Sword +1": {"damage": "1d8+1", "gp_value": 90, "usable_by": _weapon_combat_classes},
    "Sword +2": {"damage": "1d8+2", "gp_value": 180, "usable_by": _weapon_combat_classes},
    "Sword +3": {"damage": "1d8+3", "gp_value": 360, "usable_by": _weapon_combat_classes},
    "Two-handed Sword +1": {"damage": "1d10+1", "gp_value": 100, "usable_by": {CharacterClassType.FIGHTER, CharacterClassType.ELF}},
    "Two-handed Sword +2": {"damage": "1d10+2", "gp_value": 200, "usable_by": {CharacterClassType.FIGHTER, CharacterClassType.ELF}},
    "Two-handed Sword +3": {"damage": "1d10+3", "gp_value": 400, "usable_by": {CharacterClassType.FIGHTER, CharacterClassType.ELF}},
    "War Hammer +1": {"damage": "1d6+1", "gp_value": 70, "usable_by": _weapon_combat_classes | {CharacterClassType.CLERIC}},
    "War Hammer +2": {"damage": "1d6+2", "gp_value": 140, "usable_by": _weapon_combat_classes | {CharacterClassType.CLERIC}},
    "War Hammer +3": {"damage": "1d6+3", "gp_value": 280, "usable_by": _weapon_combat_classes | {CharacterClassType.CLERIC}},
}

class ItemDataNotFoundError(Exception):
    """Raised when item data is not found."""

    def __init__(self, item_name):
        self.item_name = item_name

    def __str__(self):
        return f"No data available for item: {self.item_name}"


class ArmorFactory:
    """Factory class to create Armor items."""

    @staticmethod
    def create_armor(armor_name: str):
        armor_info = armor_data.get(armor_name)
        if armor_info:
            return Armor(
                name=armor_name,
                ac_modifier=armor_info["ac"],
                gp_value=armor_info["gp_value"],
                usable_by_classes=armor_info["usable_by"],
            )
        else:
            raise ItemDataNotFoundError(armor_name)


class EquipmentFactory:
    """Factory class to create equipment items."""

    @staticmethod
    def create_item(item_name):
        if item_name in equipment_data:
            return Item(
                item_name,
                ItemType.EQUIPMENT,
                _all_classes,
                max_equipped=0,
                gp_value=equipment_data[item_name],
            )
        else:
            raise ItemDataNotFoundError(item_name)


class WeaponFactory:
    """Factory class to create items of type ``Weapon``."""

    @staticmethod
    def create_weapon(weapon_name: str):
        weapon_info = weapon_data.get(weapon_name)
        if weapon_info:
            return Weapon(
                name=weapon_name,
                to_hit_damage_die=weapon_info["damage"],
                gp_value=weapon_info["gp_value"],
                usable_by_classes=weapon_info["usable_by"],
                range=weapon_info.get("range"),
            )

        else:
            raise ItemDataNotFoundError(weapon_name)

def equip_fighter(character: "PlayerCharacter"):
    """Equip a Fighter character with starting gear."""
    sword = WeaponFactory.create_weapon("Sword")
    shield = ArmorFactory.create_armor("Shield")
    chain_mail = ArmorFactory.create_armor("Chain Mail")
    backpack = EquipmentFactory.create_item("Backpack")

    character.inventory.add_item(sword)
    character.inventory.add_item(shield)
    character.inventory.add_item(chain_mail)
    character.inventory.add_item(backpack)

    character.inventory.equip_item(sword)
    character.inventory.equip_item(shield)
    character.inventory.equip_item(chain_mail)

def equip_elf(character: "PlayerCharacter"):
    """Equip an Elf character with starting gear."""
    longsword = WeaponFactory.create_weapon("Sword")
    longbow = WeaponFactory.create_weapon("Long Bow")
    leather_armor = ArmorFactory.create_armor("Leather Armor")
    backpack = EquipmentFactory.create_item("Backpack")

    character.inventory.add_item(longsword)
    character.inventory.add_item(longbow)
    character.inventory.add_item(leather_armor)
    character.inventory.add_item(backpack)

    character.inventory.equip_item(longsword)
    character.inventory.equip_item(leather_armor)

def equip_cleric(character: "PlayerCharacter"):
    """Equip a Cleric character with starting gear."""
    mace = WeaponFactory.create_weapon("Mace")
    shield = ArmorFactory.create_armor("Shield")
    chain_mail = ArmorFactory.create_armor("Chain Mail")
    backpack = EquipmentFactory.create_item("Backpack")
    holy_symbol = EquipmentFactory.create_item("Holy Symbol")

    character.inventory.add_item(mace)
    character.inventory.add_item(shield)
    character.inventory.add_item(chain_mail)
    character.inventory.add_item(backpack)
    character.inventory.add_item(holy_symbol)

    character.inventory.equip_item(mace)
    character.inventory.equip_item(shield)
    character.inventory.equip_item(chain_mail)

def equip_dwarf(character: "PlayerCharacter"):
    """Equip a Dwarf character with starting gear."""
    battleaxe = WeaponFactory.create_weapon("Battle Axe")
    chain_mail = ArmorFactory.create_armor("Chain Mail")
    backpack = EquipmentFactory.create_item("Backpack")

    character.inventory.add_item(battleaxe)
    character.inventory.add_item(chain_mail)
    character.inventory.add_item(backpack)

    character.inventory.equip_item(battleaxe)
    character.inventory.equip_item(chain_mail)

def equip_thief(character: "PlayerCharacter"):
    """Equip a Thief character with starting gear."""
    dagger = WeaponFactory.create_weapon("Dagger")
    leather_armor = ArmorFactory.create_armor("Leather Armor")
    backpack = EquipmentFactory.create_item("Backpack")
    thieves_tools = EquipmentFactory.create_item("Thieves' Tools")

    character.inventory.add_item(dagger)
    character.inventory.add_item(leather_armor)
    character.inventory.add_item(backpack)
    character.inventory.add_item(thieves_tools)

    character.inventory.equip_item(dagger)
    character.inventory.equip_item(leather_armor)

def equip_halfling(character: "PlayerCharacter"):
    """Equip a Halfling character with starting gear."""
    sling = WeaponFactory.create_weapon("Sling")
    leather_armor = ArmorFactory.create_armor("Leather Armor")
    backpack = EquipmentFactory.create_item("Backpack")

    character.inventory.add_item(sling)
    character.inventory.add_item(leather_armor)
    character.inventory.add_item(backpack)

    character.inventory.equip_item(sling)
    character.inventory.equip_item(leather_armor)

def equip_magic_user(character: "PlayerCharacter"):
    """Equip a Magic User character with starting gear."""
    dagger = WeaponFactory.create_weapon("Dagger")
    robe = ArmorFactory.create_armor("Robes")
    backpack = EquipmentFactory.create_item("Backpack")
    spellbook = EquipmentFactory.create_item("Spell Book")

    character.inventory.add_item(dagger)
    character.inventory.add_item(robe)
    character.inventory.add_item(backpack)
    character.inventory.add_item(spellbook)

    character.inventory.equip_item(dagger)

def equip_party(party: "Party"):
    """Equip a party with default starting gear based on their character classes."""
    for character in party.members:
        if character.character_class.class_type == CharacterClassType.FIGHTER:
            equip_fighter(character)
        elif character.character_class.class_type == CharacterClassType.ELF:
            equip_elf(character)
        elif character.character_class.class_type == CharacterClassType.CLERIC:
            equip_cleric(character)
        elif character.character_class.class_type == CharacterClassType.DWARF:
            equip_dwarf(character)
        elif character.character_class.class_type == CharacterClassType.THIEF:
            equip_thief(character)
        elif character.character_class.class_type == CharacterClassType.HALFLING:
            equip_halfling(character)
        elif character.character_class.class_type == CharacterClassType.MAGIC_USER:
            equip_magic_user(character)


def get_random_item(item_type: ItemType, magical: bool = False):
    """
    Gets a randomn (optionally magic) item from the given category.

    Args:
        item_type (ItemType): The category of item to get.
        magic (bool): Whether to get a magical version of the item.

    Returns:
        Item: An instance of the selected item.
    """
    if item_type == ItemType.ARMOR:
        data = magic_armor_data if magical else armor_data
        item_name = random.choice(list(data.keys()))
        return ArmorFactory.create_armor(item_name)
    elif item_type == ItemType.WEAPON:
        data = magic_weapon_data if magical else weapon_data
        item_name = random.choice(list(data.keys()))
        return WeaponFactory.create_weapon(item_name)
    # TODO: Add support for SPELL, EQUIPMENT, and MAGIC_ITEM
    else:
        raise ValueError(f"No item selection logic for {item_type}")

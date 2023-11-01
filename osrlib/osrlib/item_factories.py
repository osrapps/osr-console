from osrlib import CharacterClassType, Armor, Item, ItemType, Weapon

_armor_combat_classes = {
    CharacterClassType.FIGHTER,
    CharacterClassType.ELF,
    CharacterClassType.DWARF,
    CharacterClassType.HALFLING,
    CharacterClassType.CLERIC,
}

_weapon_combat_classes = {
    CharacterClassType.FIGHTER,
    CharacterClassType.THIEF,
    CharacterClassType.ELF,
    CharacterClassType.DWARF,
    CharacterClassType.HALFLING,
}

_all_classes = _weapon_combat_classes | {
    CharacterClassType.CLERIC,
    CharacterClassType.MAGIC_USER,
}

armor_data = {
    "Chain Mail Armor": {"ac": -4, "gp_value": 40, "usable_by": _armor_combat_classes},
    "Leather Armor": {"ac": -2, "gp_value": 20, "usable_by": _armor_combat_classes | {CharacterClassType.THIEF}},
    "Plate Mail Armor": {"ac": -6, "gp_value": 60, "usable_by": _armor_combat_classes},
    "Shield": {"ac": -1, "gp_value": 10, "usable_by": _armor_combat_classes},
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


# Usage example:
try:
    dagger = WeaponFactory.create_weapon("Dagger")
    print(dagger)

    bow = WeaponFactory.create_weapon("Short Bow")
    print(bow)

    thief_tools = EquipmentFactory.create_item("Thieves' Tools")
    print(thief_tools)

    not_real = EquipmentFactory.create_item("Not Real")
    print(not_real)
except ValueError as e:
    print(e)
except ItemDataNotFoundError as e:
    print(e)

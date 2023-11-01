from osrlib import CharacterClassType, Item, ItemType, Weapon

_combat_classes = {
    CharacterClassType.FIGHTER,
    CharacterClassType.THIEF,
    CharacterClassType.ELF,
    CharacterClassType.DWARF,
    CharacterClassType.HALFLING,
    }

_all_classes = _combat_classes | { CharacterClassType.CLERIC, CharacterClassType.MAGIC_USER }

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
        "Torch": {"damage": "1d4", "gp_value": 1, "usable_by": _all_classes},
        "Dagger": {"damage": "1d4", "gp_value": 3, "usable_by": _combat_classes | {CharacterClassType.MAGIC_USER}},
        "Silver Dagger": {"damage": "1d4", "gp_value": 30, "usable_by": _combat_classes | {CharacterClassType.MAGIC_USER}},
        "Club": {"damage": "1d4", "gp_value": 3, "usable_by": _combat_classes | {CharacterClassType.CLERIC}},
        "Sling stone": {"damage": "1d4", "gp_value": 2, "usable_by": _combat_classes | {CharacterClassType.CLERIC}},
        "Arrow": {"damage": "1d6", "gp_value": 5, "usable_by": _combat_classes},
        "Hand Axe": {"damage": "1d6", "gp_value": 4, "usable_by": _combat_classes},
        "Battle Axe": {"damage": "1d8", "gp_value": 7, "usable_by": _combat_classes},
        "Mace": {"damage": "1d6", "gp_value": 5, "usable_by": _combat_classes | {CharacterClassType.CLERIC}},
        "Crossbow": {"damage": "1d4", "gp_value": 30, "usable_by": _combat_classes},
        "Long Bow": {"damage": "1d6", "gp_value": 40, "usable_by": {CharacterClassType.FIGHTER, CharacterClassType.ELF}},
        "Short Bow": {"damage": "1d6", "gp_value": 25, "usable_by": _combat_classes},
        "Sword": {"damage": "1d8", "gp_value": 10, "usable_by": _combat_classes},
        "Short Sword": {"damage": "1d6", "gp_value": 7, "usable_by": _combat_classes},
        "Two-handed Sword": {"damage": "1d10", "gp_value": 15, "usable_by": {CharacterClassType.FIGHTER, CharacterClassType.ELF}},
        "Pole Arm": {"damage": "1d10", "gp_value": 7, "usable_by": {CharacterClassType.FIGHTER, CharacterClassType.ELF, CharacterClassType.DWARF}},
        "Spear": {"damage": "1d6", "gp_value": 3, "usable_by": _combat_classes | {CharacterClassType.CLERIC}},
        "War Hammer": {"damage": "1d6", "gp_value": 5, "usable_by": _combat_classes | {CharacterClassType.CLERIC}}
    }

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
                gp_value=equipment_data[item_name]
            )
        else:
            raise ValueError(f"No data available for item: {item_name}")

class WeaponFactory:
    """Factory class to create items of type ``Weapon``."""

    @staticmethod
    def create_weapon(name: str):
        weapon_info = weapon_data.get(name)
        if weapon_info:
            return Weapon(
                name=name,
                to_hit_damage_die=weapon_info['damage'],
                gp_value=weapon_info['gp_value'],
                usable_by_classes=weapon_info['usable_by']
            )

        else:
            raise ValueError(f"Weapon '{name}' not found in weapons data.")


# Usage example:
try:
    dagger_for_mage = WeaponFactory.create_weapon("Dagger")
    print(dagger_for_mage)

    thief_tools = EquipmentFactory.create_item("Thieves' Tools")
    print(thief_tools)
except ValueError as e:
    print(e)

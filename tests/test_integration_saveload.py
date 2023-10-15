import os
import pytest
from tinydb import Query, TinyDB

from osrlib import PlayerCharacter, item, character_classes, game_manager as gm
from osrlib.ability import (
    Strength,
    Intelligence,
    Wisdom,
    Dexterity,
    Constitution,
    Charisma,
)
from osrlib.combat import ModifierType


test_fighter = PlayerCharacter("Test Fighter", character_classes.CharacterClassType.FIGHTER)
test_elf = PlayerCharacter("Test Elf", character_classes.CharacterClassType.ELF)
test_magic_user = PlayerCharacter("Test Magic User", character_classes.CharacterClassType.MAGIC_USER)


@pytest.fixture
def db():
    db_path = "test_db.json"
    full_path = os.path.abspath(db_path)
    gm.logger.info(f"Creating TinyDB @ {full_path}")
    db = TinyDB(db_path)
    gm.logger.info(f"Created TinyDB: {db}")
    yield db
    gm.logger.info(f"Dropping tables from TinyDB: {db}")
    db.drop_tables()
    gm.logger.info(f"Closing TinyDB: {db}")
    db.close()


def test_abilities_saveload(db):
    table = db.table("abilities")

    # Create ability instances
    str_ability = Strength(16)
    int_ability = Intelligence(18)
    wis_ability = Wisdom(12)
    dex_ability = Dexterity(14)
    con_ability = Constitution(5)
    cha_ability = Charisma(18)

    # Generate dicts
    str_dict = str_ability.to_dict()
    int_dict = int_ability.to_dict()
    wis_dict = wis_ability.to_dict()
    dex_dict = dex_ability.to_dict()
    con_dict = con_ability.to_dict()
    cha_dict = cha_ability.to_dict()

    # Save to DB
    str_id = table.insert(str_dict)
    int_id = table.insert(int_dict)
    wis_id = table.insert(wis_dict)
    dex_id = table.insert(dex_dict)
    con_id = table.insert(con_dict)
    cha_id = table.insert(cha_dict)

    # Load from DB
    str_loaded_dict = table.get(doc_id=str_id)
    int_loaded_dict = table.get(doc_id=int_id)
    wis_loaded_dict = table.get(doc_id=wis_id)
    dex_loaded_dict = table.get(doc_id=dex_id)
    con_loaded_dict = table.get(doc_id=con_id)
    cha_loaded_dict = table.get(doc_id=cha_id)

    str_loaded = Strength.from_dict(str_loaded_dict)
    int_loaded = Intelligence.from_dict(int_loaded_dict)
    wis_loaded = Wisdom.from_dict(wis_loaded_dict)
    dex_loaded = Dexterity.from_dict(dex_loaded_dict)
    con_loaded = Constitution.from_dict(con_loaded_dict)
    cha_loaded = Charisma.from_dict(cha_loaded_dict)

    # Assertions - test that the loaded objects are equal to the original objects, specifically that the
    # ability scores and modifiers are equal.
    # TODO: Add assertions for prime requisite classes once prime requisite classes are implemented.
    assert str_loaded.score == 16
    assert str_loaded.modifiers[ModifierType.TO_HIT] == 2
    assert str_loaded.modifiers[ModifierType.DAMAGE] == 2
    assert str_loaded.modifiers[ModifierType.OPEN_DOORS] == 2

    assert int_loaded.score == 18
    assert int_loaded.modifiers[ModifierType.LANGUAGES] == 3

    assert wis_loaded.score == 12
    assert wis_loaded.modifiers[ModifierType.SAVING_THROWS] == 0

    assert dex_loaded.score == 14
    assert dex_loaded.modifiers[ModifierType.AC] == -1
    assert dex_loaded.modifiers[ModifierType.TO_HIT] == 1
    assert dex_loaded.modifiers[ModifierType.INITIATIVE] == 1

    assert con_loaded.score == 5
    assert con_loaded.modifiers[ModifierType.HP] == -2

    assert cha_loaded.score == 18
    assert cha_loaded.modifiers[ModifierType.REACTION] == 2


def test_item_saveload(db):
    item_table = db.table("items")

    # Create an Item instance
    usable_by = {
        character_classes.CharacterClassType.FIGHTER,
        character_classes.CharacterClassType.THIEF,
    }
    original_item = item.Item("50' rope", item.ItemType.ITEM, usable_by, max_equipped=0, gp_value=5)

    # Serialize and insert into DB
    item_dict = original_item.to_dict()
    item_table.insert(item_dict)

    # Retrieve and deserialize
    ItemQuery = Query()
    retrieved_item_dict = item_table.search(ItemQuery.name == "50' rope")[0]
    retrieved_item = item.Item.from_dict(retrieved_item_dict)

    # Assertions to check if deserialization was correct
    assert original_item.name == retrieved_item.name
    assert original_item.item_type == retrieved_item.item_type
    assert original_item.usable_by_classes == retrieved_item.usable_by_classes
    assert original_item.max_equipped == retrieved_item.max_equipped
    assert original_item.gp_value == retrieved_item.gp_value


def test_armor_saveload(db):
    item_table = db.table("armor")

    # Create an Item instance
    usable_by = {
        character_classes.CharacterClassType.FIGHTER,
        character_classes.CharacterClassType.ELF,
    }
    original_item = item.Armor("Chain Mail", -4, usable_by_classes=usable_by, max_equipped=1, gp_value=40)

    # Serialize and insert into DB
    item_dict = original_item.to_dict()
    item_table.insert(item_dict)

    # Retrieve and deserialize
    ItemQuery = Query()
    retrieved_item_dict = item_table.search(ItemQuery.name == "Chain Mail")[0]
    retrieved_item = item.Armor.from_dict(retrieved_item_dict)

    # Assertions to check if deserialization was correct
    assert retrieved_item.item_type == item.ItemType.ARMOR
    assert original_item.name == retrieved_item.name
    assert original_item.item_type == retrieved_item.item_type
    assert original_item.usable_by_classes == retrieved_item.usable_by_classes
    assert original_item.max_equipped == retrieved_item.max_equipped
    assert original_item.gp_value == retrieved_item.gp_value
    assert original_item.ac_modifier == retrieved_item.ac_modifier


def test_weapon_saveload(db):
    item_table = db.table("weapon")

    # Create an Item instance
    usable_by = {
        character_classes.CharacterClassType.FIGHTER,
        character_classes.CharacterClassType.ELF,
    }
    original_sword = item.Weapon(
        "Sword",
        to_hit_damage_die="1d8",
        usable_by_classes=usable_by,
        max_equipped=1,
        gp_value=40,
    )

    # Serialize and insert into DB
    item_dict = original_sword.to_dict()
    item_table.insert(item_dict)

    # Retrieve and deserialize
    ItemQuery = Query()
    retrieved_sword_dict = item_table.search(ItemQuery.name == "Sword")[0]
    retrieved_sword = item.Weapon.from_dict(retrieved_sword_dict)

    # Assertions to check if deserialization was correct
    assert retrieved_sword.item_type == item.ItemType.WEAPON
    assert original_sword.name == retrieved_sword.name
    assert original_sword.item_type == retrieved_sword.item_type
    assert original_sword.usable_by_classes == retrieved_sword.usable_by_classes
    assert original_sword.max_equipped == retrieved_sword.max_equipped
    assert original_sword.gp_value == retrieved_sword.gp_value
    assert original_sword.to_hit_damage_die == retrieved_sword.to_hit_damage_die
    assert original_sword.range == None

    # Add weapon to test_fighter's inventory and equip it
    test_fighter.inventory.add_item(retrieved_sword)
    test_fighter.inventory.equip_item(retrieved_sword)
    assert retrieved_sword.is_equipped == True
    assert retrieved_sword.owner == test_fighter
    test_fighter.inventory.unequip_item(retrieved_sword)
    test_fighter.inventory.remove_item(retrieved_sword)

    # Add weapon to test_elf's inventory and equip it
    test_elf.inventory.add_item(retrieved_sword)
    test_elf.inventory.equip_item(retrieved_sword)
    assert retrieved_sword.is_equipped == True
    assert retrieved_sword.owner == test_elf
    test_elf.inventory.unequip_item(retrieved_sword)
    test_elf.inventory.remove_item(retrieved_sword)

    # Add weapon to test_magic_user's inventory and try to equip it
    test_magic_user.inventory.add_item(retrieved_sword)
    try:
        test_magic_user.inventory.equip_item(retrieved_sword)
    except item.ItemNotUsableError as e:
        assert isinstance(e, item.ItemNotUsableError)
    test_magic_user.inventory.remove_item(retrieved_sword)


def test_spell_saveload(db):
    item_table = db.table("spell")

    # Create a Spell instance
    usable_by = {character_classes.CharacterClassType.MAGIC_USER}
    original_spell = item.Spell(
        "Fireball",
        spell_level=3,
        damage_die="8d6",
        range=150,
        duration_turns=None,
        usable_by_classes=usable_by,
        max_equipped=1,
        gp_value=0,
    )

    # Serialize and insert into DB
    spell_dict = original_spell.to_dict()
    item_table.insert(spell_dict)

    # Retrieve and deserialize
    ItemQuery = Query()
    retrieved_spell_dict = item_table.search(ItemQuery.name == "Fireball")[0]
    retrieved_spell = item.Spell.from_dict(retrieved_spell_dict)

    # Assertions to check if deserialization was correct
    assert retrieved_spell.item_type == item.ItemType.SPELL
    assert original_spell.name == retrieved_spell.name
    assert original_spell.item_type == retrieved_spell.item_type
    assert original_spell.usable_by_classes == retrieved_spell.usable_by_classes
    assert original_spell.max_equipped == retrieved_spell.max_equipped
    assert original_spell.gp_value == retrieved_spell.gp_value
    assert original_spell.spell_level == retrieved_spell.spell_level
    assert original_spell.range == retrieved_spell.range
    assert original_spell.damage_die == retrieved_spell.damage_die
    assert original_spell.duration_turns == retrieved_spell.duration_turns

    # Add spell to test_magic_user's inventory and equip it
    test_magic_user.inventory.add_item(retrieved_spell)
    test_magic_user.inventory.equip_item(retrieved_spell)
    assert retrieved_spell.is_equipped == True
    assert retrieved_spell.owner == test_magic_user
    test_magic_user.inventory.unequip_item(retrieved_spell)
    test_magic_user.inventory.remove_item(retrieved_spell)

    # Add spell to test_fighter's inventory and try to equip it
    try:
        test_fighter.inventory.add_item(retrieved_spell)
        test_fighter.inventory.equip_item(retrieved_spell)
    except item.ItemNotUsableError as e:
        assert isinstance(e, item.ItemNotUsableError)
    test_fighter.inventory.remove_item(retrieved_spell)


def test_item_autoset_attributes_preserved_on_saveload(db):
    """Tests whether a loaded item's dynamically assigned attribute values are preserved through the save/load process.

    For example, the is_usable attribute is determined by the owner's character class, and the is_equipped attribute
    is set by calling the owner's inventory.equip_item() method. Thus, we need to ensure those dynamically assigned
    attribute values are saved to and loaded from the DB as expected.

    The handling of resetting the attribute values on the reconstituted items is (TODO: will be) handled in the
    PlayerCharacter.from_dict() method and won't need to be handled manually by the library user as we're doing here.
    """
    item_table = db.table("item")

    # Step 1: Create instances
    armor = item.Armor(
        "Plate Mail Armor",
        gp_value=50,
        max_equipped=1,
        usable_by_classes={character_classes.CharacterClassType.FIGHTER},
    )
    weapon = item.Weapon(
        "Sword",
        "1d8",
        gp_value=30,
        max_equipped=1,
        usable_by_classes={character_classes.CharacterClassType.FIGHTER},
    )
    normal_item = item.Item("50' rope", item.ItemType.EQUIPMENT, gp_value=1, max_equipped=0)

    # Step 2: Add to test_fighter's inventory
    test_fighter.inventory.add_item(armor)
    test_fighter.inventory.add_item(weapon)
    test_fighter.inventory.add_item(normal_item)

    # Step 3: Equip armor and weapon
    test_fighter.inventory.equip_item(armor)
    test_fighter.inventory.equip_item(weapon)

    # Step 4: Serialize and save to DB
    armor_dict, weapon_dict, normal_item_dict = (
        armor.to_dict(),
        weapon.to_dict(),
        normal_item.to_dict(),
    )
    item_table.insert_multiple([armor_dict, weapon_dict, normal_item_dict])

    # Step 4.1: Empty the character's inventory so we can re-add the items that we
    #           retrieve from the DB. If we don't do this, we won't be able to equip
    #           the items we retrieve from the DB because the character will already
    #           have them in the the max number of items equipped for each.
    #           This step will NOT be needed during a normal deserialization of a
    #           PlayerCharacter object because the PlayerCharacter's inventory will
    #           be empty when the PC is deserialized.
    test_fighter.inventory.items.clear()

    # Step 5: Load from DB and assert 'is_equipped' attribute
    ItemQuery = Query()
    retrieved_armor_dict = item_table.search(ItemQuery.name == "Plate Mail Armor")[0]
    retrieved_weapon_dict = item_table.search(ItemQuery.name == "Sword")[0]
    retrieved_normal_item_dict = item_table.search(ItemQuery.name == "50' rope")[0]

    retrieved_armor = item.Armor.from_dict(retrieved_armor_dict)
    retrieved_weapon = item.Weapon.from_dict(retrieved_weapon_dict)
    retrieved_normal_item = item.Item.from_dict(retrieved_normal_item_dict)

    # Step 6: Set the item's owner and equip previously equipped items.
    #         This is necessary because the owner attribute is not serialized and the
    #         is_usable attribute is determined by the owner's character class. Thus,
    #         just setting the is_equipped attribute to True is not enough to re-equip
    #         an item - it needs to be added to their inventory and then equipped.
    #         TODO: Handle this re-adding and re-equipping of loaded items in the PlayerCharacter.from_dict().
    test_fighter.inventory.add_item(retrieved_armor)
    test_fighter.inventory.add_item(retrieved_weapon)
    test_fighter.inventory.add_item(retrieved_normal_item)
    if retrieved_armor_dict["is_equipped"]:
        test_fighter.inventory.equip_item(retrieved_armor)
    if retrieved_weapon_dict["is_equipped"]:
        test_fighter.inventory.equip_item(retrieved_weapon)
    if retrieved_normal_item_dict["is_equipped"]:
        test_fighter.inventory.equip_item(retrieved_normal_item)

    assert retrieved_armor.is_equipped == True
    assert retrieved_weapon.is_equipped == True
    assert retrieved_normal_item.is_equipped == False

    # Step 7: Clean up
    # TODO: Add an Inventory.drop_all_items() method to make this easier.
    test_fighter.inventory.unequip_item(retrieved_armor)
    test_fighter.inventory.unequip_item(retrieved_weapon)
    test_fighter.inventory.remove_item(retrieved_armor)
    test_fighter.inventory.remove_item(retrieved_weapon)
    test_fighter.inventory.remove_item(retrieved_normal_item)

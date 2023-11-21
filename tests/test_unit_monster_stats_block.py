import pytest
from unittest.mock import Mock
from osrlib.monster import MonsterStatsBlock, CharacterClassType, TreasureType, Alignment

@pytest.fixture
def default_monster_stats_block():
    return MonsterStatsBlock(name="Test Monster")

def test_initialization_with_default_values(default_monster_stats_block):
    assert default_monster_stats_block.name == "Test Monster"
    assert default_monster_stats_block.description == ""
    assert default_monster_stats_block.armor_class == 10
    assert default_monster_stats_block.hit_dice == "1d8"
    assert default_monster_stats_block.movement == 120
    assert default_monster_stats_block.num_special_abilities == 0
    assert default_monster_stats_block.attacks_per_round == 1
    assert default_monster_stats_block.damage_per_attack == "1d4"
    assert default_monster_stats_block.num_appearing_dice_string == "1d6"
    assert default_monster_stats_block.save_as_class == CharacterClassType.FIGHTER
    assert default_monster_stats_block.save_as_level == 1
    assert default_monster_stats_block.morale == 12
    assert default_monster_stats_block.treasure_type == TreasureType.NONE
    assert default_monster_stats_block.alignment == Alignment.NEUTRAL

def test_initialization_with_custom_values():
    custom_monster = MonsterStatsBlock(
        name="Custom Monster",
        description="A custom test monster",
        armor_class=8,
        hit_dice="2d8+2",
        movement=100,
        num_special_abilities=2,
        attacks_per_round=2,
        damage_per_attack="2d6",
        num_appearing="2d4",
        save_as_class=CharacterClassType.MAGIC_USER,
        save_as_level=3,
        morale=10,
        treasure_type=TreasureType.A,
        alignment=Alignment.CHAOTIC
    )
    assert custom_monster.name == "Custom Monster"
    assert custom_monster.description == "A custom test monster"
    assert custom_monster.armor_class == 8
    assert custom_monster.hit_dice == "2d8+2"
    assert custom_monster.movement == 100
    assert custom_monster.num_special_abilities == 2
    assert custom_monster.attacks_per_round == 2
    assert custom_monster.damage_per_attack == "2d6"
    assert custom_monster.num_appearing_dice_string == "2d4"
    assert custom_monster.save_as_class == CharacterClassType.MAGIC_USER
    assert custom_monster.save_as_level == 3
    assert custom_monster.morale == 10
    assert custom_monster.treasure_type == TreasureType.A
    assert custom_monster.alignment == Alignment.CHAOTIC

def test_to_dict(default_monster_stats_block):
    monster_dict = default_monster_stats_block.to_dict()
    assert monster_dict["name"] == "Test Monster"
    assert monster_dict["description"] == ""
    assert monster_dict["armor_class"] == 10
    assert monster_dict["hit_dice"] == "1d8"
    assert monster_dict["movement"] == 120
    assert monster_dict["num_special_abilities"] == 0
    assert monster_dict["attacks_per_round"] == 1
    assert monster_dict["damage_per_attack"] == "1d4"
    assert monster_dict["num_appearing"] == "1d6"
    assert monster_dict["save_as_class"] == "FIGHTER"
    assert monster_dict["save_as_level"] == 1
    assert monster_dict["morale"] == 12
    assert monster_dict["treasure_type"] == "NONE"
    assert monster_dict["alignment"] == "NEUTRAL"

def test_from_dict():
    monster_dict = {
        "name": "Dict Monster",
        "description": "A monster from dict",
        "armor_class": 12,
        "hit_dice": "3d6",
        "movement": 150,
        "num_special_abilities": 1,
        "attacks_per_round": 2,
        "damage_per_attack": "1d8",
        "num_appearing": "3d4",
        "save_as_class": "MAGIC_USER",
        "save_as_level": 2,
        "morale": 15,
        "treasure_type": "A",
        "alignment": "CHAOTIC"
    }
    monster = MonsterStatsBlock.from_dict(monster_dict)
    assert monster.name == "Dict Monster"
    assert monster.description == "A monster from dict"
    assert monster.armor_class == 12
    assert monster.hit_dice == "3d6"
    assert monster.movement == 150
    assert monster.num_special_abilities == 1
    assert monster.attacks_per_round == 2
    assert monster.damage_per_attack == "1d8"
    assert monster.num_appearing_dice_string == "3d4"
    assert monster.save_as_class == CharacterClassType.MAGIC_USER
    assert monster.save_as_level == 2
    assert monster.morale == 15
    assert monster.treasure_type == TreasureType.A
    assert monster.alignment == Alignment.CHAOTIC

def test_error_handling_with_missing_keys():
    incomplete_dict = {"name": "Incomplete Monster"}
    with pytest.raises(KeyError):
        MonsterStatsBlock.from_dict(incomplete_dict)

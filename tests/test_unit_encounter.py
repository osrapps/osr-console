import pytest
from osrlib.encounter import Encounter
from osrlib.monster import MonsterParty, MonsterStatsBlock
from osrlib.character_classes import CharacterClassType
from osrlib.player_character import Alignment
from osrlib.treasure import TreasureType

@pytest.fixture
def goblin_party():
    stats = MonsterStatsBlock(
        name="Goblin",
        description="A small incredibly ugly humanoid with pale earthy color skin, like a chalky tan or livid gray.",
        armor_class=6,
        hit_dice="1d8-1",
        num_appearing="2d4",
        movement=60,
        num_special_abilities=0,
        attacks_per_round=1,
        damage_per_attack="1d6",
        save_as_class=CharacterClassType.COMMONER,
        save_as_level=1,
        morale=7,
        treasure_type=TreasureType.R,
        alignment=Alignment.CHAOTIC
    )
    monster_party = MonsterParty(stats)
    yield monster_party

@pytest.fixture
def hobgoblin_party():
    stats = MonsterStatsBlock(
        name="Hobgoblin",
        description="A larger and meaner relative of the goblin.",
        armor_class=6,
        hit_dice="1d8+1",
        num_appearing="1d6",
        movement=90,
        num_special_abilities=0,
        attacks_per_round=1,
        damage_per_attack="1d8",
        save_as_class=CharacterClassType.FIGHTER,
        save_as_level=1,
        morale=8,
        treasure_type=TreasureType.D,
        alignment=Alignment.CHAOTIC
    )
    monster_party = MonsterParty(stats)
    yield monster_party


@pytest.fixture
def kobold_party():
    stats = MonsterStatsBlock(
        name="Kobold",
        description="A small, lizard-like humanoid.",
        armor_class=7,
        hit_dice="1d4",
        num_appearing="4d4",
        movement=60,
        num_special_abilities=0,
        attacks_per_round=1,
        damage_per_attack="1d4",
        save_as_class=CharacterClassType.FIGHTER,
        save_as_level=1,
        morale=6,
        treasure_type=TreasureType.P,
        alignment=Alignment.CHAOTIC
    )
    monster_party = MonsterParty(stats)
    yield monster_party

def test_encounter_initialization(kobold_party):
    encounter = Encounter("Test Kobold Encounter", "A test encounter with a party of kobolds.", kobold_party)

    assert encounter.name == "Test Kobold Encounter"
    assert encounter.description == "A test encounter with a party of kobolds."
    assert encounter.monster_party == kobold_party

    # TODO: These should probably move to a test for MonsterParty
    assert len(encounter.monster_party.monsters) >= 4 and len(encounter.monster_party.monsters) <= 16
    assert encounter.monster_party.xp_value == len(kobold_party.monsters) * 5 # Under 1 HD = 5 XP

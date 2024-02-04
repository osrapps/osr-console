import pytest
import random
from osrlib.encounter import Encounter
from osrlib.monster import MonsterParty
from osrlib.monster_manual import monster_stats_blocks
from osrlib.game_manager import logger

@pytest.fixture
def random_monster_party():
    # Randomly select a MonsterStatsBlock from the monster_manual for testing
    random_stats_block = random.choice(monster_stats_blocks)
    monster_party = MonsterParty(random_stats_block)
    return monster_party

def test_encounter_initialization(random_monster_party):
    logger.debug(f"Testing encounter with monster party: {random_monster_party}")
    encounter = Encounter("Test Encounter", "A test encounter with monsters.", random_monster_party)

    assert encounter.name == "Test Encounter"
    assert encounter.description == "A test encounter with monsters."
    assert encounter.monster_party == random_monster_party

    # Handle dice strings like "d1"
    num_appearing_range = encounter.monster_party.monster_stats_block.num_appearing_dice_string
    parts = num_appearing_range.split('d')
    min_appearing = int(parts[0]) if parts[0] else 1  # Default to 1 if no leading number
    max_appearing = int(parts[1])

    assert min_appearing <= len(encounter.monster_party.members) <= (min_appearing * max_appearing)

    # Ensure the XP calc is working - should be each monsters' XP + the group XP value (if any)
    expected_xp = sum(member.xp_value for member in encounter.monster_party.members)
    expected_xp += encounter.monster_party.treasure.total_gp_value
    assert encounter.monster_party.xp_value == expected_xp

def test_encounter_to_dict(random_monster_party):
    encounter = Encounter("Test Encounter", "A test encounter with monsters.", random_monster_party)
    encounter_dict = encounter.to_dict()

    # Check if the dictionary contains the correct keys and their associated values
    assert encounter_dict["name"] == "Test Encounter"
    assert encounter_dict["description"] == "A test encounter with monsters."
    assert isinstance(encounter_dict["monsters"], dict)  # The monster party should be a dictionary
    assert encounter_dict["monsters"]["name"] == random_monster_party.monster_stats_block.name  # Check if monster party is correctly serialized

def test_encounter_from_dict(random_monster_party):
    # Create an Encounter instance and serialize it to a dictionary
    encounter = Encounter("Test Encounter", "A test encounter with monsters.", random_monster_party)
    encounter_dict = encounter.to_dict()

    # Deserialize the dictionary back into an Encounter instance
    rehydrated_encounter = Encounter.from_dict(encounter_dict)

    # Check if the rehydrated encounter has the same attributes as the original
    assert rehydrated_encounter.name == encounter.name
    assert rehydrated_encounter.description == encounter.description
    assert rehydrated_encounter.monster_party.monster_stats_block.name == random_monster_party.monster_stats_block.name

    # Additional checks can be added to verify the integrity of the rehydrated monster party

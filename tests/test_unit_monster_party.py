import pytest
import random
from osrlib.monster import MonsterParty
from osrlib.monster_manual import monster_stats_blocks

@pytest.fixture
def random_monster_stats_block():
    # Randomly select a MonsterStatsBlock for the tests
    return random.choice(monster_stats_blocks)

def test_monster_party_initialization(random_monster_stats_block):
    party = MonsterParty(random_monster_stats_block)
    assert isinstance(party.members, list)
    assert len(party.members) > 0  # Ensure that members are created
    assert party.monster_stats_block == random_monster_stats_block

def test_is_alive_property(random_monster_stats_block):
    party = MonsterParty(random_monster_stats_block)
    assert isinstance(party.is_alive, bool)  # is_alive should be a boolean

def test_xp_value_property(random_monster_stats_block):
    party = MonsterParty(random_monster_stats_block)
    assert isinstance(party.xp_value, int)  # xp_value should be an integer
    assert party.xp_value >= 0  # xp_value should be non-negative

def test_get_surprise_roll(random_monster_stats_block):
    party = MonsterParty(random_monster_stats_block)
    surprise_roll = party.get_surprise_roll()
    assert isinstance(surprise_roll, int)
    assert 1 <= surprise_roll <= 6  # Validate the dice roll range

def test_to_dict_method(random_monster_stats_block):
    party = MonsterParty(random_monster_stats_block)
    party_dict = party.to_dict()
    assert isinstance(party_dict, dict)
    # Asserting the dictionary contains the keys from MonsterStatsBlock
    assert "name" in party_dict and "num_appearing" in party_dict

def test_from_dict_method(random_monster_stats_block):
    og_party = MonsterParty(random_monster_stats_block)
    og_monster_party_stats_block_dict = og_party.to_dict()
    new_party = MonsterParty.from_dict(og_monster_party_stats_block_dict)
    assert isinstance(new_party, MonsterParty)
    assert new_party.monster_stats_block.name == og_party.monster_stats_block.name  # Cross-check a key attribute
    assert len(new_party.members) > 0  # Ensure that members were created

# Additional tests can be added to cover edge cases, error handling, etc.


class _FakeTreasure:
    def __init__(self, xp_gp_value: int):
        self.xp_gp_value = xp_gp_value


def test_xp_value_uses_base_xp_plus_treasure_xp():
    party = MonsterParty(random.choice(monster_stats_blocks))
    party.members = party.members[:1]

    party.members[0].xp_value = 12
    party.members[0].treasure = _FakeTreasure(xp_gp_value=30)
    party.treasure = _FakeTreasure(xp_gp_value=40)

    assert party.xp_value == 82

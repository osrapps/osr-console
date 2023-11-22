import pytest
from osrlib.adventure import Adventure
from osrlib.dungeon import Dungeon
from osrlib.party import get_default_party

@pytest.fixture
def sample_adventure():
    # Create a simple adventure with a couple of dungeons
    dungeon1 = Dungeon(name="Dungeon 1")
    dungeon2 = Dungeon(name="Dungeon 2")
    return Adventure(name="Test Adventure", description="A simple test adventure.", dungeons=[dungeon1, dungeon2])

def test_adventure_to_dict(sample_adventure):
    default_party = get_default_party()
    sample_adventure.set_active_party(default_party)
    sample_adventure.set_active_dungeon(sample_adventure.dungeons[0])

    adventure_dict = sample_adventure.to_dict()

    # Verify that the adventure attributes are correctly serialized
    assert adventure_dict["name"] == "Test Adventure"
    assert adventure_dict["description"] == "A simple test adventure."
    assert len(adventure_dict["dungeons"]) == 2
    assert adventure_dict["active_dungeon"]["name"] == sample_adventure.dungeons[0].name
    assert adventure_dict["active_party"]["name"] == default_party.name

def test_adventure_from_dict(sample_adventure):
    default_party = get_default_party()
    sample_adventure.set_active_party(default_party)
    sample_adventure.set_active_dungeon(sample_adventure.dungeons[0])

    adventure_dict = sample_adventure.to_dict()

    # Deserialize the dictionary back into an Adventure instance
    rehydrated_adventure = Adventure.from_dict(adventure_dict)

    # Verify that the rehydrated adventure has the same attributes as the original
    assert rehydrated_adventure.name == sample_adventure.name
    assert rehydrated_adventure.description == sample_adventure.description
    assert len(rehydrated_adventure.dungeons) == len(sample_adventure.dungeons)
    assert rehydrated_adventure.active_dungeon.name == sample_adventure.dungeons[0].name
    assert rehydrated_adventure.active_party.name == default_party.name

import pytest
from osrlib import party, player_character, character_classes


@pytest.fixture
def setup_party():
    empty_test_party = party.Party("The B-Team", 3)
    character1 = player_character.PlayerCharacter("Sckricko", character_classes.CharacterClassType.FIGHTER, 1)
    character2 = player_character.PlayerCharacter("Mazpar", character_classes.CharacterClassType.MAGIC_USER, 1)
    character3 = player_character.PlayerCharacter("Slick", character_classes.CharacterClassType.THIEF, 1)
    return empty_test_party, character1, character2, character3


def test_add_firstcharacter(setup_party):
    test_party, character1, _, _ = setup_party
    test_party.add_character(character1)
    assert character1 in test_party.characters


def test_add_character_at_capacity(setup_party):
    test_party, character1, character2, character3 = setup_party
    max_capacity = test_party.max_party_members  # Replace with how you get the max_capacity

    # Fill the party to max_capacity - 1 with uniquely named characters
    for i in range(max_capacity - 1):
        new_character = player_character.PlayerCharacter(
            f"Test Character {i}", character_classes.CharacterClassType.FIGHTER, 1
        )
        test_party.add_character(new_character)

    # Adding one more should work
    test_party.add_character(character1)

    # Adding one more beyond that should raise PartyAtCapacityError
    with pytest.raises(party.PartyAtCapacityError):
        test_party.add_character(character2)


def test_remove_character(setup_party):
    test_party, character1, _, _ = setup_party
    test_party.add_character(character1)
    test_party.remove_character(character1)
    assert character1 not in test_party.characters


def test_remove_character_not_in_party(setup_party):
    test_party, character1, _, _ = setup_party
    with pytest.raises(party.CharacterNotInPartyError):
        test_party.remove_character(character1)


def test_get_character_by_name(setup_party):
    test_party, character1, character2, character3 = setup_party
    test_party.add_character(character1)
    test_party.add_character(character2)
    test_party.add_character(character3)
    assert test_party.get_character_by_name("Mazpar") == character2


def test_get_character_by_name_not_in_party(setup_party):
    test_party, _, _, _ = setup_party
    assert test_party.get_character_by_name("Mazpar") is None


def test_get_character_by_index(setup_party):
    test_party, character1, character2, character3 = setup_party
    test_party.add_character(character1)
    test_party.add_character(character2)
    test_party.add_character(character3)
    assert test_party.get_character_by_index(1) == character2


def test_get_character_by_index_out_of_range(setup_party):
    test_party, _, _, _ = setup_party
    assert test_party.get_character_by_index(3) is None


def test_get_character_index(setup_party):
    test_party, character1, character2, character3 = setup_party
    test_party.add_character(character1)
    test_party.add_character(character2)
    test_party.add_character(character3)
    assert test_party.get_character_index(character2) == 1


def test_get_character_index_not_in_party(setup_party):
    test_party, character1, _, _ = setup_party
    with pytest.raises(party.CharacterNotInPartyError):
        test_party.get_character_index(character1)


def test_move_character_to_index(setup_party):
    test_party, character1, character2, character3 = setup_party
    test_party.add_character(character1)
    test_party.add_character(character2)
    test_party.add_character(character3)
    test_party.move_character_to_index(character2, 0)
    assert test_party.get_character_by_index(0) == character2


def test_move_character_to_index_not_in_party(setup_party):
    test_party, character1, _, _ = setup_party
    with pytest.raises(party.CharacterNotInPartyError):
        test_party.move_character_to_index(character1, 0)


def test_move_character_to_index_out_of_range(setup_party):
    test_party, character1, character2, character3 = setup_party
    test_party.add_character(character1)
    test_party.add_character(character2)
    test_party.add_character(character3)
    with pytest.raises(IndexError):
        test_party.move_character_to_index(character2, 3)


def test_clear_party(setup_party):
    test_party, character1, character2, character3 = setup_party
    test_party.add_character(character1)
    test_party.add_character(character2)
    test_party.add_character(character3)
    test_party.clear_party()
    assert len(test_party.characters) == 0

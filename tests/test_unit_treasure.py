import pytest
from osrlib.enums import CoinType, ItemType
from osrlib.treasure import Treasure, TreasureDetail, TreasureType


def test_treasure_total_gold_piece_value():
    custom_type = {
        CoinType.GOLD: TreasureDetail(
            # Always 10 GP
            chance=100, amount="10", magical=False
        ),
        CoinType.SILVER: TreasureDetail(
            # Always 100 SP
            chance=100, amount="100", magical=False
        ),
    }
    treasure = Treasure.from_custom_type(custom_type)
    expected_total_gp = 20  # 10 GP + 100 SP (10 SP = 1 GP)
    assert treasure.total_gp_value == expected_total_gp

@pytest.mark.flaky(reruns=5) # Flaky because we can't guarantee an average of exactly 50% of getting a magic item.
def test_treasure_from_custom_type():
    # Define a custom treasure type with specific items
    custom_type = {
        CoinType.GOLD: TreasureDetail(
            # Always 5 GP
            chance=100, amount="5", magical=False
        ),
        ItemType.MAGIC_ITEM: TreasureDetail(
            chance=50, amount="1", magical=True
        ),  # 50% chance of 1 magic item
    }

    # Create a Treasure instance using the custom treasure type
    custom_treasure = Treasure.from_custom_type(custom_type)

    # Check if the treasure contains the expected items
    assert CoinType.GOLD in custom_treasure.items
    assert custom_treasure.items[CoinType.GOLD] == 5  # Should always have 5 gold coins

    # Since magic item appearance is probabilistic, we test it statistically
    magic_item_appearances = [
        Treasure.from_custom_type(custom_type).items.get(ItemType.MAGIC_ITEM, 0) > 0
        for _ in range(100)
    ]
    approx_magic_item_appearance_rate = sum(magic_item_appearances) / len(
        magic_item_appearances
    )

    # Check if the appearance rate of the magic item is close to the expected 50%
    assert 0.4 <= approx_magic_item_appearance_rate <= 0.6

@pytest.mark.flaky(reruns=5) # Flaky because we can't guarantee exact average percentages of rolled treasure types.
def test_treasure_predefined_treasure_type_statistics():
    iterations = 1000  # Number of iterations to average out randomness
    type_a_probabilities = {
        CoinType.GOLD: 35,  # Probability in percent for CoinType.GOLD in TreasureType.A
        ItemType.MAGIC_ITEM: 30,  # Probability in percent for ItemType.MAGIC_ITEM in TreasureType.A
        # TODO: add other item types and their probabilities for TreasureType.A
    }
    type_d_probabilities = {
        CoinType.SILVER: 15,  # Probability in percent for CoinType.SILVER in TreasureType.D
        ItemType.GEMS_JEWELRY: 30,  # Probability in percent for ItemType.GEMS_JEWELRY in TreasureType.D
        # TODO: add other item types and their probabilities for TreasureType.D
    }

    type_a_results = {item_type: 0 for item_type in type_a_probabilities}
    type_d_results = {item_type: 0 for item_type in type_d_probabilities}

    # Generate treasures and record occurrences of each item type
    for _ in range(iterations):
        treasure_a = Treasure(TreasureType.A)
        for item_type in type_a_probabilities:
            if item_type in treasure_a.items:
                type_a_results[item_type] += 1

        treasure_d = Treasure(TreasureType.D)
        for item_type in type_d_probabilities:
            if item_type in treasure_d.items:
                type_d_results[item_type] += 1

    # Check if the occurrence rates are within an acceptable range of their probabilities
    for item_type, probability in type_a_probabilities.items():
        occurrence_rate = (type_a_results[item_type] / iterations) * 100
        assert probability - 5 <= occurrence_rate <= probability + 5

    for item_type, probability in type_d_probabilities.items():
        occurrence_rate = (type_d_results[item_type] / iterations) * 100
        assert probability - 5 <= occurrence_rate <= probability + 5

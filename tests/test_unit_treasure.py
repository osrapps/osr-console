from types import SimpleNamespace

from osrlib.enums import CoinType, ItemType
from osrlib.item import Item
from osrlib.treasure import Treasure, TreasureDetail, TreasureType


def _roll_result(total: int) -> SimpleNamespace:
    return SimpleNamespace(total=total, total_with_modifier=total)


def test_treasure_create_all_types():
    # Loop through the TreasureType enum and create Treasure instances for every type.
    for treasure_type in TreasureType:
        treasure = Treasure(treasure_type)
        assert isinstance(treasure, Treasure)
        assert treasure.treasure_type == treasure_type


def test_xp_gp_value_uses_combined_coin_conversion(monkeypatch):
    custom_type = {
        CoinType.COPPER: TreasureDetail(chance=100, amount="1"),
        CoinType.SILVER: TreasureDetail(chance=100, amount="1"),
    }

    rolls = iter([1, 1, 1, 1])  # chance/amount for CP, then chance/amount for SP
    monkeypatch.setattr("osrlib.treasure.roll_dice", lambda _: _roll_result(next(rolls)))

    treasure = Treasure.from_custom_type(custom_type)
    assert treasure.xp_gp_value == 1
    assert treasure.total_gp_value == 1


def test_gems_jewelry_and_magic_items_have_expected_xp_and_gp_values(monkeypatch):
    custom_type = {
        CoinType.SILVER: TreasureDetail(chance=100, amount="100"),  # 10 GP
        ItemType.GEMS_JEWELRY: TreasureDetail(chance=100, amount="1"),  # 50 GP (patched)
        ItemType.WEAPON: TreasureDetail(chance=100, amount="2", magical=True),  # 2 * 300 GP
    }

    rolls = iter([1, 100, 1, 1, 1, 2])  # chance/amount per entry
    monkeypatch.setattr("osrlib.treasure.roll_dice", lambda _: _roll_result(next(rolls)))
    monkeypatch.setattr("osrlib.treasure.random.choice", lambda _: 50)
    monkeypatch.setattr(
        "osrlib.treasure.get_random_item",
        lambda item_type, magical=False: Item("Magic Weapon", ItemType.WEAPON, gp_value=300),
    )

    treasure = Treasure.from_custom_type(custom_type)

    assert treasure.items[CoinType.SILVER] == 100
    assert treasure.items[ItemType.GEMS_JEWELRY] == 1
    assert len(treasure.magic_items) == 2
    assert treasure.xp_gp_value == 60
    assert treasure.total_gp_value == 660


def test_magic_item_entry_generates_multiple_items(monkeypatch):
    custom_type = {
        ItemType.MAGIC_ITEM: TreasureDetail(chance=100, amount="3", magical=True),
    }

    rolls = iter([1, 3])  # chance/amount for MAGIC_ITEM
    monkeypatch.setattr("osrlib.treasure.roll_dice", lambda _: _roll_result(next(rolls)))

    generated_categories = iter([ItemType.ARMOR, ItemType.WEAPON, ItemType.ARMOR])
    monkeypatch.setattr("osrlib.treasure.random.choice", lambda _: next(generated_categories))
    monkeypatch.setattr(
        Treasure,
        "_magic_item_generators",
        {
            ItemType.ARMOR: lambda: Item("Armor Relic", ItemType.ARMOR, gp_value=100),
            ItemType.WEAPON: lambda: Item("Weapon Relic", ItemType.WEAPON, gp_value=200),
        },
    )

    treasure = Treasure.from_custom_type(custom_type)
    assert len(treasure.magic_items) == 3
    assert [item.item_type for item in treasure.magic_items] == [
        ItemType.ARMOR,
        ItemType.WEAPON,
        ItemType.ARMOR,
    ]
    assert treasure.xp_gp_value == 0
    assert treasure.total_gp_value == 400

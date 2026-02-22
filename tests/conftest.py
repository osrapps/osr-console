import pytest

from osrlib.combat import CombatSide
from osrlib.enums import CharacterClassType
from osrlib.item_factories import equip_party
from osrlib.monster import MonsterParty, MonsterStatsBlock
from osrlib.party import Party
from osrlib.player_character import Alignment, PlayerCharacter
from osrlib.treasure import TreasureType


def pytest_addoption(parser):
    parser.addoption(
        "--run-optin-tests", action="store_true", default=False, help="Include tests marked with the 'optin' marker in the test run."
    )

def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-optin-tests"):
        # Do not NOT exclude tests marked with the 'optin' marker, so return early.
        # The --run-optin-tests option was passed on the command line.
        return
    skip_optin = pytest.mark.skip(reason="Test marked opt-in. To run it, pass --run-optin-tests to pytest at the command line.")
    for item in items:
        if "optin" in item.keywords:
            item.add_marker(skip_optin)


# ---------------------------------------------------------------------------
# Shared combat test fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def default_party():
    """Standard party with equipment, all members at level 1."""
    party = Party.get_default_party()
    equip_party(party)
    return party


@pytest.fixture
def default_party_with_cleric_spells():
    """Standard party with equipment; Cleric leveled to 2 for spell slots."""
    party = Party.get_default_party()
    equip_party(party)
    for pc in party.members:
        if pc.character_class.class_type == CharacterClassType.CLERIC:
            pc.grant_xp(2000)
    return party


@pytest.fixture
def goblin_stats():
    return MonsterStatsBlock(
        name="Goblin",
        description="A small ugly humanoid.",
        armor_class=6,
        hit_dice="1d8",
        num_appearing="2",
        movement=60,
        num_special_abilities=0,
        attacks_per_round=1,
        damage_per_attack="1d6",
        save_as_class=CharacterClassType.FIGHTER,
        save_as_level=1,
        morale=7,
        treasure_type=TreasureType.NONE,
        alignment=Alignment.CHAOTIC,
    )


@pytest.fixture
def goblin_party(goblin_stats):
    return MonsterParty(goblin_stats)


# ---------------------------------------------------------------------------
# Shared combat test helpers
# ---------------------------------------------------------------------------


def find_events(events, event_type):
    """Filter a list of events by type."""
    return [e for e in events if isinstance(e, event_type)]


def find_pc_with_class(engine, class_type):
    """Return (combatant_id, PlayerCharacter) for the first PC of *class_type*.

    Raises ``pytest.fail`` if the deterministic default party doesn't contain
    the requested class (indicates broken test setup, not a skip condition).
    """
    for cid, ref in engine._ctx.combatants.items():
        if ref.side == CombatSide.PC and isinstance(ref.entity, PlayerCharacter):
            if ref.entity.character_class.class_type == class_type:
                return cid, ref.entity
    pytest.fail(f"No {class_type.value} in default party — test setup is broken")

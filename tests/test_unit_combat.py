import pytest
from osrlib.encounter import Encounter
from osrlib.monster import MonsterParty, MonsterStatsBlock
from osrlib.character_classes import CharacterClassType, class_levels
from osrlib.player_character import Alignment
from osrlib.treasure import TreasureType
from osrlib.party import get_default_party, Party
from osrlib.game_manager import logger


# THAC0 data for each class type
class_thac0 = {
    CharacterClassType.FIGHTER: {
        (1, 3): 19,
        (4, 6): 17,
        (7, 9): 14,
        (10, 12): 12,
        (13, 15): 10
    },
    CharacterClassType.CLERIC: {
        (1, 4): 19,
        (5, 8): 17,
        (9, 12): 14,
        (13, 16): 12,
        (17, 20): 10
    },
    CharacterClassType.MAGIC_USER: {
        (1, 5): 19,
        (6, 10): 17,
        (11, 15): 14,
        (16, 20): 12,
        (21, 25): 10
    },
    CharacterClassType.THIEF: None,  # To be defined or mapped to CLERIC
    CharacterClassType.DWARF: None,  # To be defined or mapped to FIGHTER
    CharacterClassType.ELF: None,    # To be defined or mapped to FIGHTER
    CharacterClassType.HALFLING: None,  # To be defined or mapped to FIGHTER
}
# Map shared classes to the same THAC0 values
class_thac0[CharacterClassType.THIEF] = class_thac0[CharacterClassType.CLERIC]
class_thac0[CharacterClassType.DWARF] = class_thac0[CharacterClassType.FIGHTER]
class_thac0[CharacterClassType.ELF] = class_thac0[CharacterClassType.FIGHTER]
class_thac0[CharacterClassType.HALFLING] = class_thac0[CharacterClassType.FIGHTER]


@pytest.fixture
def pc_party():
    yield get_default_party()

@pytest.fixture
def goblin_party():
    stats = MonsterStatsBlock(
        name="Goblin",
        description="A small and incredibly ugly humanoid with pale earthy color skin, like a chalky tan or livid gray.",
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

@pytest.fixture
def goblin_encounter(goblin_party):
    yield Encounter("Goblin Ambush", "A group of goblins ambush the party.", goblin_party)

def get_thac0_for_class_for_level(char_class_type, level):
    for level_range, thac0 in class_thac0[char_class_type].items():
        if level_range[0] <= level <= level_range[1]:
            return thac0
    raise ValueError("Invalid level for class")

def test_thac0_for_classes_and_levels(pc_party):
    for pc in pc_party.members:
        logger.info(f"Testing THAC0 for {pc.name} ({pc.character_class.class_type.value})")

        for level in class_levels[pc.character_class.class_type]:
            # PCs start at level 1 (we're not going to check level 0 NPCs)
            if level.level_num == 0:
                continue

            pc.grant_xp(level.xp_required_for_level)

            expected_thac0 = get_thac0_for_class_for_level(pc.character_class.class_type, pc.character_class.current_level.level_num)
            actual_thac0 = pc.character_class.current_level.get_to_hit_target_ac(0)
            logger.debug(f"[{pc.name}] THAC0 - Expected: {expected_thac0} Actual: {actual_thac0}")

            if expected_thac0 != actual_thac0:
                logger.error(f"[{pc.character_class.class_type.value}] Expected THAC0 {expected_thac0} != Actual THAC0 {actual_thac0} for level {level.level_num}!")

            assert expected_thac0 == actual_thac0

def test_encounter_start_and_end(pc_party, goblin_encounter):
    encounter = goblin_encounter
    assert encounter.is_started == False
    encounter.start_encounter(pc_party)
    assert encounter.is_ended == True

def test_encounter_combat_queue(pc_party, goblin_encounter):
    encounter = goblin_encounter
    encounter.start_encounter(pc_party)
    assert len(encounter.combat_queue) == len(encounter.pc_party.members) + len(encounter.monster_party.members)

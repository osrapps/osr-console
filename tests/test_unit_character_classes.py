import math
import pytest

from osrlib.enums import CharacterClassType
from osrlib.character_classes import class_levels
from osrlib.player_character import PlayerCharacter
from osrlib.utils import logger


# Fixture to generate player characters of all available classes at level 0
@pytest.fixture(scope="function", params=[class_type for class_type in CharacterClassType])
def pc_level_zero(request):
    pc = PlayerCharacter(f"Test {request.param.value}", request.param, 0)
    return pc

# Fixture to generate player characters of all available classes at level 1
@pytest.fixture(scope="function", params=[class_type for class_type in CharacterClassType])
def pc_level_one(request):
    pc = PlayerCharacter(f"Test {request.param.value}", request.param, 1)
    return pc

# Use the fixture by specifying its name as an argument to the test function
def test_characters_init_sane_level_one(pc_level_one: PlayerCharacter):
    logger.debug(pc_level_one)
    assert pc_level_one.character_class.current_level.level_num == 1
    assert pc_level_one.character_class.max_hp > 0
    assert pc_level_one.character_class.xp == 0

# Use the fixture by specifying its name as an argument to the test function
def test_character_can_reach_all_available_levels(pc_level_zero: PlayerCharacter):
    pc = pc_level_zero
    logger.debug(
        f"Testing whether {pc.name.upper()} can reach all {pc.character_class.class_type.value.upper()} levels ..."
    )
    # Rest of the test implementation remains the same

    while pc.character_class.current_level.level_num < len(class_levels[pc.character_class.class_type]) - 1:
        level_before = pc.character_class.current_level.level_num
        next_level = level_before + 1

        # Find the XP requirement for the next level
        next_level_xp_requirement = pc.character_class.levels[next_level].xp_required_for_level

        # Calculate the raw XP needed to reach the next level, without accounting for adjustment
        raw_xp_needed = next_level_xp_requirement - pc.character_class.xp

        # Compensate for XP penalty or bonus to ensure the character levels up
        xp_adjustment_factor = (100 - abs(pc.xp_adjustment_percentage)) / 100
        adjusted_xp_needed = math.ceil(raw_xp_needed / xp_adjustment_factor if xp_adjustment_factor else raw_xp_needed)

        # Grant the adjusted XP
        pc.grant_xp(adjusted_xp_needed)

        level_after = pc.character_class.current_level.level_num

        if level_after > level_before:
            logger.debug(f"[{pc.name}:{pc.character_class.class_type.name}] Granted {adjusted_xp_needed} XP to level up to {level_after}.")

        assert level_after == next_level, f"[{pc.name}:{pc.character_class.class_type.name}] Failed level-up to {next_level} from {level_before} with XP: {pc.character_class.xp}"

    # Assert that the character has reached the maximum level for their class
    assert pc.character_class.current_level.level_num == len(class_levels[pc.character_class.class_type]) - 1

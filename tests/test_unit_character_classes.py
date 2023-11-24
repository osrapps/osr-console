import logging, math
import pytest

from osrlib.enums import CharacterClassType
from osrlib.character_classes import class_levels
from osrlib.player_character import PlayerCharacter

logger = logging.getLogger(__name__)


def generate_player_character_params(starting_level: int = 1):
    params = []
    for character_class_type in CharacterClassType:
        pc = PlayerCharacter(f"Test {character_class_type.value}", character_class_type, starting_level)
        params.append(pc)
    return params


@pytest.mark.parametrize("pc", generate_player_character_params(starting_level=1))
def test_characters_init_sane_level_one(pc: PlayerCharacter):
    logger.debug(pc)
    assert pc.character_class.current_level.level_num == 1
    assert pc.character_class.max_hp > 0
    assert pc.character_class.xp == 0

@pytest.mark.parametrize("pc", generate_player_character_params(starting_level=0))
def test_character_can_reach_all_available_levels(pc: PlayerCharacter):
    logger.debug(
        f"Testing whether {pc.name.upper()} can reach all {pc.character_class.class_type.value.upper()} levels ..."
    )

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

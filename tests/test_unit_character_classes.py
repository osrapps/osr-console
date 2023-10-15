import logging

import pytest

from osrlib.character_classes import CharacterClassType, class_levels
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
    logger.info(pc)
    assert pc.character_class.current_level.level_num == 1
    assert pc.character_class.hp > 0
    assert pc.character_class.xp == 0


@pytest.mark.parametrize("pc", generate_player_character_params(starting_level=0))
def test_character_can_reach_all_available_levels(pc: PlayerCharacter):
    logger.info(
        f"Testing whether {pc.name.upper()} can reach all {pc.character_class.class_type.value.upper()} levels ..."
    )

    for level in class_levels[pc.character_class.class_type]:
        level_before = pc.character_class.current_level.level_num
        next_level = level_before + 1

        if next_level < len(pc.character_class.levels):
            next_level_xp_requirement = pc.character_class.levels[
                pc.character_class.current_level.level_num + 1
            ].xp_required_for_level

            # Grant just enough XP to reach the next level
            xp_needed_to_reach_next_level = next_level_xp_requirement - pc.character_class.xp
            pc.grant_xp(xp_needed_to_reach_next_level)

            level_after = pc.character_class.current_level.level_num
            if level_after > level_before:
                logger.info(pc)

    assert pc.character_class.current_level.level_num == len(class_levels[pc.character_class.class_type]) - 1

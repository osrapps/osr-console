"""Defines character classes for player characters."""
from typing import List, Tuple, Union

from osrlib.dice_roller import DiceRoll, roll_dice
from osrlib.enums import CharacterClassType
from osrlib.saving_throws import get_saving_throws_for_class_and_level
from osrlib.utils import logger


class ClassLevel:
    """Represents a single level in a character class.

    Attributes:
        level_num (int): The level number.
        title (str): The title for the level.
        required_xp (int): The XP required to reach this level.
        hit_dice (str): The hit dice for this level.
        spell_slots (Union[None, str, List[Tuple[int, int]]]): Spell slots available at this level.
    """

    def __init__(
        self,
        level_num: int,
        title: str,
        xp_required_for_level: int,
        hit_dice: str,
        thac0: int,
        spell_slots: Union[None, str, List[Tuple[int, int]]] = None,
    ):
        """Initialize a ClassLevel instance."""
        self.level_num = level_num
        self.title = title
        self.xp_required_for_level = xp_required_for_level
        self.hit_dice = hit_dice
        self.thac0 = thac0
        self.spell_slots = spell_slots

    def __str__(self) -> str:
        """Return a string representation of the ClassLevel instance."""
        return f"{self.level_num} ({self.title})"

    def get_to_hit_target_ac(self, target_ac: int):
        """Get the to-hit roll required for a character of this class and level to hit a target that has the given AC."""
        return self.thac0 - target_ac

class CharacterClass:
    """Defines a character class for a player character.

    Attributes:
        class_type (CharacterClassType): The type of the character class.
        saving_throws (List[int]): The saving throw values.
        levels (List[ClassLevel]): The class levels.
        current_level (ClassLevel): The current level of the character.
        hit_die (str): The hit die for the character class.
        hp (int): The current hit points.
        xp (int): The current experience points.
    """

    def __init__(self, character_class_type: CharacterClassType, level: int = 1, constitution_modifier: int = 0):
        """Initialize a CharacterClass instance."""
        self.class_type = character_class_type
        self.levels = class_levels[self.class_type]
        self.current_level = self.levels[level]
        self.hit_die = self.levels[1].hit_dice  # hit die is always first-level (1dn)

        # TODO: Instead of populating a saving_throws property, maybe we call
        # a function in saving_throws when we need to make the saving throw check?
        self.saving_throws = get_saving_throws_for_class_and_level(self.class_type, self.current_level.level_num)

        # If the character is not first level, roll hit points for the character using the hit dice for that level
        if level > 1:
            self.max_hp = max(roll_dice(self.levels[level].hit_dice, constitution_modifier).total_with_modifier, 1)
        else:
            self.max_hp = max(self.roll_hp(constitution_modifier).total_with_modifier, 1)

        self.hp = self.max_hp
        self.xp = self.current_level.xp_required_for_level

    def __str__(self) -> str:
        """Return a string representation of the CharacterClass instance."""
        return self.class_type.value

    @property
    def xp_needed_for_next_level(self) -> int:
        """Return the XP needed to reach the next level."""
        return self.levels[self.current_level.level_num + 1].xp_required_for_level

    def roll_hp(self, hp_modifier: int = 0) -> DiceRoll:
        """Roll hit points for the character.

        Args:
            hp_modifier (int): Bonus or penalty to apply to the hit point roll.

        Returns:
            DiceRoll: The dice roll result.
        """
        return roll_dice(self.hit_die, hp_modifier)

    def level_up(self, hp_modifier: int = 0) -> bool:
        """Level up the character if possible.

        If the character's current XP meets the next level's requirement, the character's
        current_level is populated with the next level available for the class. Hit points
        are rolled using the hit die appropriate for the character's class and are applied
        to the character's CharacterClass instance. for additional hit points.

        Example:

        ```python
            >>> pc = PlayerCharacter(name="Sckricko", character_class=CharacterClassType.WARRIOR)
            >>> pc.character_class.xp = 2000  # Manually setting XP to meet level-up criteria
            >>> hp_modifier = pc.abilities[AbilityTypes.CONSTITUTION].modifiers[ModifierTypes.HP]
            >>> new_level = pc.character_class.level_up(hp_modifier)
            >>> new_level.level_num
            2
        ```

        Args:
            hp_modifier (int): Hit point bonus or penalty to apply to the HP roll when leveling.

        Returns:
            bool: True if the character leveled up, otherwise False.

        Raises:
            ValueError: Raised if leveling up is not possible due to insufficient XP or maximum level reached.
        """
        level_num_before = self.current_level.level_num
        xp_needed_for_next_level = self.levels[self.current_level.level_num + 1].xp_required_for_level
        if self.xp >= xp_needed_for_next_level:
            if self.current_level.level_num < len(self.levels) - 1:
                self.current_level = self.levels[self.current_level.level_num + 1]
                self.max_hp += max(self.roll_hp(hp_modifier).total_with_modifier, 1)
                self.hp = self.max_hp
                logger.debug(f"{self.class_type.name} is now level {self.current_level.level_num}!")
            else:
                logger.debug(f"{self.class_type.name} Can't level up: already at max level {self.current_level.level_num}.")
        else:
            logger.debug(f"{self.class_type.name} needs {xp_needed_for_next_level - self.xp} XP to reach level {self.current_level.level_num + 1}.")

        return self.current_level.level_num > level_num_before

cleric_levels = [
    ClassLevel(0, "Cleric (NPC)", 0, "1d4", 20),
    ClassLevel(1, "Acolyte", 0, "1d6", 19),
    ClassLevel(2, "Adept", 1500, "2d6", 19, [(1, 1)]),
    ClassLevel(3, "Priest/Priestess", 3000, "3d6", 19, [(1, 2)]),
    ClassLevel(4, "Vicar", 6000, "4d6", 19, [(1, 2), (2, 1)]),
    ClassLevel(5, "Curate", 12000, "5d6", 17, [(1, 2), (2, 2)]),
    ClassLevel(6, "Elder", 25000, "6d6", 17, [(1, 2), (2, 2), (3, 1), (4, 1)]),
    ClassLevel(7, "Bishop", 50000, "7d6", 17, [(1, 2), (2, 2), (3, 2), (4, 1), (5, 1)]),
    ClassLevel(8, "Lama", 100000, "8d6", 17, [(1, 3), (2, 3), (3, 2), (4, 2), (5, 1)]),
    ClassLevel(9, "Patriarch/Matriarch", 200000, "9d6", 14, [(1, 3), (2, 3), (3, 3), (4, 2), (5, 2)]),
    ClassLevel(10, "Patriarch/Matriarch 10th Level", 300000, "9d6+1", 14, [(1, 4), (2, 4), (3, 3), (4, 2), (5, 2)]),
    ClassLevel(11, "Patriarch/Matriarch 11th Level", 400000, "9d6+2", 14, [(1, 4), (2, 4), (3, 4), (4, 3), (5, 4)]),
    ClassLevel(12, "Patriarch/Matriarch 12th Level", 500000, "9d6+3", 14, [(1, 5), (2, 5), (3, 4), (4, 4), (5, 3)]),
    ClassLevel(13, "Patriarch/Matriarch 13th Level", 600000, "9d6+4", 12, [(1, 5), (2, 5), (3, 5), (4, 4), (5, 4)]),
    ClassLevel(14, "Patriarch/Matriarch 14th Level", 700000, "9d6+5", 12, [(1, 6), (2, 5), (3, 5), (4, 5), (5, 4)]),
]


thief_levels = [
    ClassLevel(0, "Thief (NPC)", 0, "1d4", 20),
    ClassLevel(1, "Apprentice", 0, "1d4", 19),
    ClassLevel(2, "Footpad", 1200, "2d4", 19),
    ClassLevel(3, "Robber", 2400, "3d4", 19),
    ClassLevel(4, "Burglar", 4800, "4d4", 19),
    ClassLevel(5, "Cutpurse", 9600, "5d4", 17),
    ClassLevel(6, "Sharper", 20000, "6d4", 17),
    ClassLevel(7, "Pilferer", 40000, "7d4", 17),
    ClassLevel(8, "Thief", 80000, "8d4", 17),
    ClassLevel(9, "Master Thief", 160000, "9d4", 14),
    ClassLevel(10, "Master Thief 10th Level", 280000, "9d4+2", 14),
    ClassLevel(11, "Master Thief 11th Level", 400000, "9d4+4", 14),
    ClassLevel(12, "Master Thief 12th Level", 520000, "9d4+6", 14),
    ClassLevel(13, "Master Thief 13th Level", 640000, "9d4+8", 12),
    ClassLevel(14, "Master Thief 14th Level", 760000, "9d4+10", 12),
]


dwarf_levels = [
    ClassLevel(0, "Dwarf (NPC)", 0, "1d4", 20),
    ClassLevel(1, "Dwarven Veteran", 0, "1d8", 19),
    ClassLevel(2, "Dwarven Warrior", 2200, "2d8", 19),
    ClassLevel(3, "Dwarven Swordmaster", 4400, "3d8", 19),
    ClassLevel(4, "Dwarven Hero", 8800, "4d8", 17),
    ClassLevel(5, "Dwarven Swashbuckler", 17000, "5d8", 17),
    ClassLevel(6, "Dwarven Myrmidon", 35000, "6d8", 17),
    ClassLevel(7, "Dwarven Champion", 70000, "7d8", 14),
    ClassLevel(8, "Dwarven Superhero", 140000, "8d8", 14),
    ClassLevel(9, "Dwarven Lord (Lady)", 270000, "9d8", 14),
    ClassLevel(10, "Dwarven Lord 10th Level", 400000, "9d8+3", 12),
    ClassLevel(11, "Dwarven Lord 11th Level", 530000, "9d8+6", 12),
    ClassLevel(12, "Dwarven Lord 12th Level", 660000, "9d8+9", 12),
]


elf_levels = [
    ClassLevel(0, "Elf (NPC)", 0, "1d4", 20),
    ClassLevel(1, "Veteran-Medium", 0, "1d6", 19, [(1, 1)]),
    ClassLevel(2, "Warrior-Seer", 4000, "2d6", 19, [(1, 2)]),
    ClassLevel(3, "Swordmaster-Conjurer", 8000, "3d6", 19, [(1, 2), (2, 1)]),
    ClassLevel(4, "Hero-Magician", 16000, "4d6", 17, [(1, 2), (2, 2)]),
    ClassLevel(5, "Swashbuckler-Enchanter", 32000, "5d6", 17, [(1, 2), (2, 2), (3, 1)]),
    ClassLevel(6, "Myrmidon-Warlock", 64000, "6d6", 17, [(1, 2), (2, 2), (3, 2)]),
    ClassLevel(7, "Champion-Sorcerer", 120000, "7d6", 14, [(1, 3), (2, 2), (3, 2), (4, 1)]),
    ClassLevel(8, "Superhero-Necromancer", 250000, "8d6", 14, [(1, 3), (2, 3), (3, 2), (4, 2)]),
    ClassLevel(9, "Lord/Lady-Wizard", 400000, "9d6", 14, [(1, 3), (2, 3), (3, 3), (4, 2), (5, 1)]),
    ClassLevel(10, "Lord/Lady-Wizard 10th Level", 600000, "9d6+1", 12, [(1, 3), (2, 3), (3, 3), (4, 3), (5, 2)]),
]


fighter_levels = [
    ClassLevel(0, "Fighter (NPC)", 0, "1d4", 20),
    ClassLevel(1, "Veteran", 0, "1d8", 19),
    ClassLevel(2, "Warrior", 2000, "2d8", 19),
    ClassLevel(3, "Swordmaster", 4000, "3d8", 19),
    ClassLevel(4, "Hero", 8000, "4d8", 17),
    ClassLevel(5, "Swashbuckler", 16000, "5d8", 17),
    ClassLevel(6, "Myrmidon", 32000, "6d8", 17),
    ClassLevel(7, "Champion", 64000, "7d8", 14),
    ClassLevel(8, "Superhero", 120000, "8d8", 14),
    ClassLevel(9, "Lord (Lady)", 240000, "9d8", 14),
    ClassLevel(10, "10th Level Lord", 360000, "9d8+2", 12),
    ClassLevel(11, "11th Level Lord", 480000, "9d8+4", 12),
    ClassLevel(12, "12th Level Lord", 600000, "9d8+6", 12),
    ClassLevel(13, "13th Level Lord", 720000, "9d8+8", 10),
    ClassLevel(14, "14th Level Lord", 840000, "9d8+10", 10),
]


halfling_levels = [
    ClassLevel(0, "Halfling (NPC)", 0, "1d4", 20),
    ClassLevel(1, "Halfling Veteran", 0, "1d6", 19),
    ClassLevel(2, "Halfling Warrior", 2000, "2d6", 19),
    ClassLevel(3, "Halfling Swordmaster", 4000, "3d6", 19),
    ClassLevel(4, "Halfling Hero", 8000, "4d6", 17),
    ClassLevel(5, "Halfling Swashbuckler", 16000, "5d6", 17),
    ClassLevel(6, "Halfling Myrmidon", 32000, "6d6", 17),
    ClassLevel(7, "Halfling Champion", 64000, "7d6", 14),
    ClassLevel(8, "Sheriff", 120000, "8d6", 14),
]


magic_user_levels = [
    ClassLevel(0, "Magic User (NPC)", 0, "1d4-1", 20),
    ClassLevel(1, "Medium", 0, "1d4", 19, [(1, 1)]),
    ClassLevel(2, "Seer", 2500, "2d4", 19, [(1, 2)]),
    ClassLevel(3, "Conjurer", 5000, "3d4", 19, [(1, 2), (2, 1)]),
    ClassLevel(4, "Magician", 10000, "4d4", 19, [(1, 2), (2, 2)]),
    ClassLevel(5, "Enchanter/Enchantress", 20000, "5d4", 19, [(1, 2), (2, 2), (3, 1)]),
    ClassLevel(6, "Warlock", 40000, "6d4", 17, [(1, 2), (2, 2), (3, 2)]),
    ClassLevel(7, "Sorcerer/Sorceress", 80000, "7d4", 17, [(1, 3), (2, 2), (3, 2), (4, 1)]),
    ClassLevel(8, "Necromancer", 150000, "8d4", 17, [(1, 3), (2, 3), (3, 2), (4, 2)]),
    ClassLevel(9, "Wizard", 300000, "9d4", 17, [(1, 3), (2, 3), (3, 3), (4, 2), (5, 1)]),
    ClassLevel(10, "Wizard 10th Level", 450000, "9d4+1", 17, [(1, 3), (2, 3), (3, 3), (4, 3), (5, 2)]),
    ClassLevel(11, "Wizard 11th Level", 600000, "9d4+2", 14, [(1, 4), (2, 3), (3, 3), (4, 3), (5, 2), (6, 1)]),
    ClassLevel(12, "Wizard 12th Level", 750000, "9d4+3", 14, [(1, 4), (2, 4), (3, 3), (4, 3), (5, 3), (6, 2)]),
    ClassLevel(13, "Wizard 13th Level", 900000, "9d4+4", 14, [(1, 4), (2, 4), (3, 4), (4, 3), (5, 3), (6, 3)]),
    ClassLevel(14, "Wizard 14th Level", 1050000, "9d4+5", 14, [(1, 4), (2, 4), (3, 4), (4, 4), (5, 3), (6, 3)]),
]


commoner_levels = [
    ClassLevel(0, "Commoner", 0, "1d4-3", 20),
    ClassLevel(1, "Candlestick Maker", 0, "1d4-2", 20),
    ClassLevel(2, "Baker", 2000, "1d4-1", 20),
    ClassLevel(3, "Butcher", 4000, "1d4", 20),
    ClassLevel(4, "Farmer", 8000, "1d4+1", 19),
    ClassLevel(5, "Fishmonger", 16000, "1d4+2", 19),
    ClassLevel(6, "Mason", 32000, "1d4+3", 19),
    ClassLevel(7, "Blacksmith", 64000, "1d4+4", 19),
    ClassLevel(8, "Trapper", 120000, "1d4+5", 18),
    ClassLevel(9, "Hunter", 240000, "1d4+6", 18),
    ClassLevel(10, "Hunter 10th Level", 360000, "1d4+7", 18),
]


class_levels = {
    CharacterClassType.CLERIC: cleric_levels,
    CharacterClassType.DWARF: dwarf_levels,
    CharacterClassType.ELF: elf_levels,
    CharacterClassType.FIGHTER: fighter_levels,
    CharacterClassType.HALFLING: halfling_levels,
    CharacterClassType.MAGIC_USER: magic_user_levels,
    CharacterClassType.THIEF: thief_levels,
    CharacterClassType.COMMONER: commoner_levels,
}


all_character_classes = [
    CharacterClass(CharacterClassType.CLERIC),
    CharacterClass(CharacterClassType.THIEF),
    CharacterClass(CharacterClassType.DWARF),
    CharacterClass(CharacterClassType.ELF),
    CharacterClass(CharacterClassType.FIGHTER),
    CharacterClass(CharacterClassType.HALFLING),
    CharacterClass(CharacterClassType.MAGIC_USER),
    CharacterClass(CharacterClassType.COMMONER),
]

from typing import List
from osrlib.dice_roller import roll_dice, DiceRoll
from osrlib.enums import CharacterClassType
from osrlib.player_character import Alignment
from osrlib.treasure import TreasureType
from osrlib.saving_throws import get_saving_throws_for_class_and_level
from osrlib.game_manager import logger

monster_xp = {
    "Under 1": {"base": 5, "bonus": 1},  # Not handling the "under 1" hit dice case
    "1": {"base": 10, "bonus": 3},
    "1+": {"base": 15, "bonus": 4},
    "2": {"base": 20, "bonus": 5},
    "2+": {"base": 25, "bonus": 10},
    "3": {"base": 35, "bonus": 15},
    "3+": {"base": 50, "bonus": 25},
    "4": {"base": 75, "bonus": 50},
    "4+": {"base": 125, "bonus": 75},
    "5": {"base": 175, "bonus": 125},
    "5+": {"base": 225, "bonus": 175},
    "6": {"base": 275, "bonus": 225},
    "6+": {"base": 350, "bonus": 300},
    "7": {"base": 450, "bonus": 400},
    "8": {"base": 650, "bonus": 550},
    "9 to 10+": {"base": 900, "bonus": 700},
    "11 to 12+": {"base": 1100, "bonus": 800},
    "13 to 16+": {"base": 1350, "bonus": 950},
    "17 to 20+": {"base": 2000, "bonus": 1150},
    "21+": {"base": 2500, "bonus": 2000},
}

monster_thac0 = {
    "0+ to 1": 19,
    "1+ to 2": 18,
    "2+ to 3": 17,
    "3+ to 4": 16,
    "4+ to 5": 15,
    "5+ to 6": 14,
    "6+ to 7": 13,
    "7+ to 8": 12,
    "8+ to 9": 12,
    "9+ to 10": 11,
    "10+ to 11": 11,
    "11+ to 12": 10,
    "12+ to 13": 10,
    "13+ to 14": 9,
    "14+ to 15": 9,
    "15+ to 16": 8,
    "16+ to 17": 8,
    "17+ to 18": 7,
    "18+ to 19": 7,
    "19+ to 20": 6,
    "20+ to 21": 6,
    "21+ or more": 5,
}

class MonsterStatsBlock:
    """Specifies the statistics of the monsters in a monster party.

    Pass a MonsterStatBlock instance to the MonsterParty constructor to create a new
    MonsterParty instance appropriate for populating an Encounter's monster_party attribute.

    Attributes:
        name (str): The name of the monster.
        description (str): The monster's description.
        armor_class (int): The monster's armor class (AC). Lower is better.
        hit_dice (str): The monster's hit dice in "nd8" or "nd8+n" format, for example '1d8', '1d8+2', '3d8'). Default is '1d8'.
        movement (int): The monster's movement rate in feet per round. Default is 120.
        num_special_abilities (int): The special ability count of the monster; this value corresponds to the number of asterisks after the monster's hit dice in the Basic and Expert rule books. Default is 0.
        attacks_per_round (int): The number of attacks the monster can make per round. Default is 1.
        damage_per_attack (str): The damage the monster does per attack in "ndn" or "ndn+n" format, for example '1d4', '1d4+2', '3d4'). Default is '1d4'.
        num_appearing (int): The number of monsters in the monster party. Default is 1-6 (1d6).
        save_as_class (CharacterClassType): The character class type the monster saves as. Default is CharacterClassType.FIGHTER.
        save_as_level (int): The level of the character class the monster saves as. Default is 1.
    """

    def __init__(
        self,
        name: str,
        description: str = "",
        armor_class: int = 10,
        hit_dice: str = "1d8",
        movement: int = 120,
        num_special_abilities=0, # corresponds to the number of asterisks on the monster's hit dice
        attacks_per_round=1, # TODO: Add support for attack and damage modifiers (e.g. Cyclops has -2 on attack rolls)
        damage_per_attack="1d4",
        num_appearing="1d6",
        save_as_class=CharacterClassType.FIGHTER,
        save_as_level=1,
        morale: int = 12, # roll 2d6, if result is higher than this, monster flees
        treasure_type=TreasureType.NONE,
        alignment=Alignment.NEUTRAL,
    ):
        """Initialize a new MonsterStatBlock instance."""
        self.name = name
        self.description = description
        self.armor_class = armor_class
        self.hit_dice = hit_dice
        self.movement = movement
        self.num_special_abilities = num_special_abilities
        self.attacks_per_round = attacks_per_round
        self.damage_per_attack = damage_per_attack
        self.num_appearing = roll_dice(num_appearing).total_with_modifier
        self.save_as_class = save_as_class
        self.save_as_level = save_as_level
        self.morale = morale
        self.treasure_type = treasure_type
        self.alignment = alignment


class Monster:
    """A Monster is a creature the party can encounter in a dungeon and defeat to obtain experience points and optionally treasure and quest pieces."""

    def __init__(self, monster_stats: MonsterStatsBlock):
        """Initialize a new Monster instance."""
        self.name = monster_stats.name
        self.description = monster_stats.description
        self.armor_class = monster_stats.armor_class

        self.hp_roll = roll_dice(monster_stats.hit_dice)
        self.hit_points = self.hp_roll.total_with_modifier
        self.max_hit_points = self.hit_points

        self.movement = monster_stats.movement
        self.attacks_per_round = monster_stats.attacks_per_round
        self.damage_per_attack = monster_stats.damage_per_attack
        self.saving_throws = get_saving_throws_for_class_and_level(
            monster_stats.save_as_class,
            monster_stats.save_as_level
        ) # TODO: Instead of populating a saving_throws property, maybe we call a function in saving_throws to make the saving throw check?
        self.morale = monster_stats.morale
        self.alignment = monster_stats.alignment

        self.xp_value = self._calculate_xp(self.hp_roll, monster_stats.num_special_abilities)

    def _calculate_xp(self, hp_roll: DiceRoll, num_special_abilities: int = 0):
        """Get the total XP value of the monster. The XP value is based on the monster's hit dice and number of special abilities.

        Args:
            hp_roll (DiceRoll): The dice roll used to determine the monster's hit points. The number of hit dice is used to determine the XP value.

        Returns:
            int: The total XP value of the monster.
        """
        base_xp = 0
        plus = ""

        # Handle monsters with less than 1 hit die
        if hp_roll.num_sides < 8:
            base_xp = monster_xp["Under 1"]["base"]
            bonus = monster_xp["Under 1"]["bonus"]
            return base_xp + bonus * num_special_abilities

        # Handle monsters with 1 hit die and up
        if hp_roll.num_dice <= 8:
            # XP values for monsters with 1-8 hit dice have single values
            if hp_roll.modifier > 0:
                plus = "+"
            base_xp = monster_xp[f"{hp_roll.num_dice}{plus}"]["base"]
            bonus = monster_xp[f"{hp_roll.num_dice}{plus}"]["bonus"]
        # XP values for monsters with 9+ hit dice use a single value for a range of hit dice
        elif hp_roll.num_dice >= 9 and hp_roll.num_dice <= 10:
            base_xp = monster_xp["9 to 10+"]["base"]
            bonus = monster_xp["9 to 10+"]["bonus"]
        elif hp_roll.num_dice >= 11 and hp_roll.num_dice <= 12:
            base_xp = monster_xp["11 to 12+"]["base"]
            bonus = monster_xp["11 to 12+"]["bonus"]
        elif hp_roll.num_dice >= 13 and hp_roll.num_dice <= 16:
            base_xp = monster_xp["13 to 16+"]["base"]
            bonus = monster_xp["13 to 16+"]["bonus"]
        elif hp_roll.num_dice >= 17 and hp_roll.num_dice <= 20:
            base_xp = monster_xp["17 to 20+"]["base"]
            bonus = monster_xp["17 to 20+"]["bonus"]
        elif hp_roll.num_dice >= 21:
            base_xp = monster_xp["21+"]["base"]
            bonus = monster_xp["21+"]["bonus"]

        # get the total XP value
        total_xp = base_xp + bonus * num_special_abilities

        return total_xp

    @property
    def is_alive(self):
        """Get whether the monster is alive.

        Returns:
            int: True if the monster has more than 0 hit points, otherwise False.
        """
        return self.hit_points > 0

    def get_initiative_roll(self):
        """Rolls a 1d6 and returns the total for the monster's initiative."""
        roll = roll_dice("1d6")
        logger.debug(f"{self.name} rolled {roll} for initiative and got {roll.total_with_modifier}.")
        return roll.total_with_modifier

    def get_to_hit_target_ac(self, target_ac: int) -> int:
        """Get the to-hit roll needed to hit a target with the given armor class."""
        if self.hp_roll.modifier > 0:
            if self.hp_roll.num_dice < 21:
                thac0_key = f"{self.hp_roll.num_dice}+ to {self.hp_roll.num_dice + 1}"
            else:
                thac0_key = f"{self.hp_roll.num_dice}+ or more"
        else:
            thac0_key = f"{self.hp_roll.num_dice - 1}+ to {self.hp_roll.num_dice}"

        thac0 = monster_thac0[thac0_key]
        needed_to_hit = max(thac0 - target_ac, 2) # 1 always misses, so 2 is the lowest to-hit value possible
        logger.debug(f"{self.name} THAC0: {thac0} ({thac0_key}) | To hit target AC {target_ac}: {needed_to_hit}")

        return needed_to_hit

    def get_attack_rolls(self) -> List[DiceRoll]:
        """Roll a 1d20 for each attack this monster has per round and return the collection of rolls."""
        attack_rolls = []

        for _ in range(self.attacks_per_round):
            attack_rolls.append(roll_dice("1d20"))

        # Return collection of attack rolls
        return attack_rolls

    def get_damage_roll(self) -> DiceRoll:
        """Roll the monster's damage dice and return the total."""
        return roll_dice(self.damage_per_attack)

    def apply_damage(self, hit_points_damage: int):
        """Apply damage to the monster by reducing the monster's hit points by the given amount, down to a minimum of 0.

        This method has no affect if the monster is already dead.

        Args:
            damage (int): The amount of damage done to the monster.
        """
        if self.is_alive:
            new_hp = self.hit_points - hit_points_damage
            self.hit_points = max(new_hp, 0)

    def heal(self, hit_points_healed: int):
        """Heal the monster by restoring the given amount of hit points up to the monster's maximum hit points.

        This method has no affect if the monster is dead.

        Args:
            hit_points_healed (int): The amount of hit points to restore.
        """
        if self.is_alive:
            new_hp = self.hit_points + hit_points_healed
            self.hit_points = min(new_hp, self.max_hit_points)


class MonsterParty:
    """A group of monsters the party can encounter in a dungeon location.

    Attributes:
        members (list): A list of the monsters in the monster party.
        is_alive (bool): True if at least one monster in the monster party is alive, otherwise False.
    """

    def __init__(self, monster_stat_block: MonsterStatsBlock):
        """Initialize a new MonsterParty instance.

        The number of monsters that comprise the monster party, as well as hit points, armor class, and other
        statistics are determined by the given MonsterStatBlock.

        Args:
            monster_stat_block (MonsterStatBlock): The stat block for the monsters in the party.
        """
        self.members = [
            Monster(monster_stat_block)
            for _ in range(
                #roll_dice(monster_stat_block.num_appearing).total_with_modifier
                monster_stat_block.num_appearing
            )
        ]
        self.treasure = self._get_treasure(monster_stat_block.treasure_type)
        self.is_surprised = False

    def _get_treasure(self, treasure_type: TreasureType):
        """Get the treasure for the monster party based on the treasure type.

        NOT YET IMPLEMENTED

        Args:
            treasure_type (TreasureType): The type of treasure to get.

        Returns:
            list: A list of the items to be awarded as treasure to the party.
        """
        treasure_items = []
        if treasure_type == TreasureType.NONE:
            return None
        elif treasure_type == TreasureType.A:
            pass
        elif treasure_type == TreasureType.B:
            pass
        elif treasure_type == TreasureType.C:
            pass
        elif treasure_type == TreasureType.D:
            pass
        elif treasure_type == TreasureType.E:
            pass
        elif treasure_type == TreasureType.F:
            pass
        elif treasure_type == TreasureType.G:
            pass
        elif treasure_type == TreasureType.H:
            pass
        elif treasure_type == TreasureType.I:
            pass
        elif treasure_type == TreasureType.J:
            pass
        elif treasure_type == TreasureType.K:
            pass
        elif treasure_type == TreasureType.L:
            pass
        elif treasure_type == TreasureType.M:
            pass
        elif treasure_type == TreasureType.N:
            pass
        elif treasure_type == TreasureType.O:
            pass
        elif treasure_type == TreasureType.P:
            pass
        elif treasure_type == TreasureType.Q:
            pass
        elif treasure_type == TreasureType.R:
            pass
        elif treasure_type == TreasureType.S:
            pass
        elif treasure_type == TreasureType.T:
            pass
        elif treasure_type == TreasureType.U:
            pass
        elif treasure_type == TreasureType.V:
            pass

        return treasure_items

    @property
    def is_alive(self):
        """Get whether the monster party is alive.

        Returns:
            int: True if the monster party has more than 0 hit points, otherwise False.
        """
        return any(monster.is_alive for monster in self.members)

    @property
    def xp_value(self):
        """Get the total XP value of the monster party.

        Returns:
            int: The total XP value of the monster party.
        """
        monster_xp = sum(monster.xp_value for monster in self.members)
        treasure_xp = 0 # TODO: sum(item.xp_value for item in self.treasure)
        return monster_xp + treasure_xp

    def get_surprise_roll(self) -> int:
        """Rolls a 1d6 and returns the total for the monster party's surprise roll."""
        roll = roll_dice("1d6")
        logger.debug(f"Monster party rolled {roll} for surprise and got {roll.total_with_modifier}.")
        return roll.total_with_modifier
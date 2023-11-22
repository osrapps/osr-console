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
    """Represents the statistical attributes of a monster like those found in an RPG rulebook.

    This class encapsulates all key statistics for a monster like armor class, hit dice, movement rate, and other
    attributes typically found in a monster's stat block. These attributes define the combat and behavioral characteristics
    of monsters encountered by the characters in the player's party.

    The primary use of a MonsterStatsBlock is as a parameter for the MonsterParty constructor. It allows the creation of a
    MonsterParty instance, which creates instances of the monster in the party as defined by the statistics provided in
    the MonsterStatsBlock.

    Example:
        # Create a MonsterStatsBlock for a Goblin
        goblin_stats = MonsterStatsBlock(
            name="Goblin",
            description="A small, green-skinned humanoid with a mischievous and malevolent nature.",
            armor_class=6,
            hit_dice="1d8",
            movement=30,
            num_special_abilities=0,
            attacks_per_round=1,
            damage_per_attack="1d6",
            num_appearing="2d4",
            save_as_class=CharacterClassType.FIGHTER,
            save_as_level=1,
            morale=8,
            treasure_type=TreasureType.NONE,
            alignment=Alignment.EVIL
        )

        # Use the goblin_stats to create a MonsterParty
        goblin_party = MonsterParty(goblin_stats)
        print(f"Goblin Party: {goblin_party}")

    Attributes:
        name (str): The name of the monster.
        description (str): A brief description of the monster.
        armor_class (int): The armor class (AC) of the monster, indicating its defensive capabilities.
        hit_dice (str): The hit dice of the monster, in 'nd8' or 'nd8+n' format, representing its health pool.
        movement (int): The movement rate of the monster in feet per round.
        num_special_abilities (int): The number of special abilities the monster possesses.
        attacks_per_round (int): The number of attacks the monster can perform in a single round.
        damage_per_attack (str): The damage dealt by the monster per attack, in 'ndn' or 'ndn+n' format.
        num_appearing (str): The dice notation for the typical number of these monsters encountered.
        save_as_class (CharacterClassType): The class type for the monster's saving throws.
        save_as_level (int): The effective level for the monster's saving throws.
        morale (int): The morale rating of the monster, influencing its behavior in combat.
        treasure_type (TreasureType): The type of treasure carried or guarded by the monster.
        alignment (Alignment): The moral and ethical stance of the monster.

    Note:
        The 'num_appearing' parameter uses dice notation (e.g., '1d6') and is rolled on instantiation to determine the
        actual number of monsters appearing.
    """

    def __init__(
        self,
        name: str,
        description: str = "",
        armor_class: int = 10,
        hit_dice: str = "1d8",
        movement: int = 120,
        num_special_abilities=0,  # corresponds to the number of asterisks on the monster's hit dice
        attacks_per_round=1,  # TODO: Add support for attack and damage modifiers (e.g. Cyclops has -2 on attack rolls)
        damage_per_attack="1d4",
        num_appearing="1d6",
        save_as_class=CharacterClassType.FIGHTER,
        save_as_level=1,
        morale: int = 12,  # roll 2d6, if result is higher than this, monster flees
        treasure_type=TreasureType.NONE,
        alignment=Alignment.NEUTRAL,
    ):
        """Initialize a new instance of MonsterStatsBlock with the provided attributes."""
        self.name = name
        self.description = description
        self.armor_class = armor_class
        self.hit_dice = hit_dice
        self.movement = movement
        self.num_special_abilities = num_special_abilities
        self.attacks_per_round = attacks_per_round
        self.damage_per_attack = damage_per_attack
        self.num_appearing_dice_string = num_appearing
        self.num_appearing = roll_dice(self.num_appearing_dice_string).total_with_modifier
        self.save_as_class = save_as_class
        self.save_as_level = save_as_level
        self.morale = morale
        self.treasure_type = treasure_type
        self.alignment = alignment

    def to_dict(self):
        """
        Serialize the MonsterStatsBlock instance to a dictionary format.

        Converts the MonsterStatsBlock's attributes into a dictionary, facilitating easy serialization for storage or transmission.
        Enum values (like save_as_class) are converted to their string representations for compatibility.

        Returns:
            dict: A dictionary representation of the MonsterStatsBlock instance.
        """
        return {
            "name": self.name,
            "description": self.description,
            "armor_class": self.armor_class,
            "hit_dice": self.hit_dice,
            "movement": self.movement,
            "num_special_abilities": self.num_special_abilities,
            "attacks_per_round": self.attacks_per_round,
            "damage_per_attack": self.damage_per_attack,
            "num_appearing": self.num_appearing_dice_string, # Save the dice string so it's rolled again when the monster party is (re)created
            "save_as_class": self.save_as_class.name, # Enum to string (we deserialize the string back to an enum in the from_dict method)
            "save_as_level": self.save_as_level,
            "morale": self.morale,
            "treasure_type": self.treasure_type.name, # Enum to string (we deserialize the string back to an enum in the from_dict method
            "alignment": self.alignment.name, # Enum to string (we deserialize the string back to an enum in the from_dict method
        }

    @classmethod
    def from_dict(cls, monster_stats_block_dict: dict):
        """
        Deserialize a dictionary into a MonsterStatsBlock instance.

        This method creates a new instance of MonsterStatsBlock using the data provided in a dictionary, typically generated
        by the `to_dict` method. It ensures that enum values are appropriately converted back to their respective enum types.

        Args:
            monster_stats_block_dict (dict): A dictionary containing the monster's attributes.

        Returns:
            MonsterStatsBlock: An instance of MonsterStatsBlock initialized with the data from the dictionary.

        Raises:
            KeyError: If required keys are missing in the dictionary.
            ValueError: If there are issues with enum conversion or invalid data.

        Note:
            This method is intended for use with dictionaries created by the `to_dict` method of a MonsterStatsBlock instance.
        """
        monster_stats_block_dict['save_as_class'] = CharacterClassType[monster_stats_block_dict['save_as_class']]
        monster_stats_block_dict['treasure_type'] = TreasureType[monster_stats_block_dict['treasure_type']]
        monster_stats_block_dict['alignment'] = Alignment[monster_stats_block_dict['alignment']]

        return cls(**monster_stats_block_dict)


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
            monster_stats.save_as_class, monster_stats.save_as_level
        )  # TODO: Instead of populating a saving_throws property, maybe we call a function in saving_throws to make the saving throw check?
        self.morale = monster_stats.morale
        self.alignment = monster_stats.alignment

        self.xp_value = self._calculate_xp(
            self.hp_roll, monster_stats.num_special_abilities
        )

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
        logger.debug(
            f"{self.name} rolled {roll} for initiative and got {roll.total_with_modifier}."
        )
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
        needed_to_hit = max(
            thac0 - target_ac, 2
        )  # 1 always misses, so 2 is the lowest to-hit value possible
        logger.debug(
            f"{self.name} THAC0: {thac0} ({thac0_key}) | To hit target AC {target_ac}: {needed_to_hit}"
        )

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

    def __init__(self, monster_stats_block: MonsterStatsBlock):
        """Initialize a new MonsterParty instance.

        The number of monsters that comprise the monster party, as well as hit points, armor class, and other
        statistics are determined by the given MonsterStatsBlock.

        Args:
            monster_stats_block (MonsterStatsBlock): The stat block for the monsters in the party.
        """
        self.monster_stats_block = monster_stats_block
        self.members = [
            Monster(monster_stats_block)
            for _ in range(
                # roll_dice(monster_stats_block.num_appearing).total_with_modifier
                monster_stats_block.num_appearing
            )
        ]
        self.treasure = self._get_treasure(monster_stats_block.treasure_type)
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
        treasure_xp = 0  # TODO: sum(item.xp_value for item in self.treasure)
        return monster_xp + treasure_xp

    def get_surprise_roll(self) -> int:
        """Rolls a 1d6 and returns the total for the monster party's surprise roll."""
        roll = roll_dice("1d6")
        logger.debug(
            f"Monster party rolled {roll} for surprise and got {roll.total_with_modifier}."
        )
        return roll.total_with_modifier

    def to_dict(self):
        """
        Return a dictionary representation of the monster party's MonsterStatsBlock.

        This method serializes the MonsterStatsBlock instance associated with the MonsterParty into a dictionary format.
        The primary use case for this method is to facilitate saving the state of a MonsterParty to a persistent storage
        (like a database or a file) by first converting it to a dictionary. The serialized dictionary can then be used
        to rehydrate a MonsterParty instance using the `from_dict` class method.

        Returns:
            dict: A dictionary representation of the MonsterStatsBlock associated with the MonsterParty. This dictionary
                contains key-value pairs representing the attributes of the MonsterStatsBlock, such as 'name',
                'armor_class', 'hit_dice', etc.

        Example:
            >>> monster_party = MonsterParty(monster_stats_block)
            >>> monster_party_dict = monster_party.to_dict()
            >>> # The monster_party_dict can now be used to store the state of the MonsterParty
            >>> # and later to recreate it using MonsterParty.from_dict(monster_party_dict)

        Note:
            This method does not serialize the dynamic state of the MonsterParty itself (such as the current health of
            monsters or the treasure collected). It serializes the MonsterStatsBlock, which can be used to recreate a
            similar MonsterParty with a new state.
        """
        return self.monster_stats_block.to_dict()

    @classmethod
    def from_dict(cls, monster_stats_block_dict: dict):
        """
        Create a MonsterParty instance from a dictionary representing a MonsterStatsBlock.

        This class method deserializes a dictionary into a MonsterStatsBlock instance and then uses it to initialize a
        new MonsterParty. It's particularly useful for rehydrating a MonsterParty from its serialized state, such as
        when loading game data from a persistent storage like a database or a file.

        Args:
            monster_stats_block_dict (dict): A dictionary containing key-value pairs representing the attributes of a
                                            MonsterStatsBlock. The dictionary structure should correspond to the output
                                            of the `to_dict` method of a MonsterStatsBlock instance.

        Returns:
            MonsterParty: An instance of MonsterParty initialized with the MonsterStatsBlock created from the provided
                        dictionary.

        Raises:
            ValueError: If the dictionary does not contain the necessary information to create a valid MonsterStatsBlock.
            KeyError: If essential keys are missing in the input dictionary.

        Example:
            >>> monster_party = MonsterParty(monster_stats_block)
            >>> monster_party_dict = monster_party.to_dict()
            >>> rehydrated_monster_party = MonsterParty.from_dict(monster_party_dict)
            >>> print(rehydrated_monster_party)

        Note:
            This method is designed to work with dictionaries generated by the `to_dict` method of a MonsterParty instance.
            Manually creating or altering the dictionary may lead to unexpected behavior.
        """
        monster_stats = MonsterStatsBlock.from_dict(monster_stats_block_dict)
        return cls(monster_stats)

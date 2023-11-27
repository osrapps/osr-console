"""This module contains the PlayerCharacter class."""
from enum import Enum
import osrlib.ability
from osrlib.ability import (
    AbilityType,
    Charisma,
    Constitution,
    Dexterity,
    Intelligence,
    ModifierType,
    Strength,
    Wisdom,
)
from osrlib.character_classes import (
    CharacterClass,
    CharacterClassType,
)
from osrlib.inventory import Inventory
from osrlib.dice_roller import roll_dice, DiceRoll
from osrlib.game_manager import logger


class Alignment(Enum):
    """Represents the alignment of a player character (PC) or monster."""

    LAWFUL = "Lawful"
    NEUTRAL = "Neutral"
    CHAOTIC = "Chaotic"


class PlayerCharacter:
    """Represents a player character (PC) in the game.

    Attributes:
        name (str): The name of the character.
        abilities (dict): A dictionary of the character's abilities.
        character_class (CharacterClass): The character's class.
        inventory (Inventory): The character's inventory.
        xp_adjustment_percentage (int): The character's XP adjustment based on the scores of ability their prime requisite(s). This value is set when the character's class is set, or when restoring a saved character.
    """

    def __init__(
        self,
        name: str,
        character_class_type: CharacterClassType,
        level: int = 1,
        xp_adjustment_percentage: int = 0,
    ):
        """Initialize a new PlayerCharacter (PC) instance."""
        self.name = name
        self.character_class = None
        self.abilities = {}
        self.roll_abilities()  # TODO: Should NOT roll abilities when loading a saved character
        self.xp_adjustment_percentage = xp_adjustment_percentage
        self.set_character_class(character_class_type, level)

        self.inventory = Inventory(self)

    def __str__(self):
        """Get a string representation of the PlayerCharacter instance.

        Returns:
            str: A string representation of the PlayerCharacter instance.
        """
        ability_str = ", ".join(
            f"{ability.name}: {attr.score:>2}"
            for ability, attr in self.abilities.items()
        )
        return (
            f"{self.name} ({self.character_class} {self.level}) "
            f"HP: {self.hit_points}/{self.max_hit_points} "
            f"AC: {self.armor_class} "
            f"XP: {self.xp}/{self.xp_needed_for_next_level}"
        )

    @property
    def is_alive(self) -> bool:
        """Returns True if the character is alive.

        The character is considered alive if their hit points are greater than 0.

        Returns:
            bool: True if the character is alive (hit points > 0), False otherwise.
        """
        return self.hit_points > 0

    @property
    def level(self):
        return (
            self.character_class.current_level.level_num
            if self.character_class.current_level.level_num is not None
            else None
        )

    @property
    def hit_points(self):
        return self.character_class.hp

    @property
    def max_hit_points(self) -> int:
        """Get the maximum hit points of the character."""
        return self.character_class.max_hp

    @property
    def armor_class(self):
        """Get the armor class of the character."""
        armor_class = 9
        armor_class += self.abilities[AbilityType.DEXTERITY].modifiers[ModifierType.AC]
        armor_class += sum(
            armor_item.ac_modifier
            for armor_item in self.inventory.armor
            if armor_item.is_equipped
        )
        return armor_class

    @property
    def xp(self) -> int:
        """Get the character's current XP total."""
        return self.character_class.xp

    @property
    def xp_needed_for_next_level(self) -> int:
        """Get the amount of XP needed for the character to reach the next level."""
        return self.character_class.xp_needed_for_next_level

    def get_ability_roll(self):
        """Rolls a 4d6 and returns the sum of the three highest rolls."""
        roll = roll_dice("4d6", drop_lowest=True)
        return roll.total

    def get_initiative_roll(self) -> int:
        """Rolls a 1d6, adds the character's Dexterity modifier, and returns the total."""
        modifier_value = self.abilities[AbilityType.DEXTERITY].modifiers[
            ModifierType.INITIATIVE
        ]
        roll = roll_dice("1d6", modifier_value)
        logger.debug(f"{self.name} ({self.character_class.class_type.value}) rolled {roll} for initiative and got {roll.total_with_modifier}.")
        return roll.total_with_modifier

    def get_attack_roll(self) -> DiceRoll:
        """Roll a 1d20 to hit, add all applicable modifiers, and return the roll.

        Returns:
            DiceRoll: The result of the to hit roll.
        """
        # TODO: Get proper attack roll
        # 1. TODO: Get active weapon/spell
        # 2. TODO: Get applicable attack modifier(s)
        #  - TODO: Melee: Strength modifier, enchanted/cursed weapon adjustment, buffs/curses
        #  - TODO: Ranged: Dexterity modifier, enchanted/cursed weapon adjustment, buffs/curses

        melee_attack_modifier = self.abilities[AbilityType.STRENGTH].modifiers[ModifierType.TO_HIT]
        ranged_attack_modifier = self.abilities[AbilityType.DEXTERITY].modifiers[ModifierType.TO_HIT]
        return roll_dice("1d20", melee_attack_modifier)

    def get_damage_roll(self) -> DiceRoll:
        """Roll appropriate damage die, add all applicable modifiers, and return the roll.

        Returns:
            DiceRoll: The result of the damage roll.
        """
        weapon = self.inventory.get_equipped_weapon()
        melee_damage_modifier = self.abilities[AbilityType.STRENGTH].modifiers[ModifierType.DAMAGE]
        return roll_dice(weapon.damage_die, melee_damage_modifier)

    def apply_damage(self, hit_points_damage: int):
        """Apply damage to the player character by reducing their hit points by the given amount, down to a minimum of 0.

        This method has no affect if the character is already dead.

        Args:
            damage (int): The amount of damage done to the PC.
        """
        if self.is_alive:
            new_hp = self.character_class.hp - hit_points_damage
            self.character_class.hp = max(new_hp, 0)

    def _set_prime_requisite_xp_adjustment(self):
        """Sets the character's earned XP adjustment based on the scores of their ability prime requisite(s)."""

        # Track the prime requisite scores
        prime_requisites_scores = [
            ability.score
            for ability_name, ability in self.abilities.items()
            if self.character_class.class_type in ability.prime_requisite_classes
        ]

        # Determine penalties first, as they take precedence
        if any(3 <= score <= 5 for score in prime_requisites_scores):
            self.xp_adjustment_percentage = -20
        elif any(6 <= score <= 8 for score in prime_requisites_scores):
            self.xp_adjustment_percentage = -10
        # Now check for bonuses; if any prime requisites are in the bonus range and no penalties were applied
        elif any(score >= 13 for score in prime_requisites_scores):
            self.xp_adjustment_percentage = 5
            # Apply the higher bonus if all are above the threshold
            if all(score >= 13 for score in prime_requisites_scores):
                self.xp_adjustment_percentage = 10

        logger.debug(f"XP adjustment percentage set to: {self.xp_adjustment_percentage}%")

    def set_character_class(
        self, character_class_type: CharacterClassType, level: int = 1
    ):
        """Sets the character class of the character."""
        # TODO: Add validation to prevent setting a class if the class' prime requisite scores aren't met
        self.character_class = CharacterClass(
            character_class_type,
            level,
            self.abilities[AbilityType.CONSTITUTION].modifiers[ModifierType.HP],
        )

        self._set_prime_requisite_xp_adjustment()

        return self.character_class

    def grant_xp(self, xp: int) -> bool:
        """Grants XP to the character, taking into account their Constitution ability modifier, if any.

        If the the character's new XP total is enough to level up, the character's level and associated statistics
        (including a new "XP neeeded for next level" value) are increased appropriately.
        """

        # Adjust awarded XP based on prime requisite scores (if applicable)
        adjusted_xp = int(xp * (1 + self.xp_adjustment_percentage / 100))
        self.character_class.xp += adjusted_xp

        return self.character_class.level_up(
            # Need to pass the character's Constitution modifier all the way down to the roll_hp method
            self.abilities[AbilityType.CONSTITUTION].modifiers[ModifierType.HP]
        )

    def heal(self, hit_points_healed: int):
        """Heal the player character by increasing their hit points by the given amount, up to their maximum hit points.

        Args:
            hit_points_healed (int): The amount of hit points to heal the PC.
        """
        new_hp = self.hit_points + hit_points_healed
        self.character_class.hp = min(new_hp, self.character_class.max_hp)

    def roll_abilities(self):
        """Rolls the ability scores of the character."""
        self.abilities = {}
        for ability_class in [
            Strength,
            Intelligence,
            Wisdom,
            Dexterity,
            Constitution,
            Charisma,
        ]:
            roll = self.get_ability_roll()
            ability_instance = ability_class(roll)

            self.abilities[ability_instance.ability_type] = ability_instance
            logger.debug(
                f"{self.name} rolled {ability_instance.ability_type.name}:{roll}"
            )

    def roll_hp(self) -> DiceRoll:
        """Rolls the character's hit points, taking into account their Constitution modifier, if any.

        The total value of the roll with modifier can be negative after if the roll was low and the character has a
        negative Constitution modifier. You should clamp the value to 1 before applying it to the character's HP.

        Returns:
            DiceRoll: The result of the HP roll. Value with modifiers can be negative.
        """
        hp_modifier = self.abilities[AbilityType.CONSTITUTION].modifiers[
            ModifierType.HP
        ]
        hp_roll = self.character_class.roll_hp(hp_modifier)
        logger.debug(
            f"{self.name} rolled {hp_roll} for HP and got {hp_roll.total_with_modifier} ({hp_roll.total} {hp_modifier})."
        )
        return hp_roll

    def to_dict(self):
        return {
            "name": self.name,
            "character_class_type": self.character_class.class_type.name,
            "level": self.character_class.current_level.level_num,
            "max_hp": self.character_class.max_hp,
            "hp": self.character_class.hp,
            "experience_points": self.character_class.xp,
            "abilities": {k.value: v.to_dict() for k, v in self.abilities.items()},
            "inventory": self.inventory.to_dict(),
        }

    @classmethod
    def from_dict(cls, data_dict: dict):
        pc = cls(
            name=data_dict["name"],
            character_class_type=CharacterClassType[data_dict["character_class_type"]],
            level=data_dict["level"],
        )
        pc.abilities = {
            AbilityType[k.upper()]: getattr(
                osrlib.ability, AbilityType[v["ability_type"]].value
            )(score=v["score"])
            for k, v in data_dict["abilities"].items()
        }
        pc.character_class.max_hp = data_dict["max_hp"]
        pc.character_class.hp = data_dict["hp"]
        pc.character_class.xp = data_dict["experience_points"]
        pc.inventory = Inventory.from_dict(data_dict["inventory"], pc)

        return pc

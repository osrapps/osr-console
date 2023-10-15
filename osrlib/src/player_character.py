"""This module contains the PlayerCharacter class."""
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
from osrlib import character_classes, dice_roller, item
from osrlib.inventory import Inventory


class PlayerCharacter:
    """Represents a player character (PC) in the game.

    Attributes:
        name (str): The name of the character.
        abilities (dict): A dictionary of the character's abilities.
        character_class (CharacterClass): The character's class.
        inventory (Inventory): The character's inventory.
    """

    def __init__(
        self,
        name: str,
        character_class_type: character_classes.CharacterClassType,
        level: int = 1,
    ):
        """Initialize a new PlayerCharacter (PC) instance."""
        self.name = name
        self.abilities = {}
        self.roll_abilities()
        self.character_class = None
        self.set_character_class(character_class_type, level)

        self.inventory = Inventory(self)

    def __str__(self):
        """Get a string representation of the PlayerCharacter instance.

        Returns:
            str: A string representation of the PlayerCharacter instance.
        """
        ability_str = ", ".join(f"{ability.name}: {attr.score:>2}" for ability, attr in self.abilities.items())
        return (
            f"Name: {self.name}, "
            f"Class: {self.character_class.class_type.name}, "
            f"Level: {self.character_class.current_level.level_num:2}, "
            f"HP: {self.character_class.hp:3}, "
            f"AC: {self.armor_class:2}, "
            f"XP: {self.character_class.xp:7}, "
            f"{ability_str}"
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
    def armor_class(self):
        """Get the armor class of the character."""
        armor_class = 9
        armor_class += self.abilities[AbilityType.DEXTERITY].modifiers[ModifierType.AC]
        armor_class += sum(armor_item.ac_modifier for armor_item in self.inventory.armor if armor_item.is_equipped)
        return armor_class

    def get_ability_roll(self):
        """Rolls a 4d6 and returns the sum of the three highest rolls."""
        roll = dice_roller.roll_dice("4d6", drop_lowest=True)
        return roll.total

    def set_character_class(self, character_class_type: character_classes.CharacterClassType, level: int = 1):
        """Sets the character class of the character."""
        # TODO: Add validation to prevent setting a class if the class' ability score prerequisites aren't met
        self.character_class = character_classes.CharacterClass(
            character_class_type,
            level,
            self.abilities[AbilityType.CONSTITUTION].modifiers[ModifierType.HP],
        )
        return self.character_class

    def grant_xp(self, xp: int) -> character_classes.ClassLevel:
        """Grants XP to the character, taking into account their Constitution ability modifier, if any."""
        self.character_class.xp += xp
        try:
            # Need to pass the character's Constitution modifier all the way down to the roll_hp method
            return self.character_class.level_up(self.abilities[AbilityType.CONSTITUTION].modifiers[ModifierType.HP])
        except ValueError as e:
            print(e)

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

    def roll_hp(self) -> dice_roller.DiceRoll:
        """Rolls the character's hit points, taking into account their Constitution modifier, if any.

        The total value of the roll with modifier can be negative after if the roll was low and the character has a
        negative Constitution modifier. You should clamp the value to 1 before applying it to the character's HP.

        Returns:
            DiceRoll: The result of the HP roll. Value with modifiers can be negative.
        """
        hp_modifier = self.abilities.get(AbilityType.CONSTITUTION).modifiers[ModifierType.HP]

        return self.character_class.roll_hp(hp_modifier)

    def add_item_to_inventory(self, item: item.Item):
        return self.inventory.add_item(item)

    def get_item_from_inventory(self, item: item.Item):
        return self.inventory.get_item(item)

    def remove_item_from_inventory(self, item: item.Item):
        return self.inventory.remove_item(item)

    def equip_item(self, item: item.Item):
        return self.inventory.equip_item(item)

    def unequip_item(self, item: item.Item):
        return self.inventory.unequip_item(item)

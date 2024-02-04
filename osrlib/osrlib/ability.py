"""Defines `PlayerCharacter` abilities and their modifiers.

Abilities are inherent traits that every [PlayerCharacter][osrlib.player_character.PlayerCharacter] possesses in
varying degrees. They provide different modifiers (bonuses or penalties) that can affect gameplay mechanics like dice
rolls during game play or core aspects of the character like whether they're especially hard to hit (lower AC) because
of a high [Dexterity][osrlib.ability.Dexterity] score or whether they know additional languages because of a high
[Intelligence][osrlib.ability.Intelligence] score.


"""

from abc import ABC, abstractmethod

from osrlib.enums import AbilityType, CharacterClassType, ModifierType


class Ability(ABC):
    """Abstract base class for character abilities.

    Attributes:
        score (int): The raw ability score.
        modifiers (dict): A mapping of the ability's modifier types to modifier values based on the
            ability score.
    """

    _MODIFIER_MAP = {
        3: -3,
        4: -2,
        5: -2,
        6: -1,
        7: -1,
        8: -1,
        13: 1,
        14: 1,
        15: 1,
        16: 2,
        17: 2,
        18: 3,
    }

    def __init__(self, score: int):
        """Initialize Ability with a score.

        Args:
            score (int): The raw ability score.
        """
        self.ability_type = None
        self.score = score
        self.modifiers = {}
        self._init_modifiers()
        self.prime_requisite_classes = []

    def __str__(self):
        """Return string representation of the ability."""
        modifiers_str = ", ".join(
            f"{mod.value}: {'+' if val > 0 else ''}{val}"
            for mod, val in self.modifiers.items()
        )
        return f"{self.ability_type.value}: {self.score} - {modifiers_str}"

    def get_earned_xp_adjustment(self) -> float:
        """Calculate the experience points adjustment based on the ability score.

        Determines the percentage adjustment to experience points earned, based on the character's
        ability score. This adjustment can be positive or negative depending on the score.

        Returns:
            float: The experience point adjustment as a decimal percentage.
        """
        if self.score >= 16:
            return 0.10
        elif self.score >= 13:
            return 0.05
        elif self.score >= 9:
            return 0.0
        elif self.score >= 6:
            return -0.10
        else:
            return -0.20

    @abstractmethod
    def _init_modifiers(self) -> None:
        """Initialize ability modifiers in subclasses.

        Subclasses must implement this method to define specific modifiers for each ability type.
        These modifiers adjust various gameplay mechanics like bonuses and penalties for dice rolls
        or adjustments to experience points earned.
        """
        pass

    def _get_modifier(self) -> int:
        return self._MODIFIER_MAP.get(self.score, 0)

    def to_dict(self) -> dict:
        """Convert ability instance to a dictionary for serialization.

        Useful for serializing and transferring the ability's data during a game save operation.

        Returns:
            dict: Dictionary containing the ability's type and score.
        """
        return {
            "ability_type": self.ability_type.name,
            "score": self.score,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Ability":
        """Create an ability instance from a dictionary.

        Useful for deserializing the ability's data during a game load operation.

        Args:
            data (dict): Dictionary containing the ability's type and score.

        Returns:
            Ability: Instance of the Ability class or its subclasses.
        """
        ability = cls(score=data["score"])
        return ability


class Strength(Ability):
    """Represents the Strength ability for characters.

    Strength measures muscle power and the ability to use that power.
    It primarily influences hand-to-hand combat and opening doors.

    Modifiers:

    - TO_HIT (`ModifierType.TO_HIT`): Modifies melee (hand-to-hand) attack rolls.
    - DAMAGE (`ModifierType.DAMAGE`): Modifies damage in melee combat.
    - OPEN_DOORS (`ModifierType.OPEN_DOORS`): Modifies chances of opening stuck doors.
    """

    def __init__(self, score: int):
        """Initialize a new Strength instance.

        Args:
            score (int): The raw ability score.
        """
        super().__init__(score)
        self.ability_type = AbilityType.STRENGTH
        self.prime_requisite_classes = [
            CharacterClassType.FIGHTER,
            CharacterClassType.DWARF,
            CharacterClassType.ELF,
            CharacterClassType.HALFLING,
        ]

    def _init_modifiers(self) -> None:
        """Initialize Strength-specific ability modifiers.

        Modifiers:

        - TO_HIT (ModifierType.TO_HIT): Modifies melee (hand-to-hand) attack rolls.
        - DAMAGE (ModifierType.DAMAGE): Modifies damage in melee combat.
        - OPEN_DOORS (ModifierType.OPEN_DOORS): Modifies chances of opening stuck doors.

        Each modifier is calculated based on the strength score of the character.
        """
        self.modifiers[ModifierType.TO_HIT] = self._get_modifier()
        self.modifiers[ModifierType.DAMAGE] = self._get_modifier()
        self.modifiers[ModifierType.OPEN_DOORS] = self._get_modifier()


class Intelligence(Ability):
    """Represents the Intelligence ability for characters.

    Intelligence is a measure of problem-solving ability, linguistic capability, and
    magical aptitude.

    Modifiers:

    - LANGUAGES (ModifierType.LANGUAGES): Modifies the number of additional languages the
            character can read and write.
    """

    def __init__(self, score: int):
        """Initialize a new Intelligence instance.

        Args:
            score (int): The raw ability score.
        """
        super().__init__(score)
        self.ability_type = AbilityType.INTELLIGENCE
        self.prime_requisite_classes = [
            CharacterClassType.MAGIC_USER,
            CharacterClassType.ELF,
        ]

    # Overriding because we can't use the standard map for languages
    _MODIFIER_MAP = {
        13: 1,
        14: 1,
        15: 1,
        16: 2,
        17: 2,
        18: 3,
    }

    def _init_modifiers(self) -> None:
        """Initialize Intelligence-specific ability modifiers.

        Modifiers:

        - LANGUAGES (ModifierType.LANGUAGES): Modifies the number of additional languages
            the character can read and write.

        The modifier is calculated based on the intelligence score of the character.
        """
        self.modifiers[ModifierType.LANGUAGES] = self._get_modifier()


class Wisdom(Ability):
    """Represents the Wisdom ability for characters.

    Wisdom measures a character's common sense, intuition, and willpower.

    Modifiers:

    - SAVING_THROWS (ModifierType.SAVING_THROWS): Modifies saving throws against spells and
        magical effects.
    """

    def __init__(self, score: int):
        """Initialize a new Wisdom instance.

        Args:
            score (int): The raw ability score.
        """
        super().__init__(score)
        self.ability_type = AbilityType.WISDOM
        self.prime_requisite_classes = [CharacterClassType.CLERIC]

    def _init_modifiers(self) -> None:
        """Initialize Wisdom-specific ability modifiers.

        Modifiers:
            SAVING_THROWS (ModifierType.SAVING_THROWS): Modifies saving throws against spells
            and magical effects.

        Each modifier is calculated based on the wisdom score of the character.
        """
        self.modifiers[ModifierType.SAVING_THROWS] = self._get_modifier()


class Dexterity(Ability):
    """Represents the Dexterity ability for characters.

    Dexterity measures agility, reflexes, and coordination.

    Modifiers:

    - TO_HIT (ModifierType.TO_HIT): Modifies ranged attack rolls.
    - AC (ModifierType.AC): Modifies armor class (lower is better).
    - INITIATIVE (ModifierType.INITIATIVE): Modifies initiative rolls.
    """

    def __init__(self, score: int):
        """Initialize a new Intelligence instance.

        Args:
            score (int): The raw ability score.
        """
        super().__init__(score)
        self.ability_type = AbilityType.DEXTERITY
        self.prime_requisite_classes = [
            CharacterClassType.THIEF,
            CharacterClassType.HALFLING,
        ]

    # We need to use both the **standard map** and
    # a **custom map** for initiative because its
    # modifiers deviate from the standard map.
    _INITIATIVE_MODIFIER_MAP = {
        3: -2,
        4: -1,
        5: -1,
        6: -1,
        7: -1,
        8: -1,
        13: 1,
        14: 1,
        15: 1,
        16: 1,
        17: 1,
        18: 2,
    }

    def _get_initiative_modifier(self) -> int:
        return self._INITIATIVE_MODIFIER_MAP.get(self.score, 0)

    def _init_modifiers(self) -> None:
        """Initialize Dexterity-specific ability modifiers.

        Modifiers:

        - TO_HIT (ModifierType.TO_HIT): Modifies ranged attack rolls.
        - AC (ModifierType.AC): Modifies armor class (lower is better).
        - INITIATIVE (ModifierType.INITIATIVE): Modifies initiative rolls.

        Each modifier is calculated based on the dexterity score of the character.
        """
        self.modifiers[ModifierType.AC] = -self._get_modifier()
        self.modifiers[ModifierType.TO_HIT] = self._get_modifier()
        self.modifiers[ModifierType.INITIATIVE] = self._get_initiative_modifier()


class Constitution(Ability):
    """Represents the Constitution ability for characters.

    Constitution measures stamina, endurance, and overall health.

    Modifiers:

    - HP (ModifierType.HP): Modifies hit point (HP) rolls. For example, when initially rolling the
        character or when the character gains a level.
    """

    def __init__(self, score: int):
        """Initialize a new Constitution instance.

        Args:
            score (int): The raw ability score.
        """
        super().__init__(score)
        self.ability_type = AbilityType.CONSTITUTION

    def _init_modifiers(self) -> None:
        """Initialize Constitution-specific ability modifiers.

        Modifiers:
            HP (ModifierType.HP): Modifies hit point (HP) rolls. For example, when initially rolling
            the character or when the character gains a level.

        The modifier is calculated based on the constitution score of the character.
        """
        self.modifiers[ModifierType.HP] = self._get_modifier()


class Charisma(Ability):
    """Represents the Charisma ability for characters.

    Charisma measures force of personality, leadership ability, and physical attractiveness.

    Modifiers:

    - REACTION (ModifierType.REACTION): Modifies reaction rolls when interacting with NPCs.
    """

    def __init__(self, score: int):
        """Initialize a new Charisma instance.

        Args:
            score (int): The raw ability score.
        """
        super().__init__(score)
        self.ability_type = AbilityType.CHARISMA

    # Overriding because we can't use the standard map for reactions
    _MODIFIER_MAP = {
        3: -2,
        4: -1,
        5: -1,
        6: -1,
        7: -1,
        8: -1,
        13: 1,
        14: 1,
        15: 1,
        16: 1,
        17: 1,
        18: 2,
    }

    def _init_modifiers(self) -> None:
        """Initialize Charisma-specific ability modifiers.

        Modifiers:

        - REACTION (ModifierType.REACTION): Modifies reaction rolls when interacting with NPCs.

        The modifier is calculated based on the charisma score of the character.
        """
        self.modifiers[ModifierType.REACTION] = self._get_modifier()

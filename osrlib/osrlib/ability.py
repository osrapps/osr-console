"""Defines player character abilities."""

from abc import ABC, abstractmethod
from enum import Enum

from osrlib.character_classes import CharacterClassType
from osrlib.combat import ModifierType


class AbilityType(Enum):
    """Enum representing the types of abilities."""

    STRENGTH = "Strength"
    INTELLIGENCE = "Intelligence"
    WISDOM = "Wisdom"
    DEXTERITY = "Dexterity"
    CONSTITUTION = "Constitution"
    CHARISMA = "Charisma"


class Ability(ABC):
    """Abstract base class for character abilities.

    Abilities are inherent traits that every character possesses in varying degrees.
    They provide different kinds of modifiers which can affect different game actions.

    Attributes:
        score (int): The raw ability score.
        modifiers (dict): A mapping of the ability's modifier types to modifier values based on the ability score.
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
        self.init_modifiers()
        self.prime_requisite_classes = []

    def __str__(self):
        """Return string representation of the ability."""
        modifiers_str = ", ".join(f"{mod.value}: {'+' if val > 0 else ''}{val}" for mod, val in self.modifiers.items())
        return f"{self.ability_type.value}: {self.score} - {modifiers_str}"

    def get_earned_xp_adjustment(self):
        """Get the experience adjustment for the ability score."""
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
    def init_modifiers(self):
        """Abstract method to initialize ability modifiers."""
        pass

    def _get_modifier(self) -> int:
        return self._MODIFIER_MAP.get(self.score, 0)

    def to_dict(self) -> dict:
        return {
            "ability_type": self.ability_type.name,
            "score": self.score,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Ability":
        ability = cls(score=data["score"])

        return ability


class Strength(Ability):
    """Represents the Strength ability for characters.

    Strength measures muscle power and the ability to use that power.
    It primarily influences hand-to-hand combat and opening doors.

    Modifiers:
        TO_HIT: Modifier to hand-to-hand attack rolls.
        DAMAGE: Modifier to damage in hand-to-hand combat.
        OPEN_DOORS: Modifier to chances of opening stuck doors.
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

    def init_modifiers(self):
        """Initialize the Strength modifiers.

        Modifiers:
            TO_HIT: Modifier to hand-to-hand attack rolls.
            DAMAGE: Modifier to damage in hand-to-hand combat.
            OPEN_DOORS: Modifier to chances of opening stuck doors.
        """
        self.modifiers[ModifierType.TO_HIT] = self._get_modifier()
        self.modifiers[ModifierType.DAMAGE] = self._get_modifier()
        self.modifiers[ModifierType.OPEN_DOORS] = self._get_modifier()


class Intelligence(Ability):
    """Represents the Intelligence ability for characters.

    Intelligence is a measure of problem-solving ability, linguistic capability, and magical aptitude.

    Modifiers:
        LANGUAGES: Modifier to the number of additional languages the character can learn.
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

    def init_modifiers(self):
        """Initialize the Intelligence modifiers.

        Modifiers:
            LANGUAGES: Modifier to the number of additional languages the character can learn.
        """
        self.modifiers[ModifierType.LANGUAGES] = self._get_modifier()


class Wisdom(Ability):
    """Represents the Wisdom ability for characters.

    Wisdom measures a character's common sense, intuition, and willpower.

    Modifiers:
        SAVING_THROWS: Modifier to saving throws against spells and magical effects.
    """

    def __init__(self, score: int):
        """Initialize a new Wisdom instance.

        Args:
            score (int): The raw ability score.
        """
        super().__init__(score)
        self.ability_type = AbilityType.WISDOM
        self.prime_requisite_classes = [CharacterClassType.CLERIC]

    def init_modifiers(self):
        """Initialize the Wisdom modifiers.

        Modifiers:
            SAVING_THROWS: Modifier to saving throws against spells and magical effects.
        """
        self.modifiers[ModifierType.SAVING_THROWS] = self._get_modifier()


class Dexterity(Ability):
    """Represents the Dexterity ability for characters.

    Dexterity measures agility, reflexes, and coordination.

    Modifiers:
        TO_HIT: Modifier to ranged attack rolls.
        AC: Modifier to Armor Class (inverts standard modifier since lower AC is better).
        INITIATIVE: Modifier to initiative rolls.
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

    def init_modifiers(self):
        """Initialize the Dexterity modifiers.

        Modifiers:
            TO_HIT: Modifier to ranged attack rolls.
            AC: Modifier to Armor Class (inverts standard modifier since lower AC is better).
            INITIATIVE: Modifier to initiative rolls.
        """
        self.modifiers[ModifierType.AC] = -self._get_modifier()  # Lower-is-better for AC
        self.modifiers[ModifierType.TO_HIT] = self._get_modifier()
        self.modifiers[ModifierType.INITIATIVE] = self._get_initiative_modifier()


class Constitution(Ability):
    """Represents the Constitution ability for characters.

    Constitution measures stamina, endurance, and overall health.

    Modifiers:
        HP: Modifier to Hit Points gained per level.
    """

    def __init__(self, score: int):
        """Initialize a new Constitution instance.

        Args:
            score (int): The raw ability score.
        """
        super().__init__(score)
        self.ability_type = AbilityType.CONSTITUTION

    def init_modifiers(self):
        """Initialize the Constitution modifiers.

        Modifiers:
            HP: Modifier to Hit Points gained per level.
        """
        self.modifiers[ModifierType.HP] = self._get_modifier()


class Charisma(Ability):
    """Represents the Charisma ability for characters.

    Charisma measures force of personality, leadership ability, and physical attractiveness.

    Modifiers:
        REACTION: Modifier to reaction rolls when interacting with NPCs.
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

    def init_modifiers(self):
        """Initialize the Charisma modifiers.

        Modifiers:
            REACTION: Modifier to reaction rolls when interacting with NPCs.
        """
        self.modifiers[ModifierType.REACTION] = self._get_modifier()

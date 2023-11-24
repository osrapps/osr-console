from enum import Enum

class CharacterClassType(Enum):
    """Specifies the class, or profession, of a player character or NPC."""

    CLERIC = "Cleric"
    DWARF = "Dwarf"
    ELF = "Elf"
    FIGHTER = "Fighter"
    HALFLING = "Halfling"
    MAGIC_USER = "Magic User"
    THIEF = "Thief"
    COMMONER = "Commoner"


class OpenAIModelVersion(Enum):
    """Specifies the version of the OpenAI model to use."""
    DEFAULT = "gpt-3.5-turbo-1106"
    GPT35 = "gpt-3.5"
    GPT35TURBO = "gpt-3.5-turbo-1106"
    GPT4 = "gpt-4"
    GPT4TURBO = "gpt-4-1106-preview"


class PartyReaction(Enum):
    """Specifies the reaction of a PC or monster party at the start of an encounter."""

    FIGHT = "Fight"
    RUN = "Run"
    TALK = "Talk"
    PASS = "Pass"

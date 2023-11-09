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

class PartyReaction(Enum):
    """Specifies the reaction of a PC or monster party at the start of an encounter."""

    FIGHT = "Fight"
    RUN = "Run"
    TALK = "Talk"
    PASS = "Pass"

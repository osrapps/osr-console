from collections import deque
from typing import Optional
import random
from osrlib.party import Party
from osrlib.monster import Monster, MonsterParty
from osrlib.game_manager import logger
from osrlib.player_character import PlayerCharacter


class Encounter:
    """An encounter represents something the party discovers, confronts, or experiences within a location in a dungeon.

    An encounter typically represents a group of monsters the party must fight, but it can also represent a trap, a
    puzzle, or other non-combat encounter.

    Attributes:
        name (str): The name or ID of the encounter.
        description (str): The description of the encounter (location, environment, etc.).
        monsters (MonsterParty): The party of monsters in the encounter.
        treasure (list): A list of the treasure in the encounter. The treasure can be any item like weapons, armor, quest pieces, or gold pieces (or gems or other valuables). Optional.
        turn_order (deque): A deque of the combatants in the encounter, sorted by initiative roll.
        is_started (bool): Whether the encounter has started.
        is_ended (bool): Whether the encounter has ended.
    """

    def __init__(
        self,
        name,
        description: str = "",
        monster_party: MonsterParty = None,
        treasure: list = [],
    ):
        """Initialize the encounter object.

        Args:
            name (str): The name or ID of the encounter.
            description (str): The description of the encounter (location, environment, etc.). Optional.
            monsters (MonsterParty): The party of monsters in the encounter. Optional.
            treasure (list): A list of the treasure in the encounter. The treasure can be any item like weapons, armor, quest pieces, or gold pieces (or gems or other valuables). Optional.
        """
        self.name = name
        self.description = description
        self.monster_party = monster_party
        # self.npc = npc # TODO: Implement NPC class
        self.treasure = treasure
        self.pc_party: Optional[Party] = None
        self.combat_queue: deque = deque()
        self.is_started: bool = False
        self.is_ended: bool = False
        self.current_round: Optional[CombatRound] = None

    def __str__(self):
        """Return a string representation of the encounter."""
        return f"{self.name}: {self.description}"

    def start_encounter(self, party: Party):
        self.is_started = True
        logger.debug(f"Starting encounter '{self.name}'...")

        self.pc_party = party

        if self.monster_party is None:
            logger.debug(f"Encounter {self.name} has no monsters - continuing as non-combat encounter.")
            return

        # 1. **Surprise check**: The DM rolls `1d6` for monster party and PC party to check for surprise.
        #    - If monster roll is higher: party is surprised and monsters attack.
        #    - If PC roll is higher: monsters are surprised and PCs choose their reaction (fight, run, talk, pass).
        #    - If it's a tie: same as PC roll is higher.
        pc_party_surprise_roll = self.pc_party.get_surprise_roll()
        monster_party_surprise_roll = self.monster_party.get_surprise_roll()

        if pc_party_surprise_roll > monster_party_surprise_roll:
            logger.debug(f"Monsters are surprised! PC surprise roll: {pc_party_surprise_roll}, monster surprise roll: {monster_party_surprise_roll}")
        elif monster_party_surprise_roll > pc_party_surprise_roll:
            logger.debug(f"PCs are surprised! PC surprise roll:: {pc_party_surprise_roll}, monster surprise roll: {monster_party_surprise_roll}")
        else:
            logger.debug(f"PC party and monsters both rolled {pc_party_surprise_roll} for surprise.")

        # 2. **PC reaction**:
        #    - If PC party chooses to fight, combat begins.
        #    - If PC party runs away, the encounter ends.

    def start_combat(self):
        logger.debug(f"Starting combat in encounter '{self.name}'...")

        # Get initiative rolls for both parties
        party_initiative = [(pc, pc.get_initiative_roll()) for pc in self.pc_party.members]
        monster_initiative = [(monster, monster.get_initiative_roll()) for monster in self.monster_party.members]

        # Combine and sort the combatants by initiative roll
        combatants_sorted_by_initiative = sorted(party_initiative + monster_initiative, key=lambda x: x[1], reverse=True)

        # Populate the combat queue
        logger.debug(f"Populating combat queue with {len(party_initiative)} PCs and {len(monster_initiative)} monsters ({len(combatants_sorted_by_initiative)} total):")
        self.combat_queue.extend(combatants_sorted_by_initiative)
        for combatant in self.combat_queue:
            logger.debug(f"Initiative {combatant[1]}: {combatant[0].name}")

    def execute_combat_round(self):

        # Deque first combatant to act
        attacker = self.combat_queue.popleft()[0]

        # If combatant is PC, player chooses a monster to attack
        if attacker is PlayerCharacter:
            logger.debug(f"PC {attacker.name} (HP: {attacker.character_class.hp}) turn to act.")
            # defender = NOT_YET_IMPLEMENTED # TODO: Player needs to be given option to select a target here - how?
        elif attacker is Monster:
            logger.debug(f"{attacker.name}'s ({attacker.hit_points}/{attacker.max_hit_points}) turn to act.")
            # Choose target at random since attacker is monster
            defender = random.choice(self.pc_party.members)


        # 3. If weapon attack, roll `1d20` to hit; if PC and melee add To Hit modifier, if ranged add Dexterity modifier and other to-hit modifiers
        #    - If weapon hits, roll damage
        #    - Add Strength and other damage modifiers as applicable
        # 4. If spell attack, target rolls save vs. spells

        # Add the attacker back into the combat queue
        self.combat_queue.append((attacker, 0))

    def end_encounter(self):

        # TODO: Award XP and treasure to PCs if monster party is defeated

        self.is_started = False
        self.is_ended = True


class CombatRound:
    """A combat round represents a single round of combat in an encounter."""

    pass
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
        self.combat_log: list = []

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

        pc_party_surprise_roll = self.pc_party.get_surprise_roll()
        monster_party_surprise_roll = self.monster_party.get_surprise_roll()

        if pc_party_surprise_roll > monster_party_surprise_roll or pc_party_surprise_roll == monster_party_surprise_roll:
            logger.debug(f"Monsters are surprised!")
            # TODO: Get player input to determine if PCs want to attack or run away, but for now, just start combat.
            self._start_combat()
        elif monster_party_surprise_roll > pc_party_surprise_roll:
            logger.debug(f"PCs are surprised!")
            self._start_combat()

    def _start_combat(self):
        logger.debug(f"Starting combat in encounter '{self.name}'...")

        # Get initiative rolls for both parties
        party_initiative = [(pc, pc.get_initiative_roll()) for pc in self.pc_party.members]
        monster_initiative = [(monster, monster.get_initiative_roll()) for monster in self.monster_party.members]

        # Combine and sort the combatants by initiative roll
        combatants_sorted_by_initiative = sorted(party_initiative + monster_initiative, key=lambda x: x[1], reverse=True)

        # Populate the combat queue
        self.combat_queue.extend(combatants_sorted_by_initiative)

        # Start combat
        round_num = 0 # Track rounds for spell and other time-based effects
        while self.pc_party.is_alive and self.monster_party.is_alive and round_num < 1000:
            round_num += 1
            self.execute_combat_round(round_num)

        # All members of one party killed - end the encounter
        self.end_encounter()

    def execute_combat_round(self, round_num: int):
        logger.debug(f"Starting combat round {round_num}...")

        # Deque first combatant to act
        attacker = self.combat_queue.popleft()[0]

        # If combatant is PC, player chooses a monster to attack
        if attacker in self.pc_party.members:
            # TODO: Get player input for next action, but for now, just attack a random monster
            defender = random.choice([monster for monster in self.monster_party.members if monster.is_alive])
            needed_to_hit = attacker.character_class.current_level.get_to_hit_target_ac(defender.armor_class)
            attack_roll = attacker.get_attack_roll()
            if attack_roll.total_with_modifier >= needed_to_hit:
                damage_roll = attacker.get_damage_roll()
                defender.apply_damage(damage_roll.total_with_modifier)
                logger.debug(f"{attacker.name} ({attacker.character_class.class_type.value}) attacked {defender.name} and rolled {attack_roll.total_with_modifier} on {attack_roll} for {damage_roll.total_with_modifier} damage.")
            else:
                logger.debug(f"{attacker.name} ({attacker.character_class.class_type.value}) attacked {defender.name} and rolled {attack_roll.total_with_modifier} on {attack_roll} and missed.")
        elif attacker in self.monster_party.members:
            defender = random.choice([pc for pc in self.pc_party.members if pc.is_alive])
            needed_to_hit = attacker.get_to_hit_target_ac(defender.armor_class)
            for attack_roll in attacker.get_attack_rolls():
                if defender.is_alive and attack_roll.total_with_modifier >= needed_to_hit:
                    damage_roll = attacker.get_damage_roll()
                    defender.apply_damage(damage_roll.total_with_modifier)
                    logger.debug(f"{attacker.name} attacked {defender.name} and rolled {attack_roll.total_with_modifier} on {attack_roll} for {damage_roll.total_with_modifier} damage.")
                else:
                    logger.debug(f"{attacker.name} attacked {defender.name} and rolled {attack_roll.total_with_modifier} on {attack_roll} and missed.")

        if not defender.is_alive:
            logger.debug(f"{defender.name} was killed!")

        # Add the attacker back into the combat queue
        self.combat_queue.append((attacker, 0))

    def end_encounter(self):
        logger.debug(f"Ending encounter '{self.name}'...")
        if self.pc_party.is_alive and not self.monster_party.is_alive:
            logger.debug(f"{self.pc_party.name} won the battle! Awarding {self.monster_party.xp_value} experience points to the party...")
            self.pc_party.grant_xp(self.monster_party.xp_value)
        elif not self.pc_party.is_alive and self.monster_party.is_alive:
            logger.debug("The monsters won the battle!")

        self.is_started = False
        self.is_ended = True

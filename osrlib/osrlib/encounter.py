from collections import deque
from typing import Optional
import math
import random
from osrlib.party import Party
from osrlib.monster import MonsterParty
from osrlib.monster_manual import monster_stats_blocks
from osrlib.game_manager import logger, last_message_handler as pylog
from osrlib.dice_roller import roll_dice


class Encounter:
    """An encounter represents something the party discovers, confronts, or experiences at a
    [Location][osrlib.dungeon.Location] in a [Dungeon][osrlib.dungeon.Dungeon].

    An encounter typically represents a group of monsters the party can fight, but it could also just be a notable
    location or other non-combat encounter in which the party receives information or perhaps a quest piece for reaching
    that [Location][osrlib.dungeon.Location].

    Attributes:
        name (str): The name or ID of the encounter.
        description (str): The description of the encounter (location, environment, etc.).
        monsters (MonsterParty): The party of monsters in the encounter.
        treasure (list): A list of the treasure in the encounter. The treasure can be any item like weapons, armor,
                         quest pieces, or gold pieces (or gems or other valuables). Optional.
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
            treasure (list): A list of the treasure in the encounter. The treasure can be any item like weapons, armor,
                             quest pieces, or gold pieces (or gems or other valuables). Optional.
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
        self.log: list = []

    def __str__(self):
        """Return a string representation of the encounter."""
        if self.monster_party is None:
            return f"{self.name}: {self.description}"
        elif len(self.monster_party.members) == 0:
            return f"{self.name}: {self.description} (no monsters)"
        else:
            return f"{self.name}: {self.description} ({len(self.monster_party.members)} {self.monster_party.members[0].name if self.monster_party.members else ''})"

    def log_mesg(self, message: str):
        """Log an encounter log message."""
        self.log.append(message)

    def get_encounter_log(self) -> str:
        """Return the encounter log as a string."""
        return "\n".join(self.log)

    def start_encounter(self, party: Party):
        """Start the encounter with the given party.

        This method initiates the encounter and sets up conditions like determining surprise and starting combat if the
        encounter contains a hostile [MonsterParty][osrlib.monster.MonsterParty]. If so, it compares the surprise rolls
        of the player's party and the monster party to decide which party is surprised, then proceeds to start combat
        with its `_start_combat` private method if combat is necessary. If there are no monsters, the encounter proceeds
        as a non-combat scenario.

        Args:
            party (Party): The player's party involved in the encounter.

        Example:
        ```python
        # Assuming 'encounter' is an instance of Encounter and 'player_party' is an instance of Party
        encounter.start_encounter(player_party)

        # This initiates the encounter, determining surprise, starting combat if applicable,
        # and logging the start of the encounter.
        ```
        """
        self.is_started = True
        logger.debug(f"Starting encounter '{self.name}'...")
        self.log_mesg(pylog.last_message)

        self.pc_party = party

        if self.monster_party is None:
            logger.debug(
                f"Encounter {self.name} has no monsters - continuing as non-combat encounter."
            )
            self.log_mesg(pylog.last_message)
            return

        pc_party_surprise_roll = self.pc_party.get_surprise_roll()
        monster_party_surprise_roll = self.monster_party.get_surprise_roll()

        if (
            pc_party_surprise_roll > monster_party_surprise_roll
            or pc_party_surprise_roll == monster_party_surprise_roll
        ):
            logger.debug(f"Monsters are surprised!")
            self.log_mesg(pylog.last_message)
            # TODO: Get player input to determine if PCs want to attack or run away, but for now, just start combat.
            self._start_combat()
        elif monster_party_surprise_roll > pc_party_surprise_roll:
            logger.debug(f"PCs are surprised!")
            self.log_mesg(pylog.last_message)
            self._start_combat()

    def _start_combat(self):
        logger.debug(f"Starting combat in encounter '{self.name}'...")
        self.log_mesg(pylog.last_message)

        # Get initiative rolls for both parties
        party_initiative = [
            (pc, pc.get_initiative_roll()) for pc in self.pc_party.members
        ]
        monster_initiative = [
            (monster, monster.get_initiative_roll())
            for monster in self.monster_party.members
        ]

        # Combine and sort the combatants by initiative roll
        combatants_sorted_by_initiative = sorted(
            party_initiative + monster_initiative, key=lambda x: x[1], reverse=True
        )

        # Populate the combat queue with only the combatant objects
        self.combat_queue.extend(
            [combatant[0] for combatant in combatants_sorted_by_initiative]
        )

        # Start combat
        round_num = 0  # Track rounds for spell and other time-based effects
        while (
            self.pc_party.is_alive and self.monster_party.is_alive and round_num < 1000
        ):
            round_num += 1
            self.execute_combat_round(round_num)

        # All members of one party killed - end the encounter
        self.end_encounter()

    def execute_combat_round(self, round_num: int):
        logger.debug(f"Starting combat round {round_num}...")
        self.log_mesg(pylog.last_message)

        # Deque first combatant to act
        attacker = self.combat_queue.popleft()

        # If combatant is PC, player chooses a monster to attack
        if attacker in self.pc_party.members:
            # TODO: Get player input for next action, but for now, just attack a random monster
            defender = random.choice(
                [monster for monster in self.monster_party.members if monster.is_alive]
            )
            needed_to_hit = attacker.character_class.current_level.get_to_hit_target_ac(
                defender.armor_class
            )
            attack_roll = (
                attacker.get_attack_roll()
            )
            # TODO: Pass attack type (e.g., MELEE, RANGED, SPELL, etc.) to get_attack_roll()
            # TODO: attack_item = attacker.inventory.get_equipped_item_by_type(attack_roll.attack_type)
            weapon = attacker.inventory.get_equipped_weapon().name.lower()

            # Natural 20 always hits and a 1 always misses
            if attack_roll.total == 20 or (
                attack_roll.total > 1
                and attack_roll.total_with_modifier >= needed_to_hit
            ):
                damage_roll = (
                    attacker.get_damage_roll()
                )  # Pass attack type (e.g., MELEE, RANGED, SPELL, etc.) to get_damage_roll()
                damage_multiplier = 1.5 if attack_roll.total == 20 else 1
                damage_mesg_suffix = " CRITICAL HIT!" if attack_roll.total == 20 else ""
                damage_amount = math.ceil(
                    damage_roll.total_with_modifier * damage_multiplier
                )
                defender.apply_damage(damage_amount)

                attack_mesg_suffix = f" for {damage_amount} damage.{damage_mesg_suffix}"
            else:
                attack_mesg_suffix = f" and missed."
            logger.debug(
                f"{attacker.name} ({attacker.character_class}) attacked {defender.name} with their {weapon} ({attack_roll.total_with_modifier} on {attack_roll}){attack_mesg_suffix}"
            )
            self.log_mesg(pylog.last_message)
        elif attacker in self.monster_party.members:
            defender = random.choice(
                [pc for pc in self.pc_party.members if pc.is_alive]
            )
            needed_to_hit = attacker.get_to_hit_target_ac(defender.armor_class)
            for attack_roll in attacker.get_attack_rolls():
                if (
                    defender.is_alive
                    and attack_roll.total_with_modifier >= needed_to_hit
                ):
                    damage_roll = attacker.get_damage_roll()
                    defender.apply_damage(damage_roll.total_with_modifier)
                    logger.debug(
                        f"{attacker.name} attacked {defender.name} and rolled {attack_roll.total_with_modifier} on {attack_roll} for {damage_roll.total_with_modifier} damage."
                    )
                    self.log_mesg(pylog.last_message)
                else:
                    logger.debug(
                        f"{attacker.name} attacked {defender.name} and rolled {attack_roll.total_with_modifier} on {attack_roll} and missed."
                    )
                    self.log_mesg(pylog.last_message)

        if not defender.is_alive:
            logger.debug(f"{defender.name} was killed!")
            self.log_mesg(pylog.last_message)
            self.combat_queue.remove(defender)

        # Add the attacker back into the combat queue
        self.combat_queue.append(attacker)

    def end_encounter(self):
        """Ends an encounter that was previously started with `start_encounter()`.

        This method concludes the encounter, performing actions like determining the outcome if it was a combat
        encounter (whether the player's party or the monsters won) and awarding experience points, if applicable.
        It sets the `is_started` and `is_ended` flags appropriately to indicate that the encounter has concluded,
        and if the player's party won, awards experience points as dictated by the MonsterParty's `xp_value` to
        the party.

        After calling `end_encounter()` is when you can consider the encounter "over," and when you'd typically
        record or otherwise process the play-by-play encounter log available through its `get_encounter_log()`
        method. It's also when you could check to see if any PCs in the player's party have gained a level, and
        perform appopriate actions in your UI (for example) if so.

        Example:
        ```python
        # Assuming 'encounter' is an instance of Encounter, this ends the encounter and
        # awards experience points to the party if appropriate, such as if they defeated
        # a monsters, gained treasure, or both.
        encounter.end_encounter()
        ```
        """
        logger.debug(f"Ending encounter '{self.name}'...")

        if self.pc_party:
            self.log_mesg(pylog.last_message)
            if self.pc_party.is_alive and not self.monster_party.is_alive:
                logger.debug(
                    f"{self.pc_party.name} won the battle! Awarding {self.monster_party.xp_value} experience points to the party..."
                )
                self.log_mesg(pylog.last_message)
                self.pc_party.grant_xp(self.monster_party.xp_value)
            elif not self.pc_party.is_alive and self.monster_party.is_alive:
                logger.debug(f"{self.pc_party.name} lost the battle.")
                self.log_mesg(pylog.last_message)

        self.is_started = False
        self.is_ended = True

    @staticmethod
    def get_random_encounter(dungeon_level: int):
        """Get a random encounter based on the dungeon level.

        The dungeon_level corresponds to the monster's number of hit dice, and the encounter will contain monsters of
        the same type and at that level (number of hit dice). For example, if dungeon_level is 1, the encounter will
        contain monsters with 1d8 (or 1d8+n) hit die. If dungeon_level is 3, the encounter will contain
        monsters with 3 hit dice (or 3d8+n).

        Args:
            dungeon_level (int): The level of dungeon the encounter should be appropriate for.

        Returns:
            Encounter: A random encounter.
        """

        # Get a random monster type from the stats blocks in the monster_manual module. The monster type is based
        # dungeon level and the first number in the monster's hit dice (e.g., the 1 in 1d8 or the 2 in 2d8).
        monsters_of_level = [
            monster
            for monster in monster_stats_blocks
            if roll_dice(monster.hit_dice).num_dice == dungeon_level
        ]
        monster_type = random.choice(monsters_of_level)
        monsters = MonsterParty(monster_type)
        return Encounter(
            name=monster_type.name,
            description=f"Wandering monsters.",
            monster_party=monsters,
        )

    def to_dict(self):
        """Serialize the Encounter instance to a dictionary format.

        This method converts the Encounter's attributes, including the associated MonsterParty, into a dictionary.
        This is particularly useful for saving the state of an encounter to persistent storage.

        Returns:
            dict: A dictionary representation of the Encounter instance.

        Example:
        ```python
        # Assuming 'encounter' is an instance of Encounter
        encounter_dict = encounter.to_dict()

        # The encounter_dict could now be used to store the state of the Encounter,
        # for example by converting the dict to JSON or storing in a database.
        # You could also pass encounter_dict the from_dict() method to recreate
        # the encounter.
        ```
        """
        encounter_dict = {
            "name": self.name,
            "description": self.description,
            "monsters": self.monster_party.to_dict(),
            "treasure": self.treasure,
            "is_ended": self.is_ended,
        }
        return encounter_dict

    @classmethod
    def from_dict(cls, encounter_dict: dict) -> 'Encounter':
        """Deserialize a dictionary into an [Encounter][osrlib.encounter.Encounter] instance.

        This class method creates a new instance of `Encounter` using the data in the dictionary.
        The dictionary should contain keys corresponding to the attributes of an Encounter, including
        a serialized [MonsterParty][osrlib.monster.MonsterParty] instance if there was one in the
        `Encounter` when it was serialized. If the `is_ended` attribute of the `Encounter` being
        deserialized with `from_dict` is `True`, the `Encounter`'s `end_encounter()` method is
        called as part of the deserialization process.

        Example:

        ```python
        # Assuming 'encounter_dict' is a previously serialized Encounter dictionary
        encounter = Encounter.from_dict(encounter_dict)

        # The 'encounter' is now a rehydrated instance of the Encounter class
        ```

        Args:
            encounter_dict (dict): A dictionary containing the encounter's attributes.

        Returns:
            Encounter: An instance of Encounter initialized with the data from the dictionary.
        """
        try:
            name = encounter_dict["name"]
            description = encounter_dict["description"]
            monster_party = MonsterParty.from_dict(encounter_dict["monsters"])
            treasure = encounter_dict["treasure"]
            is_ended = encounter_dict.get("is_ended", False)

            encounter = cls(
                name,
                description,
                monster_party,
                treasure,
            )

            if is_ended and isinstance(is_ended, bool):
                encounter.end_encounter()

            return encounter

        except KeyError as e:
            raise ValueError(f"Missing key in encounter_dict: {e}")

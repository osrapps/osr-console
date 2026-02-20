from collections import deque
from typing import Optional
import random
from osrlib.party import Party
from osrlib.monster import MonsterParty
from osrlib.monster_manual import monster_stats_blocks
from osrlib.utils import logger, last_message_handler as pylog
from osrlib.dice_roller import roll_dice
from osrlib.treasure import Treasure, TreasureType
from osrlib.combat import CombatEngine, EncounterOutcome, EncounterState, EventFormatter


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
        treasure_type (TreasureType, Optional): The type of treasure available for award to the party at this location.
                                                This treasure is in addition to any treasure associated with monsters
                                                defeated by the party if this is a combat encounter.
        turn_order (deque): A deque of the combatants in the encounter, sorted by initiative roll.
        is_started (bool): Whether the encounter has started.
        is_ended (bool): Whether the encounter has ended.
    """

    def __init__(
        self,
        name,
        description: str = "",
        monster_party: MonsterParty = None,
        treasure_type: TreasureType = TreasureType.NONE,
    ):
        """Initialize the encounter object.

        Args:
            name (str): The name or ID of the encounter.
            description (str): The description of the encounter (location, environment, etc.). Optional.
            monster_party (MonsterParty): The party of monsters in the encounter. Optional.
            treasure_type (TreasureType): The type of treasure at this location available for award to the party.
        """
        self.name = name
        self.description = description
        self.monster_party = monster_party
        # self.npc = npc # TODO: Implement NPC class
        self.treasure_type = treasure_type
        self.treasure = Treasure(self.treasure_type)
        self.pc_party: Optional[Party] = None
        self.combat_queue: deque = deque()
        self.is_started: bool = False
        self.is_ended: bool = False
        self.log: list = []
        self.engine: CombatEngine | None = None

    def __str__(self):
        """Return a string representation of the encounter."""
        if self.monster_party is None:
            return f"{self.name}: {self.description}"
        elif len(self.monster_party.members) == 0:
            return f"{self.name}: {self.description} (no monsters)"
        else:
            return f"{self.name}: {self.description} ({len(self.monster_party.members)} {self.monster_party.members[0].name if self.monster_party.members else ''})"

    def log_mesg(self, message: Optional[str]):
        """Log an encounter message.

        Args:
            message (Optional[str]): The message to log. If None, no message is logged.
        """
        if message is not None:
            self.log.append(message)

    def get_encounter_log(self) -> str:
        """Return the encounter log as a string."""
        return "\n".join(self.log)

    def start_encounter(self, party: Party):
        """Start the encounter with the given party.

        This method initiates the encounter and runs combat to completion using the
        state-machine ``CombatEngine``. If there are no monsters, the encounter proceeds
        as a non-combat scenario.

        Args:
            party (Party): The player's party involved in the encounter.
        """
        self.is_started = True
        logger.debug(f"Starting encounter '{self.name}'...")
        self.log_mesg(pylog.last_message)

        self.pc_party = party

        if self.monster_party is None or len(self.monster_party.members) == 0:
            logger.debug(
                f"Encounter {self.name} has no monsters - continuing as non-combat encounter."
            )
            self.log_mesg(pylog.last_message)
            self.end_encounter()
            return

        self.engine = CombatEngine(pc_party=party, monster_party=self.monster_party)
        formatter = EventFormatter()

        # Phase 1: all intents auto-submitted, run to completion.
        # Safety bound prevents infinite loop if engine reaches AWAIT_INTENT.
        max_steps = 10_000
        for _ in range(max_steps):
            result = self.engine.step()
            for event in result.events:
                self.log_mesg(formatter.format(event))
            if self.engine.state == EncounterState.ENDED:
                break
            if result.needs_intent:
                logger.warning(
                    "Combat engine unexpectedly awaiting intent in synchronous mode"
                )
                break

        self.end_encounter()

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

        if self.pc_party and self.monster_party:
            self.log_mesg(pylog.last_message)

            # Determine victory: prefer engine outcome (handles fled monsters),
            # fall back to HP-based check for legacy/non-engine paths.
            pc_won = False
            if self.engine and self.engine.outcome == EncounterOutcome.PARTY_VICTORY:
                pc_won = True
            elif (
                not self.engine
                and self.pc_party.is_alive
                and not self.monster_party.is_alive
            ):
                pc_won = True

            if pc_won:
                awarded_xp = self.monster_party.xp_value + self.treasure.xp_gp_value
                logger.debug(
                    f"{self.pc_party.name} won the battle! Awarding {awarded_xp} experience points to the party..."
                )
                self.log_mesg(pylog.last_message)
                self.pc_party.grant_xp(awarded_xp)
            elif not self.pc_party.is_alive:
                logger.debug(f"{self.pc_party.name} lost the battle.")
                self.log_mesg(pylog.last_message)

        self.is_started = False
        self.is_ended = True

    @classmethod
    def get_random_encounter(cls, dungeon_level: int) -> "Encounter":
        """Get a random encounter appropriate for the specified dungeon level.

        The `dungeon_level` corresponds to the monster's number of hit dice, and the encounter will contain monsters of
        the same type and at that level (number of hit dice). For example, if `dungeon_level` is `1`, the encounter will
        contain monsters with 1d8 or 1d8+n hit die. If `dungeon_level` is `3`, the encounter will contain
        monsters with 3 or 3d8+n hit dice.

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
        return cls(
            name=monster_type.name,
            description=f"Wandering monsters.",
            monster_party=monsters,
        )

    def to_dict(self) -> dict:
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
            "treasure_type": self.treasure_type.value[0],
            "is_ended": self.is_ended,
        }
        return encounter_dict

    @classmethod
    def from_dict(cls, encounter_dict: dict) -> "Encounter":
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
            treasure_type = TreasureType(
                next(
                    filter(
                        lambda x: x.value[0] == encounter_dict["treasure_type"],
                        TreasureType,
                    )
                )
            )  # Convert back to TreasureType enum
            is_ended = encounter_dict.get("is_ended", False)

            encounter = cls(
                name,
                description,
                monster_party,
                treasure_type,
            )

            if is_ended and isinstance(is_ended, bool):
                encounter.end_encounter()

            return encounter

        except KeyError as e:
            raise ValueError(f"Missing key in encounter_dict: {e}")

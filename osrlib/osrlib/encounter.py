from collections import deque
from osrlib.party import Party
from osrlib.monster import MonsterParty

# 1. **Surprise check**: The DM rolls `1d6` for monster party and PC party to check for surprise.
#    - If monster roll is higher: party is surprised and monsters attack.
#    - If PC roll is higher: monsters are surprised and PCs choose their reaction (fight, run, talk, pass).
#    - If it's a tie: same as PC roll is higher.
# 2. **PC reactiont**:
#    - If PC party chooses to fight, combat begins.
#    - If PC party runs away, the encounter ends.
#
# 5. All combatants roll initiative (`1d6`).
# 6. The DM deques first combatant to act.
# 1. Combatant chooses target:
#     - if combatant is PC, player chooses a monster to attack
#     - if combatant is monster, DM chooses target PC at random
# 2. If weapon, roll `1d20` to hit; if PC, if melee add To Hit modifier, if ranged add Dexterity modifier and other to-hit modifiers
# 3. Roll damage if weapon/ranged hit was successful or target failed save vs. spell; if PC, add Strength modifier and other damage modifiers.


class Encounter:
    """An encounter represents something the party discovers, confronts, or experiences within a location in a dungeon.

    An encounter typically represents a group of monsters the party must fight, but it can also represent a trap, a
    puzzle, or other non-combat encounter.

    Attributes:
        name (str): The name or ID of the encounter.
        description (str): The description of the encounter (location, environment, etc.).
        monsters (MonsterParty): The party of monsters in the encounter.
        treasure (list): A list of the treasure in the encounter. The treasure can be any item like weapons, armor, quest pieces, or gold pieces (or gems or other valuables). Optional.
    """

    def __init__(
        self,
        name,
        description: str = "",
        monster_party: MonsterParty = None,
        # npc: NPC = None, # TODO: Implement NPC class
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
        self.pc_party = None

    def __str__(self):
        """Return a string representation of the encounter."""
        return f"{self.name}: {self.description}"

        self.turn_order = deque()

    def start_encounter(self, party: Party):
        self.pc_party = party

        # TODO: Roll for surprise

        # Get initiative rolls for both parties
        party_initiative = [(pc, pc.get_initiative_roll()) for pc in self.pc_party.members]
        monster_initiative = [(monster, monster.get_initiative_roll()) for monster in self.monster_party.members]

        # Combine and sort the combatants by initiative roll
        combined_initiative = sorted(party_initiative + monster_initiative, key=lambda x: x[1].total_with_modifier, reverse=True)

        # Populate the turn order deque
        self.turn_order.extend(combined_initiative)

    def next_turn(self):
        # Rotate the deque to get the next combatant
        current_combatant, _ = self.turn_order.popleft()
        return current_combatant

    # TODO: Implement combat methods
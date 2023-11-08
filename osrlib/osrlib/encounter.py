from osrlib.monster import MonsterParty


class Encounter:
    """An encounter represents a location like a room or cavern and can contain monsters, traps, treasure, and quest pieces.

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
        treasure: list = [],
    ):
        """Initialize an encounter.

        Args:
            name (str): The name or ID of the encounter.
            description (str): The description of the encounter (location, environment, etc.). Optional.
            monsters (MonsterParty): The party of monsters in the encounter. Optional.
            treasure (list): A list of the treasure in the encounter. The treasure can be any item like weapons, armor, quest pieces, or gold pieces (or gems or other valuables). Optional.
        """
        self.name = name
        self.description = description
        self.monster_party = monster_party
        self.treasure = treasure

    def __str__(self):
        """Return a string representation of the encounter."""
        return f"{self.name}: {self.description}"

from osrlib.dice_roller import roll_dice

class Monster:
    """A Monster is a creature the party can encounter in a dungeon and defeat to obtain experience points and optionally treasure and quest pieces.

    Attributes:
        name (str): The name of the monster.
        monster_type (MonsterType): The type of monster (DEMON, DRAGON, HUMANOID, MAGICAL, UNDEAD, etc.)
        description (str): The monster's description.
        hit_dice (str): The hit dice of the monster in NdN format, like "1d8" or "2d6".
        hit_points (int): The number of hit points the monster has.
        weapon (Weapon): The weapon that the monster uses for attacks.
        armor_class (int): The armor class of the monster.
        treasure (list): A list of the treasure that the monster is carrying. The treasure can be any item like weapons, armor, quest pieces, or gold pieces (or gems or other valuables).
    """
    def __init__(self, name, monster_type, description, hit_dice, weapon, armor_class, treasure):
        self.name = name
        self.monster_type = monster_type
        self.description = description
        self.hit_dice = hit_dice
        self.weapon = weapon
        self.armor_class = armor_class
        self.treasure = treasure
        self.hit_points = roll_dice(hit_dice).total_with_modifier

    @property
    def is_alive(self):
        """Get whether the monster is alive.

        Returns:
            int: True if the monster has more than 0 hit points, otherwise False.
        """
        return self.hit_points > 0

    def attack(self):
        """Attack the party with the monster's weapon.

        Returns:
            int: The amount of damage done to the party.
        """
        # attack the party
        damage = self.weapon.attack()
        return damage

    def damage(self, hit_points_damage: int):
        """Apply damage from an attack.

        Args:
            damage (int): The amount of damage done to the monster.
        """
        self.hit_points -= hit_points_damage

    def heal(self, hit_points_healed: int):
        """Heal the monster by restoring the given amount of hit points.

        Args:
            hit_points_healed (int): The amount of hit points to restore.
        """
        self.hit_points += hit_points_healed

    pass
from osrlib.dice_roller import roll_dice
from osrlib.enums import ItemType, TreasureType
from osrlib.item import Item, Weapon, Armor

def get_treasure(treasure_type: TreasureType):
        """Get a collection of items appropriate for the specified treasure type.

        Typical use of this method is to pass it the treasure_type attribute value of a MonsterStatBlock instance
        when determining the treasure to award the party for defeating a monster.

        Args:
            treasure_type (TreasureType): The type of treasure to get.

        Returns:
            list: A list of the items to be awarded as treasure to the party.
        """
        treasure_items = []
        if treasure_type == TreasureType.NONE:
            return None
        elif treasure_type == TreasureType.A:
            pass
        elif treasure_type == TreasureType.B:
            pass
        elif treasure_type == TreasureType.C:
            pass
        elif treasure_type == TreasureType.D:
            pass
        elif treasure_type == TreasureType.E:
            pass
        elif treasure_type == TreasureType.F:
            pass
        elif treasure_type == TreasureType.G:
            pass
        elif treasure_type == TreasureType.H:
            pass
        elif treasure_type == TreasureType.I:
            pass
        elif treasure_type == TreasureType.J:
            pass
        elif treasure_type == TreasureType.K:
            pass
        elif treasure_type == TreasureType.L:
            pass
        elif treasure_type == TreasureType.M:
            pass
        elif treasure_type == TreasureType.N:
            pass
        elif treasure_type == TreasureType.O:
            pass
        elif treasure_type == TreasureType.P:
            pass
        elif treasure_type == TreasureType.Q:
            pass
        elif treasure_type == TreasureType.R:
            pass
        elif treasure_type == TreasureType.S:
            pass
        elif treasure_type == TreasureType.T:
            pass
        elif treasure_type == TreasureType.U:
            pass
        elif treasure_type == TreasureType.V:
            pass
        elif treasure_type == TreasureType.W:
            pass
        elif treasure_type == TreasureType.X:
            pass
        elif treasure_type == TreasureType.Y:
            pass
        elif treasure_type == TreasureType.Z:
            pass

        return treasure_items
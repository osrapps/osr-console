from textual.app import App, ComposeResult

from osrlib import CharacterClassType, PlayerCharacter, Armor, Item, Weapon, Party, Adventure, Dungeon, DungeonMaster, Location, Exit, Direction
from osrlib.party import get_default_party
from screen import CharacterScreen, WelcomeScreen, ExploreScreen


class OSRConsole(App):
    CSS_PATH = "screen.tcss"

    BINDINGS = [
        ("c", "character", "Character"),
        ("e", "explore", "Explore"),
        ("q", "quit", "Quit"),
    ]

    # Set up a test party
    default_party = get_default_party()
    player_character = default_party.get_character_by_index(0)
    armor = Armor("Chain Mail", -5, usable_by_classes = {CharacterClassType.FIGHTER}, max_equipped = 2, gp_value = 40)
    shield = Armor("Shield", -1, usable_by_classes = {CharacterClassType.FIGHTER}, max_equipped = 2, gp_value = 10)
    sword = Weapon("Sword", "1d8", usable_by_classes = {CharacterClassType.FIGHTER}, max_equipped = 1, gp_value = 10)
    backpack = Item("Backpack", gp_value = 5)
    wineskin = Item("Wineskin", gp_value = 1)
    iron_rations = Item("Iron Rations", gp_value = 15)
    torch = Item("Torch", gp_value = 1)
    player_character.inventory.add_item(armor)
    player_character.inventory.add_item(shield)
    player_character.inventory.add_item(sword)
    player_character.inventory.add_item(backpack)
    player_character.inventory.add_item(wineskin)
    player_character.inventory.add_item(iron_rations)
    player_character.inventory.add_item(torch)
    player_character.inventory.equip_item(armor)
    player_character.inventory.equip_item(shield)
    player_character.inventory.equip_item(sword)

    # Set up a test dungeon
    loc0 = Location(9999, 10, 10, [Exit(Direction.NORTH, 1)], ["Randoville", "tavern", "The Beer and Whine"], None)
    loc1 = Location(1, 40, 30, [Exit(Direction.SOUTH, 0), Exit(Direction.NORTH, 2)], ["just outside", "dwarven mines", "ancient", "entrance", "cold wind", "dragon rumors"], None)
    loc2 = Location(2, 10, 10, [Exit(Direction.SOUTH, 1), Exit(Direction.NORTH, 3)], ["vestibule", "large entry doors", "dirty stone", "carvings"], None)
    loc3 = Location(3, 5, 5, [Exit(Direction.SOUTH, 2)], ["guard station", "broken weapons", "bat droppings"], None)
    dungeon = Dungeon("Mine of Deepness - 1", "An ancient lost dwarven mine.", [loc0, loc1, loc2, loc3], 9999)

    # Set up a test adventure
    adventure = Adventure("Sparky's Not-So-Secret Secret")
    adventure.introduction = "Deep in the heart of the Tall Icy Mountains lies the long abandoned Mine of Deepness, a once-thriving dwarven operation now reduced to whispered rumors and tavern tales. Legend holds that a fearsome dragon named Sparky has claimed the labyrinthine tunnels as its lair, its fiery breath illuminating the darkened corridors once chiseled with dwarven precision. The beleaguered town of Randoville has suffered a series of devastating raids, livestock and treasure vanishing in plumes of smoke and flame. Mayor Swiggins Chuggery, desperate and out of options, has commissioned your party to delve into the mine, confirm the presence of the mythical beast, and eliminate the threat that hangs like a dark cloud over the land."
    adventure.add_dungeon(dungeon)
    adventure.set_active_dungeon(dungeon)

    # Initialize the Dungeon Master
    dungeon_master = DungeonMaster(adventure)

    SCREENS = {"scr_character": CharacterScreen(),
               "scr_welcome": WelcomeScreen(),
               "scr_explore": ExploreScreen()}

    def compose(self) -> ComposeResult:
        yield WelcomeScreen()

    def on_mount(self) -> None:
        self.title = "OSR Console"
        self.sub_title = "Adventures in turn-based text"

    def action_character(self) -> None:
        """Show the character screen."""
        self.push_screen("scr_character")

    def action_explore(self) -> None:
        """Show the explore screen."""
        self.push_screen("scr_explore")

    def action_quit(self) -> None:
        """Quit the application."""
        self.exit()


app = OSRConsole()
if __name__ == "__main__":
    app.run()

from textual.app import App, ComposeResult
from screen import CharacterScreen, WelcomeScreen, ExploreScreen

from osrlib.adventure import Adventure
from osrlib.dungeon import Dungeon
from osrlib.party import get_default_party


class OSRConsole(App):
    CSS_PATH = "screen.tcss"

    BINDINGS = [
        ("c", "character", "Character"),
        ("e", "explore", "Explore"),
        ("q", "quit", "Quit"),
    ]

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

    adventure = Adventure("Whispers in the Mystic Forest")
    adventure.introduction = "In the heart of the cursed Mystic Forest, a tale as old as time stirs once again. Legends speak of Glofarnux, an ancient wizard lich whose thirst for arcane knowledge knew no bounds. His lair, known as the Dungeon of the Mad Mage, has remained hidden for centuries, its entrance concealed within a secluded glade, untouched by the ravages of time. Brave adventurers are called to unravel the mysteries lying in the depths of this forgotten dungeon. Within its walls, echoes of the past mingle with the shadows of the present, challenging all who dare to uncover the secrets of Glofarnux and the arcane magic that pulsates through the very stones of the dungeon. Your journey begins at the edge of the Mystic Forest, where the line between myth and reality blurs, and the adventure of a lifetime awaits."

    dungeon = Dungeon.get_random_dungeon("Dungeon of the Mad Mage",
                                                "The first level of the home of the ancient wizard lich Glofarnux, its "
                                                "entrance hidden in a forgotten glade deep in the cursed Mystic Forest.",
                                                num_locations=20)
    dungeon.set_start_location(1)

    if dungeon.validate_location_connections():
        print("Dungeon location connection graph is valid.")

    adventure.add_dungeon(dungeon)
    adventure.set_active_dungeon(dungeon)
    adventure.set_active_party(get_default_party())

app = OSRConsole()
if __name__ == "__main__":
    app.run()

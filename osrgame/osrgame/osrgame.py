from textual.app import App, ComposeResult
from screen_character import CharacterScreen
from screen_welcome import WelcomeScreen
from screen_explore import ExploreScreen
from screen_adventure_browser import AdventureBrowserScreen

from osrlib.adventure import Adventure
from osrlib.dungeon import Dungeon
from osrlib.party import get_default_party


class OSRConsole(App):
    """The OSR Console application."""
    adventure = None

    CSS_PATH = "screen.tcss"

    BINDINGS = [
        ("c", "character", "Character"),
        # ("e", "explore", "Explore"),
        # ("ctrl+l", "load", "Load"),
        ("escape", "app.pop_screen", "Pop screen"),
        ("q", "quit", "Quit"),
    ]

    SCREENS = {
        "scr_adventure_browser": AdventureBrowserScreen(),
        #"scr_adventure_creator": AdventureCreator(),
        "scr_character": CharacterScreen(),
        "scr_explore": ExploreScreen(),
        "scr_welcome": WelcomeScreen(),
    }

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
        if self.adventure is None:
            self.set_active_adventure()
        self.push_screen("scr_explore")

    def action_load(self) -> None:
        """Load a saved adventure."""
        self.set_active_adventure(Adventure.load_adventure("/Users/mmacy/under_in_the_mystic_forest.json"))

    def action_quit(self) -> None:
        """Quit the application."""
        self.exit()

    def set_active_adventure(self, adventure: Adventure = None) -> None:
        """Set the active adventure. If no adventure is provided, a default adventure is created."""
        if adventure is not None:
            self.adventure = adventure
        else:
            default_adventure = Adventure("Raving Mad Under the Mystic Forest")
            default_adventure.description = "An adventure for 4-6 characters of levels 1-3."
            default_adventure.introduction = (
                "In the heart of the cursed Mystic Forest, a tale as old as time stirs once again. Legends "
                "speak of Glofarnux, an ancient wizard lich whose thirst for arcane knowledge knew no bounds. The entrance to the "
                "underground complex he once called home--but for centuries been is tomb--has recently been found. Known now as the "
                "'Dungeon of the Mad Mage,' its entrance is concealed within a seemingly natural rock outcropping in a secluded glade "
                "deep in the Mystic Forest. Brave adventurers, your party, have summone to help unravel the mysteries in depths of "
                "the forgotten subterranean citadel. Within its depth, echoes of the past mingle with the shadows of the present, "
                "challenging all who dare to attempt to learn the secrets of Glofarnux and his once noble but now twisted arcane "
                "magic. Your party stands ready in the oppressive silence of the lost glade in the Mystic Forest, just outside the "
                "once magically concealed outcropping of rock and its now visible entrance open to the depths of the Dungeon of the "
                "Mad Mage."
            )

            dungeon = Dungeon.get_random_dungeon("Dungeon of the Mad Mage",
                                                    "The first level of the home of the ancient wizard lich Glofarnux, its "
                                                    "entrance hidden in a forgotten glade deep in the cursed Mystic Forest.",
                                                    num_locations=50, use_ai=True)
            dungeon.set_start_location(1)

            if dungeon.validate_location_connections():
                print("Dungeon location connection graph is valid.")

            default_adventure.add_dungeon(dungeon)
            default_adventure.set_active_dungeon(dungeon)
            default_adventure.set_active_party(get_default_party())
            self.adventure = default_adventure

app = OSRConsole()
if __name__ == "__main__":
    app.run()

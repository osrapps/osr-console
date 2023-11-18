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

    adventure = Adventure("Castle of the Copper Maiden")
    adventure.introduction = "In the secluded vale of  Lurimara, the palace of Duchess Elara stood tall, crafted from moonlit alabaster echoing the brilliance of winter's dawn. This land, filled with creatures of whispered legends, flourished under Elara's watchful eyes, and was particularly famed for its intricate artifacts and armaments, at the heart of which was a gleaming sapphire termed 'The Luminous Gem.' On an evening bathed in starlight, during a majestic carnival, envy took root amidst celebration. Although the palace boasted chambers painted in hues of crimson and azure, and a terrace granting views of enchanting flora and lustrous vines, it was 'The Luminous Gem' that ensnared every gaze. Rumors speak of mages and sprites, consumed by its beauty, orchestrating its disappearance. When dawn broke, the sapphire was lost, and  Lurimara's peace with it. Now, wyvern's silhouettes darken the skies, with tales of a solitary knight astride it, in pursuit of the lost treasure, echoing through time."

    dungeon = Dungeon.get_random_dungeon(num_locations=20)
    dungeon.set_start_location(1)

    if dungeon.validate_location_connections():
        print("Dungeon location connection graph is valid.")

    adventure.add_dungeon(dungeon)
    adventure.set_active_dungeon(dungeon)
    adventure.set_active_party(get_default_party())

app = OSRConsole()
if __name__ == "__main__":
    app.run()

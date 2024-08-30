import random
from textual.app import App, ComposeResult
from screen_character import CharacterScreen
from screen_welcome import WelcomeScreen
from screen_explore import ExploreScreen
from screen_modal_new_char import NewCharacterModalScreen
from screen_adventure_browser import AdventureBrowserScreen

from osrlib.adventure import Adventure
from osrlib.constants import ADVENTURE_NAMES, DUNGEON_NAMES
from osrlib.dungeon import Dungeon
from osrlib.dungeon_assistant import DungeonAssistant
from osrlib.utils import logger
from osrlib.party import Party
from osrlib.enums import OpenAIModelVersion


class OSRConsole(App):
    """The OSR Console application."""
    player_party = None
    adventure = None
    dungeon_assistant = None

    # To disable AI, set this to OpenAIModelVersion.NONE
    openai_model = OpenAIModelVersion.DEFAULT
    num_dungeon_locations = 10

    CSS_PATH = "screen.tcss"

    BINDINGS = [
        ("escape", "previous_screen", "Back"),
        ("q", "quit", "Quit"),
    ]

    SCREENS = {
        "screen_adventure_browser": AdventureBrowserScreen(),
        "screen_character": CharacterScreen(),
        "screen_explore": ExploreScreen(),
        "screen_welcome": WelcomeScreen(),
        "screen_modal_new_char": NewCharacterModalScreen(),
    }

    def compose(self) -> ComposeResult:
        yield WelcomeScreen()

    def on_mount(self) -> None:
        self.title = "OSR Console"
        self.sub_title = f"Adventures in turn-based text (model: {self.openai_model.value})"

    ### Actions ###

    def action_previous_screen(self) -> None:
        """Return to the previous screen."""
        if len(self.screen_stack) > 1:
            self.pop_screen()

    def action_quit(self) -> None:
        """Quit the application."""
        self.exit()

    def set_active_adventure(self, adventure: Adventure = None) -> None:
        """Set the active adventure. If no adventure is provided, a default adventure is created."""
        if adventure is not None:
            self.adventure = adventure
        else:
            default_adventure = Adventure(random.choice(ADVENTURE_NAMES))
            default_adventure.description = "An adventure for 4-6 characters of levels 1-3."
            default_adventure.introduction = (
                "Deep underground in the heart of the Mystic Forest lives Glofarnux, an ancient wizard lich "
                "whose thirst for arcane knowledge knew no bounds. The entrance to the underground complex he once called "
                "home--but has for centuries been his tomb--was recently found concealed in a seemingly natural rock "
                "outcropping deep in forest. Your party of adventurers have been summoned to help unravel the mysteries "
                "of Glofarnux's subterranean citadel by learning the secrets of Glofarnux and his once noble but now "
                "twisted arcane magic. Your party stands ready in the oppressive silence of the forest, just outside the "
                "once magically hidden entrance now open to the depths of the dungeon."
            )

            dungeon = Dungeon.get_random_dungeon(random.choice(DUNGEON_NAMES),
                                                    "The first level of the home of the ancient wizard lich Glofarnux, "
                                                    "its entrance hidden in a glade deep in the Mystic Forest.",
                                                    num_locations=self.num_dungeon_locations, openai_model=self.openai_model)
            dungeon.set_start_location(1)

            if dungeon.validate_location_connections():
                print("Dungeon location connection graph is valid.")

            default_adventure.add_dungeon(dungeon)
            default_adventure.set_active_dungeon(dungeon)
            default_adventure.set_active_party(Party.get_default_party())
            self.adventure = default_adventure

    def start_session(self) -> str:
        """Start a new session."""

        if self.adventure is None:
            self.set_active_adventure(adventure=None)

        self.dungeon_assistant = DungeonAssistant(self.adventure, openai_model=self.openai_model)
        dm_start_session_response = self.dungeon_assistant.start_session()
        logger.debug(f"DM start session response: {dm_start_session_response}")

        # Move the party to the first location
        first_exit = self.dungeon_assistant.adventure.active_dungeon.get_location_by_id(1).exits[0]
        dm_first_party_move_response = self.dungeon_assistant.move_party(first_exit.direction)
        logger.debug(f"DM first PC move response: {dm_first_party_move_response}")

        return dm_start_session_response + "\n" + dm_first_party_move_response

app = OSRConsole()
if __name__ == "__main__":
    app.run()

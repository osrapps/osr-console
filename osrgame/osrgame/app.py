"""Main application class for the Gold Box-style TUI."""

import random
from pathlib import Path

from textual.app import App

from osrlib.adventure import Adventure
from osrlib.constants import ADVENTURE_NAMES, DUNGEON_NAMES
from osrlib.dungeon import Dungeon
from osrlib.enums import OpenAIModelVersion
from osrlib.party import Party
from osrlib.utils import logger

from .game_state import GameState
from .screens.main_menu import MainMenuScreen
from .screens.town_hub import TownHubScreen


class OSRConsoleApp(App):
    """Gold Box-style dungeon crawler TUI."""

    CSS_PATH = [Path("styles/app.tcss"), Path("styles/character.tcss")]

    BINDINGS = [
        ("q", "quit", "Quit"),
    ]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.game_state = GameState()
        self.ai = None  # AI assistant placeholder (Phase 6)
        self.openai_model = OpenAIModelVersion.NONE
        self.num_dungeon_locations = 10

    def on_mount(self) -> None:
        self.title = "OSR Console"
        self.sub_title = "Gold Box-style dungeon crawler"
        self.push_screen(MainMenuScreen())

    def start_new_game(self) -> None:
        """Create a default adventure with a random dungeon and party, then go to town."""
        adventure = Adventure(random.choice(ADVENTURE_NAMES))
        adventure.description = "An adventure for 4-6 characters of levels 1-3."

        dungeon = Dungeon.get_random_dungeon(
            random.choice(DUNGEON_NAMES),
            "A dark and dangerous dungeon awaits...",
            num_locations=self.num_dungeon_locations,
            openai_model=self.openai_model,
        )
        dungeon.set_start_location(1)

        if dungeon.validate_location_connections():
            logger.debug("Dungeon location connection graph is valid.")

        adventure.add_dungeon(dungeon)
        adventure.set_active_dungeon(dungeon)
        adventure.set_active_party(Party.get_default_party())

        self.game_state.adventure = adventure
        self.game_state.turn_count = 0
        self.game_state.in_dungeon = False
        self.game_state.party_gold = 0
        self.game_state.party_gems = []
        self.game_state.party_jewelry = []

        self.push_screen(TownHubScreen())

    def action_quit(self) -> None:
        self.exit()

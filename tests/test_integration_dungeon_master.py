import pytest
import os
import openai
from osrlib.dungeon_master import DungeonMaster
from osrlib.adventure import Adventure
from osrlib import game_manager as gm
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@pytest.fixture(scope="module")
def setup_openai_api():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip(
            "OpenAI API key must be set as an environment variable for this test."
        )
    openai.api_key = api_key
    yield
    openai.api_key = None


@pytest.mark.flaky(reruns=5, reruns_delay=5)
@pytest.mark.integration
def test_dungeon_master_start_session_real_api(setup_openai_api):
    adventure_description = "In a land shrouded by mist and haunted by forgotten gods, your party stands before the gaping maw of Darkfang Cavern. Rumors abound of an ancient artifact of terrible power hidden deep within, guarded by spectral knights and nightmarish beasts. Will you claim the artifact and ascend to untold glory, or fall like so many before you, your names etched into the cavern's endless walls of sorrow? The choice is yours, brave adventurers. Venture forth!"
    adventure = Adventure("Test Adventure")
    adventure.long_description = adventure_description
    dm = DungeonMaster(adventure)

    message = dm.start_session()
    gm.logger.info(message)
    assert len(message) > 0

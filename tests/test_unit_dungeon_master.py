import pytest
import openai
from osrlib.dungeon_master import DungeonMaster
from osrlib.adventure import Adventure
from osrlib import game_manager as gm

def test_dungeon_master_initialization():
    adventure = Adventure("Test Adventure")
    dm = DungeonMaster(adventure)

    assert dm.adventure == adventure
    assert dm.started == False
    assert 'system' in dm.system_message[0]['role']
    assert 'role' in dm.init_messages[0]
    assert dm.messages == dm.system_message + dm.init_messages

def test_dungeon_master_start_session(mocker):
    adventure = Adventure("Test Adventure")
    dm = DungeonMaster(adventure)

    mocker.patch('openai.ChatCompletion.create', return_value=mocker.Mock())
    mocker.patch('osrlib.game_manager.logger.info')

    dm.start_session()

    openai.ChatCompletion.create.assert_called_once()
    gm.logger.info.assert_called_once()

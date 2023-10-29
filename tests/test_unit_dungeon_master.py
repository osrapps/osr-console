import openai
from osrlib.dungeon_master import DungeonMaster
from osrlib.adventure import Adventure
from osrlib import game_manager as gm

def test_dungeon_master_initialization():
    adventure = Adventure("Test Adventure")
    dm = DungeonMaster(adventure)

    assert dm.adventure == adventure
    assert 'role' in dm.session_messages[0]
    assert 'system' in dm.session_messages[0]['role']
    assert 'role' in dm.session_messages[1]
    assert 'user' in dm.session_messages[1]['role']


def test_dungeon_master_start_session(mocker):
    adventure = Adventure("Test Adventure")
    dm = DungeonMaster(adventure)

    mock_completion = mocker.MagicMock()
    mock_completion.choices = [mocker.MagicMock()]
    mock_completion.choices[0].message = {'content': 'some_content'}
    mocker.patch('openai.ChatCompletion.create', return_value=mock_completion)

    mocker.patch('osrlib.game_manager.logger.info')
    result = dm.start_session()

    assert result == 'some_content'
    openai.ChatCompletion.create.assert_called_once()

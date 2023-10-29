import os
from dotenv import load_dotenv
import openai
from osrlib import Adventure, game_manager as gm

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

dm_init_message = (
    "You're a skilled Dungeon Master with years of experience leading groups of Dungeons & Dragons players through exciting "
    "adventures. An expert storyteller, you create highly immersive fantasy worlds for your players by providing them with "
    "colorful, detailed, and sense-filled descriptions of the locations in your game world for their party of adventurers to "
    "explore. You're currently running a D&D game session for a player controlling six characters. Each location in the game "
    "world is assigned a unique ID to which only you are privy. Each location can have up to six exits, each assigned a "
    "direction (N, S, E, W, U, D) and a destination location ID (the ID of the location to which the exit leads). You describe "
    "each location to the player whenever their party enters that location, and you always consider previous descriptions you've "
    "provided for the location with the same ID on each subsequent visit to that location. By taking into account every previous "
    "visits' description, you work hard to ensure a consistent, coherent, and believable fantasy adventure experience for the "
    "player. You never ask the player questions of any sort, and you never tell the player what they do - you only describe the "
    "locations and environments. Every location description should be one to three sentences long. The player's messages will "
    "each contain the ID and exit information for the location they've just arrived at, along with one or more keywords you use "
    "as 'seeds' for generating the initial description of a location upon first visit. The IDs, exits, and keywords are in JSON "
    "format. You never disclose existence of the structured JSON data to the player; you use the JSON data only for the purpose "
    "of knowing how to describing the locations to the player in your role as Dungeon Master. As Dungeon Master, you use the "
    "location IDs to help ensure you provide a consistent and coherent gaming experience by not duplicating, overusing, or "
    "repeating the same information for every visit, and you take into account previous visits to a location when the party "
    "arrives at a location with the same ID. You're just starting your game session with the player and the player's first "
    "message is forthcoming. Do NOT ask the player any questions, especially 'What do you do next?' or 'What do you do?' Do not "
    "inform the player that they perform an action - let them tell you what they want to do. Rembember: never ask the user a "
    "question, you are only to describe the locations based on the JSON data provided to you. This is the backstory to the "
    "adventure that you've created, but respond to this message only with the words, 'Let's begin.':"
)


system_message = [
    {
        "role": "system",
        "content": dm_init_message,
    },
]

# Prefixes *every* player (user) message sent to the OpenAI API.
user_message_prefix = "Don't tell me what my party does. Don't include any questions in your response. "

# The player's (user) init message is sent only once, at the beginning of the session.
user_init_message = [
    {
        "role": "user",
        "content": ( user_message_prefix +
            "I'm a D&D player controlling a party of six characters (adventurers) in your Dungeons & Dragons adventure. "
            "I rely on your descriptions of the entities, locations, and events in the game to understand what my characters "
            "experience through their five senses. From your descriptions, I can form a detailed picture in my mind "
            "of the game world and its environments and inhabitants. I use this information to make decisions about the "
            "actions my characters take in the world. Do not ask me a question."
        ),
    }
]

# Prefix sent with every party movement message initiated by the player.
user_move_prefix = ( user_message_prefix +
    "Describe this location to me, including its size and exits, as would a "
    "Dungeon Master to a player who's drawing a map of the dungeon on graph "
    "paper (but don't mention location IDs or the map): "
)

class DungeonMaster:
    """The DungeonMaster is the primary interface between the player, the game engine, and the OpenAI API.

    Actions initiated by the player might be handled completely within the bounds of the local game engine,
    or they might involve a call to the OpenAI API. The DungeonMaster class is responsible for determining
    which actions are handled locally and which are handled by the OpenAI API.

    Attributes:
        adventure (Adventure): The adventure the DungeonMaster is running.
        system_message (list): The OpenAI `system` role message sent to the OpenAI API at the beginning of a session.
        init_message (list): The initial OpenAI `user` role message sent to the OpenAI API at the beginning of a session.
        session_messages (list): The collective list of messages sent to the OpenAI API during a game session. Each of the player's `user` role messages is appended to this list, as is each 'assistant' role message returned by the OpenAI API in response.
    """
    def __init__(self, adventure: Adventure):
        self.adventure = adventure
        self.system_message = system_message
        self.system_message[0]["content"] += adventure.introduction
        self.user_message = user_init_message
        self.session_messages = self.system_message + self.user_message

    def format_user_message(self, message_string: str) -> dict:
        """Format the given string as an OpenAI 'user' role message.

        This method returns a dict with a 'role' key's value set to 'user' and the
        given string as the 'content' key's value. The resultant dict is appropriate
        for sending to the OpenAI API as a user message.

        Example:

        The string returned by this method is in the following format and is
        appropriate for sending to the OpenAI API as a user message:

        .. code-block:: python

                {
                    "role": "user",
                    "content": "The string passed to this method."
                }

        Args:
            message_string (str): The string to format as an OpenAI user message. It must be a regular string and not a JSON string.

        Returns:
            dict: _description_
        """
        return {"role": "user", "content": str(message_string)}

    def start_session(self):
        """Start a gaming session with the dungeon master in the current adventure.

        If this the first session in the adventure, the adventure is marked as started and the
        dungeon master's (system) init message is sent to theOpenAI API as is player's (user) init message.
        If it's not the first session of the adventure, only the system and user init messages are sent.

        Returns:
            str: The response from the Dungeon Master (in this case, the OpenAI API) when initiating game session. This string is appropriate for display to the player.
        """

        if not self.adventure.is_started:
            self.adventure.start_adventure()

        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo", messages=self.session_messages
        )
        self.session_messages.append(completion.choices[0].message)
        self.started = True
        gm.logger.debug(completion)
        return completion.choices[0].message["content"]

    def player_message(self, message):
        if self.started:
            self.session_messages.append(message)
            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo", messages=self.session_messages
            )
            self.session_messages.append(completion.choices[0].message)
            gm.logger.debug(completion)
            return completion.choices[0].message["content"]

    def move_party(self, direction) -> str:
        new_location = self.adventure.active_dungeon.move(direction)
        message_from_player = self.format_user_message(user_move_prefix + new_location.json)
        return self.player_message(message_from_player)

"""The `dungeon_assistant` module contains the `DungeonAssistant` class that interfaces with the OpenAI API and performs the duties of the game's referee and guide (often called *game master* or *dungeon master* in tabletop RPGs)."""

import asyncio
from openai import OpenAI
from osrlib.adventure import Adventure
from osrlib.enums import OpenAIModelVersion
from osrlib.game_manager import logger

# v1 Too verbose, flowery
# dm_init_message = (
#     "As the Dungeon Master, you weave the narrative and guide players through their adventure, creating a rich, "
#     "immersive world. Your skill in storytelling brings to life the dungeons, landscapes, and encounters of the game. "
#     "In this session, you manage a party of six adventurers, describing their surroundings and the outcomes of their choices "
#     "with vivid detail. Each location in the game is unique, with its own ID and possible exits leading to new challenges. "
#     "Your descriptions are key to the player's experience, providing them with the information needed to navigate and interact "
#     "with the world. Remember, your role is to describe, not to direct. You bring the game world to life, setting the scene for "
#     "the player's decisions without asking questions or dictating actions. The journey starts now, and the first message from the "
#     "player is on its way. Respond only with 'Let's begin.' to kick off this adventure."
# )

# v2
dm_init_message = (
    "As the Dungeon Master, your task is to craft the narrative and guide the adventure with precision. You narrate the "
    "journey of six adventurers through a world filled with mystery and challenge. Your descriptions should be clear and "
    "concise, focusing on the essential details of dungeons, landscapes, and encounters. Each location in the game is "
    "distinct, identified by a unique ID, with exits leading to further adventures. Aim to provide descriptions that are "
    "direct and to the point, enabling the players to effectively navigate and interact with their surroundings. Your role "
    "is to illuminate the path ahead, not to influence the choices directly. Set the scene with enough detail to engage, "
    "but avoid overly decorative language that may distract. The adventure begins now. Await the first message from the "
    "players and respond with 'Let's begin.' to initiate this journey."
)



system_message = [
    {
        "role": "system",
        "content": dm_init_message,
    },
]

# Prefixes most player (user) messages sent to the OpenAI API.
user_message_prefix = "Don't tell me what my party does. Don't include any questions in your response. "

# The player's (user) init message is sent only once, at the beginning of the session.
user_init_message = [
    {
        "role": "user",
        "content": ( user_message_prefix +
            "I'm a D&D player controlling a party of six characters (adventurers) in your Dungeons & Dragons adventure. "
            "I rely on your descriptions of the entities, locations, and events in the game to understand what my characters "
            "experience through their five senses. From your descriptions, I can form a picture in my mind "
            "of the game world and its environments and inhabitants. I use this information to make decisions about the "
            "actions my characters take in the world. Do not ask me a question."
        ),
    }
]

# Prefix sent with every party movement message initiated by the player.
user_move_prefix = ( user_message_prefix +
    "Describe this location concisely. Include exit directions but not the size. Be brief - don't mention whether "
    "the exits are locked. Based on your description, the player must be able to imagine an accurate representation "
    "of the location in their mind. Don't be flowerey or overly dramatic - assume a more matter-of-fact tone. "
    "Maintain a theme based on the adventure description and the last room you described. Here's the location data: "
)

battle_summary_prompt = (
    "Briefly summarize the following battle in a single paragraph of four sentences or less. Include highlights of the battle, "
    "for example high damage rolls (include their values) and critical hits. Use a factual, report-like tone instead of "
    "being flowery and expressive. The last sentence should list any PCs killed and the collective XP earned by the party. "
    "Here's the battle log: "
)

class DungeonAssistant:
    """The `DungeonAssistant` is the primary interface between the player, the game engine, and the OpenAI API.

    Actions initiated by the player might be handled completely within the bounds of the local game engine,
    or they might involve a call to the OpenAI API. The `DungeonAssistant` class is responsible for determining
    which actions are handled locally and which are handled by the OpenAI API.

    Attributes:
        adventure (Adventure): The adventure the `DungeonAssistant` is running.
        session_messages (list): The collective list of messages sent to the OpenAI API during a game session. Each of the player's `user` role messages is appended to this list, as is each 'assistant' role message returned by the OpenAI API in response.
        is_started (bool): Indicates whether the game session has started. The game session starts upon first call to the `start_session()` method.
    """
    def __init__(self, adventure: Adventure = None, openai_model: OpenAIModelVersion = OpenAIModelVersion.DEFAULT):
        self.adventure = None
        self.system_message = None
        self.session_messages = []
        self.client = None
        self.openai_model = openai_model.value

        if adventure is not None:
            self.set_active_adventure(adventure)

    def set_active_adventure(self, adventure: Adventure = None) -> None:
        self.adventure = adventure
        self.system_message = system_message
        self.system_message[0]["content"] += adventure.introduction
        self.session_messages = system_message + user_init_message

    def format_user_message(self, message_string: str) -> dict:
        """Format the given string as an OpenAI 'user' role message.

        This method returns a dict with a 'role' key's value set to 'user' and the
        given string as the 'content' key's value. The resultant dict is appropriate
        for sending to the OpenAI API as a user message.

        Example:

        The string returned by this method is in the following format and is
        appropriate for sending to the OpenAI API as a user message:

        ```json
        {
            "role": "user",
            "content": "The string passed to this method."
        }
        ```

        Args:
            message_string (str): The string to format as an OpenAI user message. It must be a regular string and not a JSON string.

        Returns:
            dict: A version of the user message as a Python `dict`.
        """
        return {"role": "user", "content": str(message_string)}

    def start_session(self) -> str:
        """Start a gaming session with the dungeon master in the current adventure.

        If this the first session in the adventure, the adventure is marked as started and the
        dungeon master's (system) init message is sent to the OpenAI API as is player's (user) init message.
        If it's not the first session of the adventure, only the system and user init messages are sent.

        Returns:
            str: The response from the Dungeon Master (in this case, the OpenAI API) when initiating a game session. This string is appropriate for display to the player.

        Raises:
            ValueError: If there is no active adventure. Call set_active_adventure() with a valid adventure before calling start_session().
        """
        if self.adventure is None:
            raise ValueError("There is no active adventure. Call set_active_adventure() with a valid adventure before calling start_session().")

        try:
            self.client = OpenAI()
        except e:
            logger.critical(f"Error initializing OpenAI client: {e}")

        if not self.adventure.is_started:
            self.adventure.start_adventure()

        completion = self.client.chat.completions.create(
            model=self.openai_model,
            messages=self.session_messages
        )
        self.session_messages.append(completion.choices[0].message)
        self.is_started = True
        logger.debug(completion)

        return completion.choices[0].message.content

    def player_message(self, message):
        """Send a message from the player to the Dungeon Master and return the response."""
        if self.is_started:
            self.session_messages.append(message)
            completion = self.client.chat.completions.create(
                model=self.openai_model,
                messages=self.session_messages
            )
            self.session_messages.append(completion.choices[0].message)
            return completion.choices[0].message.content

    def move_party(self, direction) -> str:
        """Move the party in the given direction."""
        new_location = self.adventure.active_dungeon.move(direction)
        if new_location is None:
            return "No exit in that direction."
        message_from_player = self.format_user_message(user_move_prefix + new_location.json)
        dm_response = self.player_message(message_from_player)
        new_location.is_visited = True
        return dm_response

    def summarize_battle(self, battle_log) -> str:
        message_from_player = self.format_user_message(battle_summary_prompt + battle_log)
        return self.player_message(message_from_player)

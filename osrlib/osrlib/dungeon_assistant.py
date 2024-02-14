"""The `dungeon_assistant` module contains the `DungeonAssistant` class that interfaces with the OpenAI API and performs the duties of the game's referee and guide (*game master* or *dungeon master* in some tabletop RPGs)."""

from openai import OpenAI
from osrlib.adventure import Adventure
from osrlib.enums import OpenAIModelVersion
from osrlib.utils import logger


dm_init_message = (
    "As the Dungeon Assistant, your task is to narrate the journey of six adventurers through a fantasty game setting. "
    "Your descriptions of the locations, beings, and events in the game world should be clear and concise, focusing only "
    "only on the essential details. Each location in the game is distinct, having a unique ID and exits leading to other "
    "locations. Aim to provide descriptions that are direct and to the point, enabling the adventurers to effectively "
    "navigate and interact with their surroundings. Your role is to illuminate the path ahead, not influence their "
    "choices directly. Set the scene with enough detail to engage, but avoid overly decorative language that could "
    "distract. The adventure begins now. Await the first message from the player, then respond only with 'Let's begin.' "
    "to initiate this journey."
)


system_message = [
    {
        "role": "system",
        "content": dm_init_message,
    },
]

# The player's (user) init message is sent only once, at the beginning of the session.
user_init_message = [
    {
        "role": "user",
        "content": (
            "I'm the leader of small party of adventurers exploring a fantasy game setting in a turn-based RPG. "
            "I rely on your descriptions of the locations, beings, and events we encounter in the game world to inform "
            "my decisions as I lead the party in our adventures. Avoid asking me any questions, and other than "
            "describing actions that occurred in combat, avoid telling me what the party does - that's my job, not yours. "
        ),
    }
]

# Prefix sent with every party movement message initiated by the player.
user_move_prefix = (
    "Describe this location using precise, non-expressive terminology. Use three sentences for new locations that have "
    "no monsters, mentioning the exits and which are unexplored, but without saying whether any are locked. Use one "
    "sentence and omit the dimensions for previously visited locations and locations with monsters. "
    "Avoid mentioning the location ID in all cases. "
    "Here is the location information: "
)

battle_summary_prompt = (
    "Summarize this battle in four sentences. Include only the highlights: high and low rolls (especially critical hits), "
    "deaths, and the weapon or spell used in the attack. Refer to adventurers only by their first names. Be direct, "
    "assuming the tone of a military combat officer reporting to their superior. Include the total XP earned by my party "
    "if my party won the battle. Here's the battle log: "
)


class DungeonAssistant:
    """The `DungeonAssistant` is the primary interface between the player, the game world's rules engine, and optionally the OpenAI API.

    Actions initiated by the player might be handled completely within the bounds of the local game engine,
    or they might involve a call to the OpenAI API. The `DungeonAssistant` class is responsible for determining
    which actions are handled locally and which are handled by the OpenAI API.

    Attributes:
        adventure (Adventure): The adventure the `DungeonAssistant` is running.
        session_messages (list): The collective list of messages sent to the OpenAI API during a game session. Each of the player's `user` role messages is appended to this list, as is each 'assistant' role message returned by the OpenAI API in response.
        session_is_started (bool): Indicates whether the game session has started. The game session starts upon first call to the `start_session()` method.
    """

    def __init__(
        self,
        adventure: Adventure = None,
        openai_model: OpenAIModelVersion = OpenAIModelVersion.DEFAULT,
    ):
        self.adventure = None
        self.system_message = None
        self.session_messages = []
        self.client = None
        self.openai_model = openai_model
        self.session_is_started = False

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
        """Start a gaming session with the dungeon assistant in the current adventure.

        If this the first session in the adventure, the adventure is marked as started and the
        dungeon assistant's (system) init message is sent to the OpenAI API as is player's (user) init message.
        If it's not the first session of the adventure, only the system and user init messages are sent.

        Returns:
            str: The response from the Dungeon Assistant (in this case, the OpenAI API) when initiating a game session. This string is appropriate for display to the player.

        Raises:
            ValueError: If there is no active adventure. Call set_active_adventure() with a valid adventure before calling start_session().
        """
        if self.adventure is None:
            raise ValueError(
                "No active adventure set. Call set_active_adventure() with a valid adventure before calling start_session()."
            )

        try:
            self.client = OpenAI()
        except e:
            logger.critical(f"Error initializing OpenAI client: {e}")

        if not self.adventure.is_started:
            self.adventure.start_adventure()

        completion = self.client.chat.completions.create(
            model=self.openai_model.value, messages=self.session_messages
        )
        self.session_messages.append(completion.choices[0].message)
        self.is_started = True
        logger.debug(completion)

        return completion.choices[0].message.content

    def send_player_message(self, message):
        """Send a message from the player to the Dungeon Assistant and return the response."""
        if self.is_started:
            self.session_messages.append(message)
            completion = self.client.chat.completions.create(
                model=self.openai_model.value, messages=self.session_messages
            )
            self.session_messages.append(completion.choices[0].message)
            return completion.choices[0].message.content

    def move_party(self, direction) -> str:
        """Move the party in the given direction."""
        new_location = self.adventure.active_dungeon.move(direction)
        if new_location is None:
            return "No exit in that direction."
        message_from_player = self.format_user_message(
            user_move_prefix + new_location.json
        )
        dm_response = self.send_player_message(message_from_player)
        new_location.is_visited = True
        return dm_response.replace(".  ", ". ")

    def summarize_battle(self, battle_log) -> str:
        message_from_player = self.format_user_message(
            battle_summary_prompt + battle_log
        )
        dm_response = self.send_player_message(message_from_player)
        return dm_response.replace(".  ", ". ")

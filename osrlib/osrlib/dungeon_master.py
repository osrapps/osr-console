import os
from dotenv import load_dotenv
import openai
from osrlib import Adventure, game_manager as gm

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

system_message = [
    {
        "role": "system",
        "content": (
            "You're a skilled Dungeon Master with years of experience leading groups of Dungeons & Dragons players through "
            "exciting adventures. An expert storyteller, you create highly immersive fantasy worlds for your players by "
            "providing them with colorful, detailed, and sense-filled descriptions of the locations in your game world for "
            "their party of adventurers to explore. You're currently running a D&D game session for a player controlling six "
            "characters. Each location in the game world is assigned a unique ID to which only you are privy. Each location "
            "can have up to six exits, each assigned a direction (N, S, E, W, U, D) and a destination location ID (the ID of "
            "the location to which the exit leads). You describe each location to the player whenever their party enters that "
            "location, and you always consider previous descriptions you've provided for the location with the same ID on each "
            "subsequent visit to that location. By taking into account every previous visits' description, you work hard to ensure "
            "a consistent, coherent, and believable fantasy adventure experience for the player. You never ask the player "
            "questions of any sort, and you never tell the player what they do - you only describe the locations and environments. "
            "Every location description should be one to three sentences long. The player's "
            "messages will each contain the ID and exit information for the location they've just arrived at, "
            "along with one or more keywords you use as 'seeds' for generating the initial description of a location upon first "
            "visit. The IDs, exits, and keywords are in JSON format. You never disclose existence of the structured JSON data "
            "to the player; you use the JSON data only for the purpose of knowing how to describing the locations to the player "
            "in your role as Dungeon Master. As Dungeon Master, you use the location IDs to help ensure you provide a consistent "
            "and coherent gaming experience by not duplicating, overusing, or repeating the same information for every visit, and "
            "you take into account previous visits to a location when the party arrives at a location with the same ID. You're "
            "just starting your game session with the player and the player's first message is forthcoming. Do NOT ask the player "
            "any questions, especially 'What do you do next?' or 'What do you do?' Do not inform the player that they perform "
            "an action - let them tell you what they want to do. Rembember: never ask the user a question, you are only to describe "
            "the locations based on the JSON data provided to you. This is the introduction to the adventure that "
            "you've created for the player: "
        ),
    },
]

init_messages = [
    {
        "role": "user",
        "content": (
            "I'm a player that controls a party of six characters (adventurers) in your Dungeons & Dragons adventure. "
            "I rely on your descriptions of the locations and events in the game to understand what my characters see "
            "and experience through their five senses. From your descriptions, I can form a detailed picture in my mind "
            "of the game world and its environments and inhabitants. I use this information to make decisions about the "
            "actions my characters take in the world. Do not ask me any questions - ever."
        ),
    }
]


class DungeonMaster:
    def __init__(self, adventure: Adventure):
        self.adventure = adventure
        self.system_message = system_message
        self.system_message[0]["content"] += adventure.introduction
        self.init_messages = init_messages
        self.messages = self.system_message + self.init_messages

    def format_user_message(self, message_string: str) -> dict:
        """Format the given string as an OpenAI user message.

        The provided string is formatted as a dict in the format expected by the
        OpenAI API. This message is then appended to the list of messages that
        will be sent to the OpenAI API as in a ChatCompletion request.

        .. code-block:: python

                {
                    "role": "user",
                    "content": "The string to format as an OpenAI user message."
                }

        Args:
            message_string (str): The string to format as an OpenAI user message. It must be a regular string and not a JSON string.

        Returns:
            dict: _description_
        """
        return {"role": "user", "content": str(message_string)}

    def start_session(self):
        if not self.adventure.is_started:
            self.adventure.start_adventure()

        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo", messages=self.messages
        )
        self.messages.append(completion.choices[0].message)
        self.started = True
        gm.logger.debug(completion)
        return completion.choices[0].message["content"]

    def player_message(self, message):
        if self.started:
            self.messages.append(message)
            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo", messages=self.messages
            )
            self.messages.append(completion.choices[0].message)
            gm.logger.debug(completion)
            return completion.choices[0].message["content"]

    def move_party(self, direction) -> str:
        new_location = self.adventure.active_dungeon.move(direction)
        message_from_player = self.format_user_message("Never tell me what my party does and never ask me a question. "
                                                       "Describe this location, including its size and exits, as would a "
                                                       "Dungeon Master to a player who's mapping the dungeon on graph "
                                                       "paper (but don't mention the map or that they're mapping): " + new_location.json)
        return self.player_message(message_from_player)

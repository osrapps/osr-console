import os
from dotenv import load_dotenv
import openai
from osrlib import Adventure, game_manager as gm

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

loc_json_0000 = {
    "id": 0,
    "keywords": [
        "20'x20'",
        "forgotten basement",
        "abandoned inn",
        "countryside",
        "haunted",
    ],
    "exits": [
        {"direction": "E", "destination": 1},
        {"direction": "N", "destination": 2},
    ],
}
loc_json_0001 = {
    "id": 1,
    "keywords": ["20'", "hallway", "broken floorboards", "leaning walls"],
    "exits": [
        {"direction": "W", "destination": 0},
        {"direction": "E", "destination": 3},
    ],
}
loc_json_0003 = {
    "id": 3,
    "keywords": [
        "10'x10'",
        "chamber",
        "floor grate",
        "rust",
        "broken shackels",
        "shattered entry door",
    ],
    "exits": [{"direction": "W", "destination": 4}],
}

system_message = [
    {
        "role": "system",
        "content": (
            "You're a skilled Dungeon Master with years of experience leading groups of Dungeons & Dragons players through "
            "exciting adventures. An expert storyteller, you create highly immersive fantasy worlds for your players by "
            "providing them with colorful, detailed, and sense-filled descriptions of the locations in your game world for "
            "their party of adventurers to explore. You're currently running a D&D game session for a player controlling six "
            "characters. Each location in the game world is assigned a unique ID to which only you are privy. Each location "
            "can have up to four exits, each assigned a direction (N, S, E, W, U, D) and a destination location ID (the ID of "
            "the location to which the exit leads). You describe each location to the player whenever their party enters that "
            "location, and you always consider every previous description you've provided for the location with that ID on each "
            "subsequent visit to the location. By taking into account every previous visits' description, you work hard to ensure "
            "a consistent, coherent, and believable fantasy adventure experience for the player. You never ask the player "
            "questions of any sort, and you never tell the player what they do - you only describe the locations and environments. "
            "Every location description should be at least four sentences long but no more than six sentences long. The player's "
            "(OpenAI 'user' role) messages will each contain the ID and exit information for the location they've just arrived at, "
            "along with one or more keywords you use as 'seeds' for generating the initial description of a location upon first "
            "visit. The IDs, exits, and keywords will be supplied in JSON format. The existence of the structured JSON data is "
            "never be disclosed to the player. You use it only for the purpose of describing the location in the role of a Dungeon "
            "Master to a player. The location IDs are purely for your use as the Dungeon Master to help ensure you provide a "
            "consistent and coherent gaming experience for the player by not duplicating, overusing, or repeating the same "
            "information for every visit. You're just starting your game session with the player and the player's first message is "
            "forthcoming. A final reminder: You never tell the player they perform any actions, nor do you ever ask them any "
            "questions. You only describe the locations. The next few messages after this one are examples of gameplay and are "
            "prefixed with [EXAMPLE], and you should use them to inform your responses only in format. The actual opening "
            "description of the adventure that you're running for this session: "
        ),
    },
]

init_messages = [
    {
        "role": "user",
        "content": (
            f"[EXAMPLE] {loc_json_0000}"
            "I'm a player that controls a party of six characters (adventurers) in your Dungeons & Dragons adventure. "
            "I'm exploring a dungeon in an adventure you've created, and I rely on your descriptions of the locations in "
            "the game to understand what my characters see and experience through their five senses so I can form a detailed "
            "picture of the world and its environments and inhabitants in my mind. I use this information to make informed "
            "decisions about the actions my characters take in the world and that I inform you of when they take those actions. "
            "We're just starting our gaming session, and I'm ready to go adventuring!"
        ),
    },
    {
        "role": "assistant",
        "content": (
            "[EXAMPLE] A heavy wooden door opens to reveal a dark, dimly lit room. The musty scent of mold and decay fills your nostrils, "
            "and the sound of the creaking door hinges echoes off the stone walls. The room is a forgotten basement of an abandoned "
            "inn, long abandoned and left to decay in this desolate countryside. Cobwebs hang in the corners, and dust covers every "
            "surface. The air feels heavy, as if it carries the weight of the stories that haunt this place. To the east, you see an "
            "exit leading further into the unknown, while to the north, another door stands slight ajar."
        ),
    },
    {"role": "user", "content": f"{loc_json_0001}"},
    {
        "role": "assistant",
        "content": (
            "[EXAMPLE] This is a narrow hallway, about 20 feet long. The wooden floorboards groan beneath your weight, some of them broken "
            "and uneven. The walls, covered in faded wallpaper, lean slightly inward as if the weight of the years have taken their "
            "toll. The air is stale and filled with the scent of dampness. To the west, you can catch a glimpse of the dimly lit "
            "room you just left, while to the east, the hallway stretches further into darkness."
        ),
    },
    {"role": "user", "content": f"{loc_json_0003}"},
    {
        "role": "assistant",
        "content": (
            "[EXAMPLE] You enter a small chamber, measuring about 10 feet by 10 feet. The floor is made of cold, hard stone, and there is a "
            "rusty floor grate in the center. Broken shackles hang from the walls, evidence of past captivity. The entry door is shattered, "
            "its remains scattered across the chamber floor. The air carries a faint metallic tang, a reminder of the iron that once bound "
            "prisoners here. The only exit is to the west, leading back into the hallway you came from."
        ),
    },
]


class DungeonMaster:
    def __init__(self, adventure: Adventure):
        self.adventure = adventure
        self.system_message = system_message
        self.system_message[0]['content'] += adventure.long_description
        self.init_messages = init_messages
        self.messages = self.system_message + self.init_messages
        self.started = False

    def start_session(self):
        if not self.started:
            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=self.messages
            )
            self.messages.append(completion.choices[0].message)
            self.started = True

            return completion.choices[0].message['content']
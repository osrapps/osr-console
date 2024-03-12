import json
import os

import questionary
from questionary import Separator

from osrlib.player_character import PlayerCharacter
from osrlib.enums import CharacterClassType
from osrlib.party import Party


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


back = "Back"
exit_app = "Exit"
nav_instruction = "📜"
nav_instruction_arrow_keys = "(use arrow keys)"
separator_top = "==--==--==--==--=="
separator_bottom = "------------------"

icon_arrow_left = "⬅️"
icon_arrow_right = "➡️"
icon_bubble = "💬"
icon_cloud = "☁️"
icon_crown = "👑"
icon_dash = "➖"
icon_diamon_blue = "🔹"
icon_diamond_orange = "🔸"
icon_die = "🎲"
icon_earth = "🌍"
icon_finger = "👉"
icon_fire = "🔥"
icon_flag = "🚩"
icon_gear = "⚙️"
icon_gem = "💎"
icon_heart = "❤️"
icon_key = "🔑"
icon_lightning = "⚡"
icon_lock = "🔒"
icon_map = "🗺️"
icon_moon = "🌙"
icon_questionmark = "❓"
icon_rain = "🌧️"
icon_scroll = "📜"
icon_select = "➤"
icon_shield = "🛡️"
icon_skull = "💀"
icon_snowflake = "❄️"
icon_star = "⭐"
icon_star = "⭐"
icon_sun = "☀️"
icon_sword = "⚔️"
icon_treasure = "💰"
icon_water = "💧"
icon_wind = "💨"


class MainMenu:
    def show(self):
        while True:
            choice = questionary.select(
                "Welcome to OSR CLI",
                qmark=icon_scroll,
                pointer=icon_select,
                instruction=nav_instruction,
                choices=[
                    Separator(separator_top),
                    "Create character",
                    "Create party",
                    "Create adventure",
                    "Play adventure",
                    "Settings",
                    Separator(separator_bottom),
                    exit_app,
                ],
            ).ask()
            if choice == "Create character":
                character_menu = CreateCharacterMenu()
                character_menu.show()
            elif choice == exit_app:
                break


class CreateCharacterMenu:
    def show(self):
        while True:
            character_name = questionary.text("Character name:", qmark=icon_dash).ask()

            class_choice = questionary.select(
                "Character class:",
                qmark=icon_dash,
                pointer=icon_select,
                instruction=nav_instruction_arrow_keys,
                choices=[
                    Separator(separator_top),
                    *[c.value for c in CharacterClassType],
                    Separator(separator_bottom),
                    back,
                ],
            ).ask()

            if class_choice != back:
                character_class = CharacterClassType(class_choice)
                character = PlayerCharacter(character_name, character_class)
                print(character)

                while True:
                    reroll_choice = questionary.confirm(
                        "Reroll abilities [Y/n]",
                        qmark=icon_dash,
                        instruction=icon_questionmark,
                        default=True,
                    ).ask()

                    if reroll_choice:
                        character.roll_abilities()
                    else:
                        break

                save_character = questionary.confirm(
                    "Save character [Y/n]",
                    qmark=icon_dash,
                    instruction=icon_questionmark,
                    default=True,
                ).ask()
                if save_character:
                    save_file = questionary.text("File name:", qmark=icon_dash, default=character.name + ".json").ask()
                    save_dir = questionary.path("Directory:", qmark=icon_dash).ask()

                    # Expand the tilde to the user's home directory path if present
                    save_dir = os.path.expanduser(save_dir)

                    # Check if the directory exists and create it if necessary
                    full_path = os.path.join(save_dir, save_file)
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)

                    with open(full_path, "w") as f:
                        f.write(json.dumps(character.to_dict(), indent=4))

                    questionary.print("Character saved to " + full_path)
                    break
            else:
                break


def main() -> int:
    main_menu = MainMenu()
    clear_screen()
    main_menu.show()
    return 0

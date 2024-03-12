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

pointer_finger = "👉"
pointer_die = "🎲"
pointer_arrow = "➡️"
pointer_bracket = "🔹"
pointer_diamond = "🔸"

pointer_select = "➤"
pointer_arrow_large = "➜"
pointer_arrow_left_1 = "⬅️"

qmark_menu = "📜"
qmark_submenu = "➖"
qmark_question = "❓"

qmark_bubble = "💬"
qmark_sword = "⚔️"
qmark_shield = "🛡️"
qmark_treasure = "💰"
qmark_map = "🗺️"
qmark_flag = "🚩"
qmark_gear = "⚙️"
qmark_star = "⭐"
qmark_heart = "❤️"
qmark_skull = "💀"
qmark_crown = "👑"
qmark_gem = "💎"
qmark_key = "🔑"
qmark_lock = "🔒"
qmark_lightning = "⚡"
qmark_fire = "🔥"
qmark_ice = "❄️"
qmark_water = "💧"
qmark_wind = "💨"
qmark_earth = "🌍"
qmark_sun = "☀️"
qmark_moon = "🌙"
qmark_star = "⭐"
qmark_cloud = "☁️"
qmark_rain = "🌧️"


class MainMenu:
    def show(self):
        while True:
            choice = questionary.select(
                "Welcome to OSR CLI!",
                qmark=qmark_menu,
                pointer=pointer_select,
                instruction=nav_instruction,
                choices=[
                    Separator(),
                    "Create character",
                    "Create party",
                    "Create adventure",
                    "Play adventure",
                    "Settings",
                    Separator(),
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
            character_name = questionary.text("Character name:", qmark=qmark_submenu).ask()

            class_choice = questionary.select(
                "Select a class",
                qmark=qmark_submenu,
                pointer=pointer_select,
                choices=[
                    Separator(),
                    *[c.value for c in CharacterClassType],
                    Separator(),
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
                        qmark=qmark_submenu,
                        instruction=qmark_question,
                        default=True,
                    ).ask()

                    if reroll_choice:
                        character.roll_abilities()
                    else:
                        break
                break
            else:
                break


def main() -> int:
    main_menu = MainMenu()
    clear_screen()
    main_menu.show()
    return 0

from textual.app import App, ComposeResult
from textual.containers import Grid, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Input, RadioSet, Static, Placeholder
from textual import on
from widgets import CharacterClassRadioButtons
from osrlib.enums import CharacterClassType

class NewCharacterModalScreen(ModalScreen):
    """A modal screen for creating a new character."""

    CSS_PATH = "screen.tcss"

    def compose(self) -> ComposeResult:
        yield Grid(
            Static("Create New Character", id="title"),
            Input(id="character_name", placeholder="Enter character name"),
            CharacterClassRadioButtons(),
            Horizontal(
                Button("Create", id="btn_char_create", variant="primary", classes="button"),
                Button("Cancel", id="btn_char_cancel", variant="default", classes="button"),
                classes="char_create_buttons",
            ),
            id="new_character_grid",
        )

    def on_mount(self) -> None:
        self.set_focus(self.query_one("#character_name"))

    @on(Button.Pressed, "#btn_char_cancel")
    def cancel_button_pressed(self) -> None:
        self.app.pop_screen()

    @on(Button.Pressed, "#btn_char_create")
    def create_button_pressed(self) -> None:
        character_name = self.query_one("#character_name").value
        character_class_value = self.query_one(RadioSet).pressed_button.label.plain
        character_class = CharacterClassType[character_class_value.upper()]
        # Implement the character creation logic here
        self.app.pop_screen()

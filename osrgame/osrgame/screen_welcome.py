from textual import on
from textual.screen import Screen
from textual.app import ComposeResult
from textual.widgets import Header, Footer, Button
from widgets import WelcomeScreenButtons


class WelcomeScreen(Screen):

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True, id="header")
        yield WelcomeScreenButtons(id="welcome-buttons")
        yield Footer()
    def on_mount(self) -> None:
        pass

    ### Buttons ###

    @on(Button.Pressed, "#btn-adventure-default")
    def default_button_pressed(self) -> None:
        self.action_start_default_adventure()

    @on(Button.Pressed, "#btn-adventure-load")
    def load_button_pressed(self) -> None:
        self.action_load_adventure()

    @on(Button.Pressed, "#btn-adventure-create")
    def create_button_pressed(self) -> None:
        ## TODO: self.action_create_adventure()
        pass

    @on(Button.Pressed, "#btn-quit")
    def quit_button_pressed(self) -> None:
        self.action_quit()

    ### Actions ###

    def action_start_default_adventure(self) -> None:
        """Start the default adventure, which is an adventure with one randomly generated dungeon."""
        self.app.set_active_adventure(adventure=None)
        dm_response = self.app.start_session() # TODO: dm_response should be a textual reactive property
        self.app.push_screen("screen_explore")

    def action_load_adventure(self) -> None:
        """Show the adventure browser screen."""
        self.app.push_screen("screen_adventure_browser")

    def action_create_adventure(self) -> None:
        """Show the adventure creator screen."""
        self.app.push_screen("screen_adventure_creator")

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()

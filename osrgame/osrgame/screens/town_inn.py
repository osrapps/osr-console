"""Inn screen — save game and rest the party."""

import datetime
import json

from textual import on
from textual.app import ComposeResult
from textual.containers import Center, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Static

from ..game_state import get_save_dir


class InnScreen(Screen):
    """Inn: save the game and rest the party."""

    BINDINGS = [
        ("escape", "done", "Done"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Center():
            with Vertical(id="inn-container"):
                yield Static("Inn", id="town-title", classes="gold-heading")
                yield Static(
                    "The innkeeper greets you warmly.\n"
                    '"Rest your weary bones, or save your progress for another day."',
                    id="inn-description",
                )
                yield Button("Save game", id="btn-save", variant="primary")
                yield Button("Rest", id="btn-rest")
                yield Button("Done", id="btn-inn-done")
        yield Footer()

    @on(Button.Pressed, "#btn-save")
    def save_game(self) -> None:
        gs = self.app.game_state
        if gs.adventure is None:
            self.notify("No adventure to save.", severity="error", title="Inn")
            return

        save_data = gs.to_dict()
        now = datetime.datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        adventure_name = gs.adventure.name.replace(" ", "_").lower()
        filename = f"{adventure_name}_{timestamp}.json"
        save_path = get_save_dir() / filename

        try:
            with open(save_path, "w") as f:
                json.dump(save_data, f, indent=2)
            self.notify(f"Game saved to {save_path.name}", title="Inn")
        except OSError as e:
            self.notify(f"Save failed: {e}", severity="error", title="Inn")

    @on(Button.Pressed, "#btn-rest")
    def rest_party(self) -> None:
        gs = self.app.game_state
        if gs.adventure is None or gs.adventure.active_party is None:
            self.notify("No party to rest.", severity="error", title="Inn")
            return
        gs.adventure.active_party.heal_party()
        self.notify("The party rested and healed.", title="Inn")

    @on(Button.Pressed, "#btn-inn-done")
    def done(self) -> None:
        self.action_done()

    def action_done(self) -> None:
        self.dismiss()

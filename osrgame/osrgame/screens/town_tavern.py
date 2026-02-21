"""Tavern screen — hear rumors (stub)."""

from textual import on
from textual.app import ComposeResult
from textual.containers import Center, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Log, Static


TAVERN_RUMORS = [
    "The barkeep leans in and whispers...",
    '"I heard there\'s a hidden room on the second level of the dungeon."',
    '"They say the goblins have been hoarding gems in the eastern tunnels."',
    '"A cleric passed through last week — said the dead walk in the lower levels."',
    '"Watch out for the pit traps. Many an adventurer has met their end that way."',
]


class TavernScreen(Screen):
    """Tavern: hear rumors about the dungeon."""

    BINDINGS = [
        ("escape", "done", "Done"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Center():
            with Vertical(id="tavern-container"):
                yield Static("Tavern", id="town-title", classes="gold-heading")
                yield Log(id="tavern-log", auto_scroll=True)
                yield Button("Leave", id="btn-leave")
        yield Footer()

    def on_mount(self) -> None:
        log = self.query_one("#tavern-log", Log)
        for rumor in TAVERN_RUMORS:
            log.write_line(rumor)

    @on(Button.Pressed, "#btn-leave")
    def leave(self) -> None:
        self.action_done()

    def action_done(self) -> None:
        self.dismiss()

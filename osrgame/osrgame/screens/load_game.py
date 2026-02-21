"""Load game screen — browse and restore saved games."""

import json
from datetime import datetime, timezone
from pathlib import Path

from textual import on
from textual.app import ComposeResult
from textual.containers import Center, Vertical
from textual.screen import Screen
from textual.widgets import Button, DataTable, Footer, Header, Static

from ..game_state import GameState, get_save_dir


class LoadGameScreen(Screen):
    """Browse saved games and load one."""

    BINDINGS = [
        ("escape", "back", "Back"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Center():
            with Vertical(id="load-container"):
                yield Static("Load game", id="town-title", classes="gold-heading")
                yield DataTable(id="load-table", cursor_type="row")
                yield Button("Back", id="btn-load-back")
        yield Footer()

    def on_mount(self) -> None:
        self._save_files: list[Path] = []
        table = self.query_one("#load-table", DataTable)
        table.add_columns("Save file", "Date")
        self._scan_saves()

    def _scan_saves(self) -> None:
        table = self.query_one("#load-table", DataTable)
        table.clear()
        self._save_files = []
        save_dir = get_save_dir()
        if not save_dir.exists():
            return
        files = sorted(save_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        for f in files:
            self._save_files.append(f)
            mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc).astimezone()
            table.add_row(f.stem, mtime.strftime("%Y-%m-%d %H:%M"))

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        event.stop()
        if event.cursor_row >= len(self._save_files):
            return
        save_path = self._save_files[event.cursor_row]
        try:
            with open(save_path) as f:
                data = json.load(f)
            gs = GameState.from_dict(data)
            self.app.game_state = gs
            self.notify(f"Loaded {save_path.stem}", title="Load game")
            # Replace this screen with town hub (pop LoadGame, push TownHub)
            self.app.pop_screen()
            from .town_hub import TownHubScreen

            self.app.push_screen(TownHubScreen())
        except Exception as e:
            self.notify(f"Load failed: {e}", severity="error", title="Load game")

    @on(Button.Pressed, "#btn-load-back")
    def back(self) -> None:
        self.action_back()

    def action_back(self) -> None:
        self.app.pop_screen()

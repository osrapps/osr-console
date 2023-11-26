import os

from rich.syntax import Syntax
from rich.traceback import Traceback

from textual.app import ComposeResult
from textual.containers import Container, VerticalScroll
from textual.screen import Screen
from textual.widgets import DirectoryTree, Footer, Header, Static

from osrlib.adventure import Adventure

from widgets import JsonFilteredDirectoryTree

class AdventureBrowserScreen(Screen):
    """File browser for selecting an adventure to load."""

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("l", "load_adventure", "Load adventure"),
    ]

    adventure_file_path = None

    def compose(self) -> ComposeResult:
        """Compose our UI."""
        # Set the path to the current user's home directory.
        path = os.path.expanduser("~") + "/"
        yield Header()
        with Container():
            yield JsonFilteredDirectoryTree(path, id="tree-view")
        with VerticalScroll(id="code-view"):
            yield Static(id="code", expand=True)
        yield Footer()

    def on_mount(self) -> None:
        self.query_one(JsonFilteredDirectoryTree).focus()

    def on_directory_tree_file_selected(
        self, event: JsonFilteredDirectoryTree.FileSelected
    ) -> None:
        """Called when the user selects a file in the directory tree."""
        event.stop()
        code_view = self.query_one("#code", Static)
        try:
            syntax = Syntax.from_path(
                str(event.path),
                line_numbers=True,
                word_wrap=False,
                indent_guides=True,
                theme="github-dark",
            )
        except Exception:
            code_view.update(Traceback(theme="github-dark", width=None))
            self.sub_title = "ERROR"
        else:
            code_view.update(syntax)
            self.query_one("#code-view").scroll_home(animate=False)
            self.sub_title = str(event.path)
            self.adventure_file_path = str(event.path)

    def action_load_adventure(self) -> None:
        """An action to load an adventure."""

        # Ensure the path we're passing to Adventure.load_adventure() is valid.
        if self.adventure_file_path is None or not os.path.exists(self.adventure_file_path):
            return

        # Load the adventure and set it as the active adventure.
        try:
            loaded_adventure = Adventure.load_adventure(self.adventure_file_path)
            self.app.set_active_adventure(loaded_adventure)
            self.app.get_screen("scr_explore").start_session()
            self.app.pop_screen()
            self.app.push_screen("scr_explore")
        except Exception:
            # Get the traceback and display it in the code view.
            code_view = self.query_one("#code", Static)
            code_view.update(Traceback(theme="github-dark", width=None))

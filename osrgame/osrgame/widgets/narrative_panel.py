"""Scrollable narrative log with optional loading indicator."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import LoadingIndicator, RichLog


class NarrativePanel(Vertical):
    """RichLog with a LoadingIndicator overlay for AI generation."""

    DEFAULT_CSS = """
    NarrativePanel {
        height: 100%;
    }

    NarrativePanel RichLog {
        height: 1fr;
    }

    NarrativePanel LoadingIndicator {
        height: 3;
    }
    """

    def compose(self) -> ComposeResult:
        yield RichLog(id="narrative-log", auto_scroll=True, wrap=True)
        yield LoadingIndicator(id="narrative-loading")

    def on_mount(self) -> None:
        self.query_one("#narrative-loading", LoadingIndicator).display = False

    def write(self, text: str) -> None:
        """Append text to the narrative log."""
        self.query_one("#narrative-log", RichLog).write(text)

    def show_loading(self) -> None:
        """Show the loading indicator (for AI-generated content)."""
        self.query_one("#narrative-loading", LoadingIndicator).display = True

    def hide_loading(self) -> None:
        """Hide the loading indicator."""
        self.query_one("#narrative-loading", LoadingIndicator).display = False

    def clear(self) -> None:
        """Clear the narrative log."""
        self.query_one("#narrative-log", RichLog).clear()

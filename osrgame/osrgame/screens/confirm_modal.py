"""Reusable confirmation modal dialog."""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Static


class ConfirmModal(ModalScreen[bool]):
    """Modal confirmation dialog with Yes/No buttons.

    Push with a callback to get the result:

        self.app.push_screen(ConfirmModal("Delete?", title="Confirm"), callback=handler)
    """

    DEFAULT_CSS = """
    ConfirmModal {
        align: center middle;
    }

    #confirm-dialog {
        width: 50;
        height: auto;
        padding: 1 2;
        border: solid #4a4a8a;
        background: #0e0e3a;
    }

    #confirm-title {
        text-align: center;
        color: #ffd700;
        text-style: bold;
        margin-bottom: 1;
    }

    #confirm-message {
        color: #c0c0c0;
        margin-bottom: 1;
    }

    #confirm-buttons {
        align: center middle;
        height: auto;
    }

    #confirm-buttons Button {
        margin: 0 2;
        min-width: 12;
    }
    """

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    def __init__(self, message: str, title: str = "Confirm", **kwargs) -> None:
        super().__init__(**kwargs)
        self._message = message
        self._title = title

    def compose(self) -> ComposeResult:
        with Vertical(id="confirm-dialog"):
            yield Static(self._title, id="confirm-title")
            yield Static(self._message, id="confirm-message")
            with Horizontal(id="confirm-buttons"):
                yield Button("No", id="btn-confirm-no", variant="primary")
                yield Button("Yes", id="btn-confirm-yes", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-confirm-yes":
            self.dismiss(True)
        else:
            self.dismiss(False)

    def action_cancel(self) -> None:
        self.dismiss(False)

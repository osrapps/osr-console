"""Ability scores + modifiers DataTable widget."""

from rich.text import Text
from textual.widgets import DataTable

from osrlib.enums import AbilityType
from osrlib.utils import format_modifiers


class AbilityTableWidget(DataTable):
    """DataTable showing ability scores and their modifiers."""

    DEFAULT_CSS = """
    AbilityTableWidget {
        height: auto;
        max-height: 12;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(cursor_type=None, **kwargs)

    def on_mount(self) -> None:
        self.add_columns("Ability", "Score", "Modifiers")

    def update_from_abilities(self, abilities: dict[AbilityType, object]) -> None:
        """Rebuild rows from an abilities dict (AbilityType -> Ability instance)."""
        self.clear()
        for ability_type, ability in abilities.items():
            self.add_row(
                ability_type.value,
                Text(str(ability.score), justify="center"),
                format_modifiers(ability.modifiers),
                key=ability_type.name,
            )

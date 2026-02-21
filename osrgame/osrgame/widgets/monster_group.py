"""Grouped monster display for the combat screen."""

from rich.text import Text
from textual.widgets import DataTable

from osrlib.combat.context import CombatSide
from osrlib.combat.views import CombatView, CombatantView


class MonsterGroupWidget(DataTable):
    """DataTable showing monsters grouped by name with count and total HP."""

    DEFAULT_CSS = """
    MonsterGroupWidget {
        height: 100%;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(cursor_type=None, **kwargs)

    def on_mount(self) -> None:
        self.add_columns("Monster", "#", "HP")

    def refresh_from_view(self, view: CombatView) -> None:
        """Rebuild rows from a combat view, grouping monsters by name."""
        self.clear()

        # Group monsters by name
        groups: dict[str, list[CombatantView]] = {}
        for c in view.combatants:
            if c.side != CombatSide.MONSTER:
                continue
            groups.setdefault(c.name, []).append(c)

        for name, members in groups.items():
            living = [m for m in members if m.is_alive and not m.has_fled]
            dead_count = sum(1 for m in members if not m.is_alive)
            fled_count = sum(1 for m in members if m.has_fled)

            if not living and dead_count == len(members):
                # All dead — show dimmed
                count_text = Text(str(len(members)), justify="center", style="dim")
                hp_text = Text("dead", justify="center", style="dim red")
                name_text = Text(name, style="dim")
            elif not living and fled_count > 0:
                count_text = Text(str(len(members)), justify="center", style="dim")
                hp_text = Text("fled", justify="center", style="dim yellow")
                name_text = Text(name, style="dim")
            else:
                total_hp = sum(m.hp for m in living)
                count_text = Text(str(len(living)), justify="center")
                hp_text = Text(str(total_hp), justify="center")
                suffix_parts = []
                if dead_count:
                    suffix_parts.append(f"{dead_count} dead")
                if fled_count:
                    suffix_parts.append(f"{fled_count} fled")
                if suffix_parts:
                    name_text = Text(f"{name} ({', '.join(suffix_parts)})")
                else:
                    name_text = Text(name)

            self.add_row(name_text, count_text, hp_text, key=name)

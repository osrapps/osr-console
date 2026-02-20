"""Level-up display screen showing before/after stats."""

from textual import on
from textual.app import ComposeResult
from textual.containers import Center, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Static

from osrlib.enums import AbilityType, ModifierType
from osrlib.player_character import PlayerCharacter


class LevelUpScreen(Screen):
    """Show before/after stats for a level-up, then apply it."""

    BINDINGS = [
        ("escape", "done", "Done"),
    ]

    def __init__(self, pc: PlayerCharacter, **kwargs) -> None:
        super().__init__(**kwargs)
        self.pc = pc
        self._old_level = pc.level
        self._old_hp = pc.max_hit_points
        self._old_thac0 = pc.character_class.current_level.thac0

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Center():
            with Vertical(id="level-up-container"):
                yield Static("Level up!", id="level-up-title", classes="gold-heading")
                yield Static("", id="level-up-info")
                yield Button("Apply level up", id="btn-apply", variant="primary")
                yield Button("Done", id="btn-done")
        yield Footer()

    def on_mount(self) -> None:
        # Apply the level up
        hp_mod = self.pc.abilities[AbilityType.CONSTITUTION].modifiers.get(
            ModifierType.HP, 0
        )
        leveled = self.pc.character_class.level_up(hp_mod)
        if not leveled:
            self.query_one("#level-up-info", Static).update(
                f"{self.pc.name} does not have enough XP to level up."
            )
            self.query_one("#btn-apply", Button).display = False
            return

        new_level = self.pc.level
        new_hp = self.pc.max_hit_points
        new_thac0 = self.pc.character_class.current_level.thac0
        title = self.pc.character_class.current_level.title

        info_text = (
            f"{self.pc.name} — {self.pc.character_class.class_type.value}\n\n"
            f"Level: {self._old_level} → {new_level} ({title})\n"
            f"HP: {self._old_hp} → {new_hp}\n"
            f"THAC0: {self._old_thac0} → {new_thac0}\n"
        )

        # Check spell slots
        spell_slots = self.pc.character_class.current_level.spell_slots
        if spell_slots:
            slots_str = ", ".join(f"Lv{lvl}: {count}" for lvl, count in spell_slots)
            info_text += f"Spell slots: {slots_str}\n"

        self.query_one("#level-up-info", Static).update(info_text)
        self.query_one("#btn-apply", Button).display = False  # Already applied

    @on(Button.Pressed, "#btn-done")
    def done(self) -> None:
        self.action_done()

    @on(Button.Pressed, "#btn-apply")
    def apply(self) -> None:
        self.action_done()

    def action_done(self) -> None:
        self.dismiss(True)

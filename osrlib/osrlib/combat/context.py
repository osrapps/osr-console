"""Combat context: combatant references and mutable state bag for the engine."""

from collections import deque
from dataclasses import dataclass, field
from enum import Enum, auto

from osrlib.combat.conditions import ConditionTracker
from osrlib.combat.intents import ActionIntent
from osrlib.combat.modifiers import ModifierTracker
from osrlib.monster import Monster, MonsterParty
from osrlib.party import Party
from osrlib.player_character import PlayerCharacter


class CombatSide(Enum):
    """Which side of the encounter a combatant belongs to."""

    PC = auto()
    MONSTER = auto()


@dataclass
class MoraleState:
    """Tracks B/X morale-check state for the monster group."""

    initial_monster_count: int = 0
    first_death_checked: bool = False
    half_incapacitated_checked: bool = False
    checks_passed: int = 0
    is_immune: bool = False  # True after 2 passes or morale == 12


@dataclass
class CombatantRef:
    """Uniform handle wrapping either a PC or a Monster."""

    id: str
    side: CombatSide
    entity: PlayerCharacter | Monster
    has_fled: bool = False

    @property
    def is_alive(self) -> bool:
        return self.entity.is_alive

    @property
    def armor_class(self) -> int:
        return self.entity.armor_class

    @property
    def name(self) -> str:
        return self.entity.name


@dataclass
class CombatContext:
    """Mutable state bag carried through the combat engine's lifecycle."""

    combatants: dict[str, CombatantRef] = field(default_factory=dict)
    turn_queue: deque[str] = field(default_factory=deque)
    current_combatant_id: str | None = None
    round_number: int = 0
    announced_deaths: set[str] = field(default_factory=set)
    forced_intents: dict[str, ActionIntent] = field(default_factory=dict)
    pc_party: Party | None = None
    monster_party: MonsterParty | None = None
    morale: MoraleState = field(default_factory=MoraleState)
    conditions: ConditionTracker = field(default_factory=ConditionTracker)
    modifiers: ModifierTracker = field(default_factory=ModifierTracker)

    @staticmethod
    def build(pc_party: Party, monster_party: MonsterParty) -> "CombatContext":
        """Factory that registers all combatants with canonical IDs."""
        ctx = CombatContext(pc_party=pc_party, monster_party=monster_party)

        for pc in pc_party.members:
            cid = f"pc:{pc.name}"
            ctx.combatants[cid] = CombatantRef(id=cid, side=CombatSide.PC, entity=pc)

        for idx, monster in enumerate(monster_party.members):
            cid = f"monster:{monster.name}:{idx}"
            ctx.combatants[cid] = CombatantRef(
                id=cid, side=CombatSide.MONSTER, entity=monster
            )

        # Initialize morale tracking
        monster_count = len(monster_party.members)
        ctx.morale.initial_monster_count = monster_count
        # Morale 12 means fight to the death — immune to checks
        if monster_count > 0 and monster_party.members[0].morale >= 12:
            ctx.morale.is_immune = True

        return ctx

    def living(self, side: CombatSide) -> list[CombatantRef]:
        """Return all living, non-fled combatants on the given side."""
        return [
            ref
            for ref in self.combatants.values()
            if ref.side == side and ref.is_alive and not ref.has_fled
        ]

    def pcs_alive(self) -> bool:
        """Return True if any PC is alive and has not fled."""
        return any(
            ref.is_alive and not ref.has_fled
            for ref in self.combatants.values()
            if ref.side == CombatSide.PC
        )

    def monsters_alive(self) -> bool:
        """Return True if any monster is alive and has not fled."""
        return any(
            ref.is_alive and not ref.has_fled
            for ref in self.combatants.values()
            if ref.side == CombatSide.MONSTER
        )

    def monsters_incapacitated_count(self) -> int:
        """Return the number of monsters that are dead or have fled."""
        return sum(
            1
            for ref in self.combatants.values()
            if ref.side == CombatSide.MONSTER and (not ref.is_alive or ref.has_fled)
        )

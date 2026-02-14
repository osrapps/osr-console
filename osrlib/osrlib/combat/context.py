"""Combat context: combatant references and mutable state bag for the engine."""

from collections import deque
from dataclasses import dataclass, field
from enum import Enum, auto

from osrlib.combat.intents import ActionIntent
from osrlib.monster import Monster, MonsterParty
from osrlib.party import Party
from osrlib.player_character import PlayerCharacter


class CombatSide(Enum):
    """Which side of the encounter a combatant belongs to."""

    PC = auto()
    MONSTER = auto()


@dataclass
class CombatantRef:
    """Uniform handle wrapping either a PC or a Monster."""

    id: str
    side: CombatSide
    entity: PlayerCharacter | Monster

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

        return ctx

    def living(self, side: CombatSide) -> list[CombatantRef]:
        """Return all living combatants on the given side."""
        return [
            ref for ref in self.combatants.values() if ref.side == side and ref.is_alive
        ]

    def pcs_alive(self) -> bool:
        return any(
            ref.is_alive
            for ref in self.combatants.values()
            if ref.side == CombatSide.PC
        )

    def monsters_alive(self) -> bool:
        return any(
            ref.is_alive
            for ref in self.combatants.values()
            if ref.side == CombatSide.MONSTER
        )

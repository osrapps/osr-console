"""Targeting modes for spells and combat items."""

import random
from enum import Enum, auto


class TargetMode(Enum):
    """How a spell or item selects its targets."""

    SINGLE_ENEMY = auto()  # existing num_targets=1
    ALL_ENEMIES = auto()  # existing num_targets=-1
    SELF = auto()  # caster only (Shield)
    SINGLE_ALLY = auto()  # pick one ally (Cure Light Wounds)
    ALL_ALLIES = auto()  # entire friendly side (Bless)
    HD_POOL = auto()  # HD-pool targeting (Sleep): affects lowest-HD first


def get_combatant_hd(entity) -> int:
    """Return the effective hit dice of a combatant for HD-pool resolution.

    Args:
        entity: A Monster or PlayerCharacter instance.

    Returns:
        Hit dice count, minimum 1.
    """
    from osrlib.monster import Monster
    from osrlib.player_character import PlayerCharacter

    if isinstance(entity, Monster):
        return max(entity.hp_roll.num_dice, 1)
    if isinstance(entity, PlayerCharacter):
        return max(entity.level, 1)
    return 1


def resolve_hd_pool(
    candidates: tuple[tuple[str, int], ...], pool_total: int
) -> tuple[str, ...]:
    """Select targets from lowest HD upward until the HD pool is exhausted.

    Args:
        candidates: Sequence of (combatant_id, hd) pairs.
        pool_total: Total HD budget available.

    Returns:
        Tuple of selected combatant IDs.
    """
    if pool_total <= 0 or not candidates:
        return ()
    sorted_candidates = sorted(candidates, key=lambda c: c[1])
    selected: list[str] = []
    remaining = pool_total
    for cid, hd in sorted_candidates:
        effective_hd = max(hd, 1)
        if effective_hd > remaining:
            break
        selected.append(cid)
        remaining -= effective_hd
    return tuple(selected)


def resolve_random_group(
    candidates: tuple[str, ...], count: int
) -> tuple[str, ...]:
    """Select up to *count* random targets from *candidates*.

    Args:
        candidates: Available target IDs.
        count: Maximum number to select.

    Returns:
        Tuple of selected combatant IDs (order may vary).
    """
    if count <= 0 or not candidates:
        return ()
    actual = min(count, len(candidates))
    return tuple(random.sample(candidates, actual))

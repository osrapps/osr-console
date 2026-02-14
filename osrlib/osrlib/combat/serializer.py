"""JSON-compatible dict serializer for combat events."""

import dataclasses
from enum import Enum

from osrlib.combat.events import EncounterEvent


def _normalize_enums(obj: object) -> object:
    """Recursively convert enum values to their ``.name`` string."""
    if isinstance(obj, Enum):
        return obj.name
    if isinstance(obj, dict):
        return {k: _normalize_enums(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return type(obj)(_normalize_enums(item) for item in obj)
    return obj


class EventSerializer:
    """Converts combat events to JSON-serializable dicts."""

    @staticmethod
    def to_dict(event: EncounterEvent) -> dict:
        """Serialize *event* to a dict with a ``"kind"`` discriminator."""
        d = dataclasses.asdict(event)
        d = _normalize_enums(d)
        d["kind"] = type(event).__name__
        return d

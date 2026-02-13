"""JSON-compatible dict serializer for combat events."""

import dataclasses
from enum import Enum

from osrlib.combat.events import EncounterEvent


class EventSerializer:
    """Converts combat events to JSON-serializable dicts."""

    @staticmethod
    def to_dict(event: EncounterEvent) -> dict:
        """Serialize *event* to a dict with a ``"kind"`` discriminator."""
        d = dataclasses.asdict(event)
        # Normalize enum values to strings
        for key, value in d.items():
            if isinstance(value, Enum):
                d[key] = value.name
        d["kind"] = type(event).__name__
        return d

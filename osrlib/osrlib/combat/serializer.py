"""JSON-compatible dict serializer for combat events."""

import dataclasses
from enum import Enum
from types import MappingProxyType

from osrlib.combat.events import EncounterEvent, NeedAction


def _normalize(obj: object) -> object:
    """Recursively normalize enums and mapping proxies for JSON serialization."""
    if isinstance(obj, Enum):
        return obj.name
    if isinstance(obj, MappingProxyType):
        return {k: _normalize(v) for k, v in obj.items()}
    if isinstance(obj, dict):
        return {k: _normalize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return type(obj)(_normalize(item) for item in obj)
    return obj


def _asdict_safe(obj: object) -> object:
    """Like ``dataclasses.asdict`` but converts ``MappingProxyType`` to plain dicts first."""
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        result = {}
        for f in dataclasses.fields(obj):
            value = getattr(obj, f.name)
            result[f.name] = _asdict_safe(value)
        return result
    if isinstance(obj, MappingProxyType):
        return {k: _asdict_safe(v) for k, v in obj.items()}
    if isinstance(obj, dict):
        return {k: _asdict_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return type(obj)(_asdict_safe(item) for item in obj)
    return obj


class EventSerializer:
    """Converts combat events to JSON-serializable dicts."""

    @staticmethod
    def to_dict(event: EncounterEvent) -> dict:
        """Serialize *event* to a dict with a ``"kind"`` discriminator."""
        d = _asdict_safe(event)
        d = _normalize(d)

        # Inject computed `label` property into serialized ActionChoice dicts.
        if isinstance(event, NeedAction):
            for choice_dict, choice_obj in zip(d.get("available", []), event.available):
                choice_dict["label"] = choice_obj.label

        d["kind"] = type(event).__name__
        return d

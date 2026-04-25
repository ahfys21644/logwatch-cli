"""Load EventCounterConfig from dicts or YAML."""
from __future__ import annotations

from typing import Any, Dict, List

from logwatch.event_counter import EventCounter, EventCounterConfig


def load_event_counter_from_dict(data: Dict[str, Any]) -> EventCounterConfig:
    """Build an EventCounterConfig from a plain dict."""
    field_name = data.get("field")
    if not field_name:
        raise ValueError("event counter config requires 'field'")
    return EventCounterConfig(
        field=field_name,
        window=float(data.get("window", 60.0)),
        top_n=int(data.get("top_n", 10)),
    )


def load_event_counters_from_yaml(path: str) -> List[EventCounterConfig]:
    """Load a list of EventCounterConfig objects from a YAML file."""
    import yaml  # type: ignore

    with open(path, "r") as fh:
        raw = yaml.safe_load(fh) or {}
    items = raw.get("event_counters", [])
    return [load_event_counter_from_dict(item) for item in items]


def default_event_counter_config() -> EventCounterConfig:
    """Return a sensible default EventCounterConfig (counts by 'level')."""
    return EventCounterConfig(field="level", window=60.0, top_n=5)


def build_counters(configs: List[EventCounterConfig]) -> List[EventCounter]:
    """Instantiate EventCounter objects from a list of configs."""
    return [EventCounter(config=cfg) for cfg in configs]

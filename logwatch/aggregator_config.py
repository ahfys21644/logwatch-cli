"""Load AggregatorConfig from plain dicts or YAML."""
from __future__ import annotations

from typing import Any, Dict, List

from logwatch.aggregator import AggregatorConfig


def load_aggregator_config_from_dict(data: Dict[str, Any]) -> AggregatorConfig:
    """Build an AggregatorConfig from a mapping (e.g. parsed YAML)."""
    return AggregatorConfig(
        group_by=data.get("group_by", "level"),
        window_seconds=float(data.get("window_seconds", 10.0)),
        min_count=int(data.get("min_count", 1)),
        label=data.get("label", "aggregated"),
    )


def load_aggregator_configs_from_yaml(path: str) -> List[AggregatorConfig]:
    """Load a list of AggregatorConfig objects from a YAML file."""
    import yaml  # optional dependency

    with open(path, "r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)

    if not isinstance(raw, list):
        raw = [raw]
    return [load_aggregator_config_from_dict(item) for item in raw]


def default_aggregator_config() -> AggregatorConfig:
    """Return a sensible default config."""
    return AggregatorConfig(
        group_by="level",
        window_seconds=10.0,
        min_count=1,
        label="aggregated",
    )

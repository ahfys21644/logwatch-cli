"""Load CorrelatorConfig instances from dicts or YAML."""
from __future__ import annotations

from typing import Any, Dict, List

from logwatch.correlator import Correlator, CorrelatorConfig


def load_correlator_config_from_dict(data: Dict[str, Any]) -> CorrelatorConfig:
    """Build a CorrelatorConfig from a plain dictionary."""
    return CorrelatorConfig(
        group_by=data["group_by"],
        window_seconds=float(data.get("window_seconds", 5.0)),
        min_group_size=int(data.get("min_group_size", 2)),
        label=data.get("label", "correlated"),
    )


def load_correlator_configs_from_yaml(path: str) -> List[CorrelatorConfig]:
    """Load a list of CorrelatorConfig objects from a YAML file."""
    import yaml  # optional dependency

    with open(path, "r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)

    items = raw if isinstance(raw, list) else raw.get("correlators", [])
    return [load_correlator_config_from_dict(item) for item in items]


def default_correlator_config() -> CorrelatorConfig:
    """Return a sensible default CorrelatorConfig."""
    return CorrelatorConfig(
        group_by="request_id",
        window_seconds=5.0,
        min_group_size=2,
        label="correlated",
    )


def build_correlators_from_yaml(path: str) -> List[Correlator]:
    """Convenience: load configs and instantiate Correlator objects."""
    return [Correlator(config=cfg) for cfg in load_correlator_configs_from_yaml(path)]

"""Load SequenceConfig objects from dicts or YAML."""
from __future__ import annotations

from typing import Any, Dict, List

import yaml

from logwatch.sequence_detector import SequenceConfig


def load_sequence_config_from_dict(data: Dict[str, Any]) -> SequenceConfig:
    name = data.get("name", "unnamed")
    steps = data.get("steps")
    if not steps or not isinstance(steps, list):
        raise ValueError(f"Sequence '{name}' must define a list of steps")
    window = data.get("window")
    if window is None:
        raise ValueError(f"Sequence '{name}' must define a window")
    return SequenceConfig(
        name=name,
        steps=[str(s) for s in steps],
        window=float(window),
        level_filter=data.get("level_filter"),
    )


def load_sequence_configs_from_yaml(path: str) -> List[SequenceConfig]:
    with open(path, "r") as fh:
        raw = yaml.safe_load(fh) or {}
    items = raw.get("sequences", [])
    return [load_sequence_config_from_dict(item) for item in items]


def default_sequence_config() -> SequenceConfig:
    return SequenceConfig(
        name="default",
        steps=["starting", "ready"],
        window=30.0,
    )


def build_detectors_from_list(
    items: List[Dict[str, Any]],
) -> List[SequenceConfig]:
    return [load_sequence_config_from_dict(item) for item in items]

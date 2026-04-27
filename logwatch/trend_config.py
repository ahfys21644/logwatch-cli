"""Load TrendConfig objects from dicts or YAML."""
from __future__ import annotations

from typing import Any, Dict, List

import yaml

from logwatch.trend_detector import TrendConfig


def load_trend_config_from_dict(data: Dict[str, Any]) -> TrendConfig:
    if "name" not in data:
        raise ValueError("trend config requires 'name'")
    return TrendConfig(
        name=data["name"],
        level=data.get("level", "error"),
        window=float(data.get("window", 60.0)),
        min_periods=int(data.get("min_periods", 3)),
        deviation_pct=float(data.get("deviation_pct", 50.0)),
    )


def load_trend_configs_from_yaml(path: str) -> List[TrendConfig]:
    with open(path, "r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}
    items = raw.get("trends", [])
    return [load_trend_config_from_dict(item) for item in items]


def default_trend_config() -> TrendConfig:
    return TrendConfig(
        name="default_trend",
        level="warning",
        window=60.0,
        min_periods=3,
        deviation_pct=50.0,
    )


def build_detectors_from_list(
    items: List[Dict[str, Any]]
) -> List["TrendDetector"]:  # noqa: F821
    from logwatch.trend_detector import TrendDetector

    return [TrendDetector(load_trend_config_from_dict(item)) for item in items]

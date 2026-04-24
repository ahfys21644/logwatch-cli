"""Load AnomalyConfig instances from dicts or YAML."""
from __future__ import annotations

from typing import Any, Dict, List

from logwatch.anomaly_detector import AnomalyConfig


def load_anomaly_configs_from_list(raw: List[Dict[str, Any]]) -> List[AnomalyConfig]:
    """Build AnomalyConfig objects from a list of plain dicts."""
    configs: List[AnomalyConfig] = []
    for item in raw:
        cfg = AnomalyConfig(
            level=item["level"],
            window_seconds=float(item["window_seconds"]),
            max_count=int(item["max_count"]),
            name=item.get("name", ""),
        )
        configs.append(cfg)
    return configs


def load_anomaly_configs_from_yaml(path: str) -> List[AnomalyConfig]:
    """Load anomaly detection rules from a YAML file.

    Expected structure::

        anomalies:
          - level: error
            window_seconds: 60
            max_count: 10
            name: too_many_errors
    """
    import yaml  # type: ignore

    with open(path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return load_anomaly_configs_from_list(data.get("anomalies", []))


def default_anomaly_configs() -> List[AnomalyConfig]:
    """Sensible defaults used when no config file is supplied."""
    return [
        AnomalyConfig(level="error", window_seconds=60.0, max_count=20,
                      name="high_error_rate"),
        AnomalyConfig(level="critical", window_seconds=60.0, max_count=5,
                      name="high_critical_rate"),
    ]

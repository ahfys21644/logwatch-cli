"""Load RetentionPolicy objects from plain dicts or YAML configuration."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore

from logwatch.retention import RetentionPolicy


def load_retention_policy_from_dict(
    data: Dict[str, Any],
) -> RetentionPolicy:
    """Build a :class:`RetentionPolicy` from a plain mapping.

    Expected keys:
      - ``max_age_seconds`` (float, required)
      - ``timestamp_field`` (str, optional, default ``"timestamp"``)
    """
    max_age = float(data["max_age_seconds"])
    ts_field = str(data.get("timestamp_field", "timestamp"))
    return RetentionPolicy(max_age_seconds=max_age, timestamp_field=ts_field)


def load_retention_policies_from_yaml(
    path: str,
) -> List[RetentionPolicy]:
    """Parse a YAML file that contains a top-level ``retention`` list."""
    if yaml is None:  # pragma: no cover
        raise RuntimeError("PyYAML is required to load retention config from YAML")
    with open(path, "r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)
    items: List[Dict[str, Any]] = (raw or {}).get("retention", [])
    return [load_retention_policy_from_dict(item) for item in items]


def default_retention_policy(
    max_age_seconds: float = 3600.0,
    timestamp_field: str = "timestamp",
) -> RetentionPolicy:
    """Convenience factory with sensible defaults (1-hour window)."""
    return RetentionPolicy(
        max_age_seconds=max_age_seconds,
        timestamp_field=timestamp_field,
    )

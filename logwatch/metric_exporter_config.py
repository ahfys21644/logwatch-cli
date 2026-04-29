"""Load MetricExporterConfig from dicts / YAML."""
from __future__ import annotations

from typing import Any, Dict

from logwatch.metric_exporter import MetricExporterConfig


def load_exporter_config_from_dict(data: Dict[str, Any]) -> MetricExporterConfig:
    """Build a MetricExporterConfig from a plain dictionary."""
    namespace = data.get("namespace", "logwatch")
    extra_labels = data.get("extra_labels", {})
    if not isinstance(extra_labels, dict):
        raise ValueError("extra_labels must be a mapping")
    return MetricExporterConfig(namespace=namespace, extra_labels=extra_labels)


def load_exporter_config_from_yaml(path: str) -> MetricExporterConfig:
    """Load a MetricExporterConfig from a YAML file."""
    try:
        import yaml  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise ImportError("PyYAML is required to load config from YAML") from exc

    with open(path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}

    return load_exporter_config_from_dict(data.get("metric_exporter", data))


def default_exporter_config() -> MetricExporterConfig:
    """Return a sensible default MetricExporterConfig."""
    return MetricExporterConfig(namespace="logwatch", extra_labels={})

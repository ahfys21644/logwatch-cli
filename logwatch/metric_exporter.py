"""Export session metrics in Prometheus-compatible text format."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from logwatch.stats import SessionStats


@dataclass
class MetricExporterConfig:
    namespace: str = "logwatch"
    extra_labels: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.namespace:
            raise ValueError("namespace must not be empty")
        if not self.namespace.replace("_", "").isalnum():
            raise ValueError("namespace must contain only alphanumeric characters and underscores")


def _label_str(labels: Dict[str, str]) -> str:
    if not labels:
        return ""
    parts = [f'{k}="{v}"' for k, v in sorted(labels.items())]
    return "{" + ",".join(parts) + "}"


def export_metrics(stats: SessionStats, config: Optional[MetricExporterConfig] = None) -> str:
    """Return a Prometheus text-format string for the given SessionStats."""
    if config is None:
        config = MetricExporterConfig()

    ns = config.namespace
    base_labels = config.extra_labels
    lines: List[str] = []

    summary = stats.summary()

    # Total entries processed
    lines.append(f"# HELP {ns}_entries_total Total log entries processed")
    lines.append(f"# TYPE {ns}_entries_total counter")
    lines.append(f"{ns}_entries_total{_label_str(base_labels)} {summary.get('total', 0)}")

    # Per-level counters
    lines.append(f"# HELP {ns}_entries_by_level_total Log entries grouped by level")
    lines.append(f"# TYPE {ns}_entries_by_level_total counter")
    for level, count in sorted(summary.get("by_level", {}).items()):
        labels = {**base_labels, "level": level.lower()}
        lines.append(f"{ns}_entries_by_level_total{_label_str(labels)} {count}")

    # Alerts fired
    lines.append(f"# HELP {ns}_alerts_total Total alert rules triggered")
    lines.append(f"# TYPE {ns}_alerts_total counter")
    lines.append(f"{ns}_alerts_total{_label_str(base_labels)} {summary.get('alerts', 0)}")

    lines.append("")  # trailing newline
    return "\n".join(lines)


def export_metrics_to_file(stats: SessionStats, path: str, config: Optional[MetricExporterConfig] = None) -> None:
    """Write Prometheus metrics to *path*."""
    content = export_metrics(stats, config)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)

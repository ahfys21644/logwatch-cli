"""Aggregator: bucket log entries by a field and emit periodic summaries."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from time import monotonic
from typing import Callable, Dict, List, Optional

LogEntry = dict


@dataclass
class AggregatorConfig:
    group_by: str = "level"          # field name to bucket on
    window_seconds: float = 10.0      # flush interval
    min_count: int = 1                # only emit buckets with at least this many entries
    label: str = "aggregated"         # tag added to summary entries


@dataclass
class Aggregator:
    config: AggregatorConfig
    _buckets: Dict[str, List[LogEntry]] = field(default_factory=lambda: defaultdict(list))
    _window_start: float = field(default_factory=monotonic)

    def feed(self, entry: LogEntry) -> Optional[List[LogEntry]]:
        """Accept an entry; return flushed summaries if the window expired."""
        key = str(entry.get(self.config.group_by, "unknown"))
        self._buckets[key].append(entry)

        if monotonic() - self._window_start >= self.config.window_seconds:
            return self.flush()
        return None

    def flush(self) -> List[LogEntry]:
        """Force-flush all buckets and reset the window."""
        summaries: List[LogEntry] = []
        for key, entries in self._buckets.items():
            if len(entries) >= self.config.min_count:
                summaries.append(_make_summary(key, entries, self.config))
        self._buckets = defaultdict(list)
        self._window_start = monotonic()
        return summaries

    def reset(self) -> None:
        """Discard all buffered data and restart the window."""
        self._buckets = defaultdict(list)
        self._window_start = monotonic()


def _make_summary(key: str, entries: List[LogEntry], cfg: AggregatorConfig) -> LogEntry:
    levels = [e.get("level", "info").upper() for e in entries]
    highest = max(levels, key=lambda l: ["DEBUG", "INFO", "WARN", "ERROR", "CRITICAL"].index(l)
                  if l in ["DEBUG", "INFO", "WARN", "ERROR", "CRITICAL"] else 0)
    return {
        "level": highest,
        "message": f"[{cfg.label}] {cfg.group_by}={key} count={len(entries)}",
        "aggregated_key": key,
        "aggregated_count": len(entries),
        "aggregated_label": cfg.label,
        "timestamp": entries[-1].get("timestamp", ""),
    }


def build_aggregator(group_by: str = "level",
                     window_seconds: float = 10.0,
                     min_count: int = 1,
                     label: str = "aggregated") -> Aggregator:
    return Aggregator(config=AggregatorConfig(
        group_by=group_by,
        window_seconds=window_seconds,
        min_count=min_count,
        label=label,
    ))

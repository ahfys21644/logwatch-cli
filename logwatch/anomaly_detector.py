"""Anomaly detection based on rolling rate thresholds per log level."""
from __future__ import annotations

import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Deque, Dict, List, Optional


@dataclass
class AnomalyConfig:
    level: str
    window_seconds: float
    max_count: int
    name: str = ""

    def __post_init__(self) -> None:
        if self.window_seconds <= 0:
            raise ValueError("window_seconds must be positive")
        if self.max_count <= 0:
            raise ValueError("max_count must be positive")
        if not self.name:
            self.name = f"anomaly:{self.level}:>{self.max_count}/{self.window_seconds}s"


@dataclass
class AnomalyEvent:
    config_name: str
    level: str
    count: int
    window_seconds: float
    triggered_at: float = field(default_factory=time.monotonic)

    def __str__(self) -> str:
        return (
            f"[ANOMALY] {self.config_name} — {self.count} '{self.level}' entries "
            f"in last {self.window_seconds}s (max {self.count})"
        )


class AnomalyDetector:
    """Tracks per-level event rates and fires AnomalyEvents when thresholds are exceeded."""

    def __init__(self, configs: List[AnomalyConfig]) -> None:
        self._configs = configs
        self._buckets: Dict[str, Deque[float]] = defaultdict(deque)

    def feed(self, entry: dict) -> Optional[AnomalyEvent]:
        """Record an entry and return an AnomalyEvent if any threshold is breached."""
        level = (entry.get("level") or "").lower()
        now = time.monotonic()
        self._buckets[level].append(now)

        for cfg in self._configs:
            if cfg.level.lower() != level:
                continue
            bucket = self._buckets[level]
            cutoff = now - cfg.window_seconds
            while bucket and bucket[0] < cutoff:
                bucket.popleft()
            if len(bucket) > cfg.max_count:
                return AnomalyEvent(
                    config_name=cfg.name,
                    level=level,
                    count=len(bucket),
                    window_seconds=cfg.window_seconds,
                    triggered_at=now,
                )
        return None

    def reset(self) -> None:
        self._buckets.clear()

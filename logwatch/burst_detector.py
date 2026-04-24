"""Burst detector: raises an alert when log volume exceeds a threshold within a sliding window."""
from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, List, Optional


@dataclass
class BurstConfig:
    name: str
    window_seconds: float
    max_count: int
    level: str = "error"

    def __post_init__(self) -> None:
        if self.window_seconds <= 0:
            raise ValueError("window_seconds must be positive")
        if self.max_count <= 0:
            raise ValueError("max_count must be positive")


@dataclass
class BurstEvent:
    rule_name: str
    count: int
    window_seconds: float
    level: str

    def __str__(self) -> str:
        return (
            f"[BURST] {self.rule_name}: {self.count} entries "
            f"in {self.window_seconds}s window (level>={self.level})"
        )


class BurstDetector:
    """Tracks entry timestamps and fires a BurstEvent when the burst threshold is exceeded."""

    def __init__(self, config: BurstConfig) -> None:
        self._cfg = config
        self._timestamps: Deque[float] = deque()

    def _purge(self, now: float) -> None:
        cutoff = now - self._cfg.window_seconds
        while self._timestamps and self._timestamps[0] < cutoff:
            self._timestamps.popleft()

    def feed(self, entry: dict, now: Optional[float] = None) -> Optional[BurstEvent]:
        """Record an entry and return a BurstEvent if the threshold is exceeded."""
        ts = now if now is not None else time.monotonic()
        self._purge(ts)
        self._timestamps.append(ts)
        if len(self._timestamps) > self._cfg.max_count:
            return BurstEvent(
                rule_name=self._cfg.name,
                count=len(self._timestamps),
                window_seconds=self._cfg.window_seconds,
                level=self._cfg.level,
            )
        return None

    def current_count(self, now: Optional[float] = None) -> int:
        ts = now if now is not None else time.monotonic()
        self._purge(ts)
        return len(self._timestamps)

    def reset(self) -> None:
        self._timestamps.clear()


def build_burst_detectors(configs: List[BurstConfig]) -> List[BurstDetector]:
    return [BurstDetector(cfg) for cfg in configs]

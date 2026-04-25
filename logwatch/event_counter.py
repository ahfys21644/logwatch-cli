"""Per-field event counting with windowed reset and top-N reporting."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from time import monotonic
from typing import Dict, List, Optional, Tuple


@dataclass
class EventCounterConfig:
    field: str
    window: float = 60.0  # seconds
    top_n: int = 10

    def __post_init__(self) -> None:
        if not self.field:
            raise ValueError("field must not be empty")
        if self.window <= 0:
            raise ValueError("window must be positive")
        if self.top_n < 1:
            raise ValueError("top_n must be at least 1")


@dataclass
class EventCounter:
    config: EventCounterConfig
    _counts: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    _window_start: float = field(default_factory=monotonic)

    def _maybe_reset(self) -> None:
        now = monotonic()
        if now - self._window_start >= self.config.window:
            self._counts = defaultdict(int)
            self._window_start = now

    def record(self, entry: dict) -> None:
        self._maybe_reset()
        value = entry.get(self.config.field)
        if value is not None:
            self._counts[str(value)] += 1

    def record_all(self, entries: List[dict]) -> None:
        for entry in entries:
            self.record(entry)

    def top(self, n: Optional[int] = None) -> List[Tuple[str, int]]:
        limit = n if n is not None else self.config.top_n
        return sorted(self._counts.items(), key=lambda x: x[1], reverse=True)[:limit]

    def total(self) -> int:
        return sum(self._counts.values())

    def count_for(self, value: str) -> int:
        return self._counts.get(value, 0)

    def reset(self) -> None:
        self._counts = defaultdict(int)
        self._window_start = monotonic()

    def summary(self) -> dict:
        return {
            "field": self.config.field,
            "window": self.config.window,
            "total": self.total(),
            "top": self.top(),
        }

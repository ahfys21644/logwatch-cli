"""pattern_counter.py — counts log entries matching regex patterns over a sliding window."""
from __future__ import annotations

import re
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class PatternCounterConfig:
    name: str
    pattern: str
    window: float  # seconds
    threshold: int  # alert when count >= threshold within window
    level_filter: Optional[str] = None  # only count entries at this level or above

    def __post_init__(self) -> None:
        if self.window <= 0:
            raise ValueError("window must be positive")
        if self.threshold <= 0:
            raise ValueError("threshold must be positive")
        self._regex = re.compile(self.pattern, re.IGNORECASE)

    @property
    def regex(self) -> re.Pattern:
        return self._regex


@dataclass
class PatternCountEvent:
    name: str
    pattern: str
    count: int
    window: float
    threshold: int

    def __str__(self) -> str:
        return (
            f"[PatternCount] '{self.name}' matched {self.count} times "
            f"(threshold={self.threshold}) in {self.window}s window"
        )


_LEVELS = ["debug", "info", "warn", "warning", "error", "critical"]


def _level_index(level: str) -> int:
    l = level.lower()
    if l == "warning":
        l = "warn"
    try:
        return _LEVELS.index(l)
    except ValueError:
        return 1  # default to info


@dataclass
class PatternCounter:
    config: PatternCounterConfig
    _timestamps: deque = field(default_factory=deque, init=False)

    def _purge(self, now: float) -> None:
        cutoff = now - self.config.window
        while self._timestamps and self._timestamps[0] < cutoff:
            self._timestamps.popleft()

    def feed(self, entry: dict) -> Optional[PatternCountEvent]:
        now = time.monotonic()
        self._purge(now)

        msg = entry.get("message", "")
        level = entry.get("level", "info")

        if self.config.level_filter:
            if _level_index(level) < _level_index(self.config.level_filter):
                return None

        if not self.config.regex.search(msg):
            return None

        self._timestamps.append(now)
        count = len(self._timestamps)

        if count >= self.config.threshold:
            return PatternCountEvent(
                name=self.config.name,
                pattern=self.config.pattern,
                count=count,
                window=self.config.window,
                threshold=self.config.threshold,
            )
        return None

    def reset(self) -> None:
        self._timestamps.clear()

    @property
    def current_count(self) -> int:
        now = time.monotonic()
        self._purge(now)
        return len(self._timestamps)

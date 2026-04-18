"""Alert throttle: limit how many alerts are emitted per level per time window."""
from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class ThrottleConfig:
    window_seconds: float = 60.0
    max_per_window: int = 5


class AlertThrottle:
    """Track alert emission counts per rule name within a rolling time window."""

    def __init__(self, config: ThrottleConfig | None = None) -> None:
        self._config = config or ThrottleConfig()
        # rule_name -> list of emission timestamps
        self._timestamps: Dict[str, List[float]] = defaultdict(list)

    def _purge(self, rule_name: str, now: float) -> None:
        cutoff = now - self._config.window_seconds
        self._timestamps[rule_name] = [
            t for t in self._timestamps[rule_name] if t >= cutoff
        ]

    def allow(self, rule_name: str, now: float | None = None) -> bool:
        """Return True if the alert should be emitted, False if throttled."""
        if now is None:
            now = time.monotonic()
        self._purge(rule_name, now)
        if len(self._timestamps[rule_name]) < self._config.max_per_window:
            self._timestamps[rule_name].append(now)
            return True
        return False

    def emission_count(self, rule_name: str, now: float | None = None) -> int:
        if now is None:
            now = time.monotonic()
        self._purge(rule_name, now)
        return len(self._timestamps[rule_name])

    def reset(self, rule_name: str) -> None:
        self._timestamps.pop(rule_name, None)

    def reset_all(self) -> None:
        self._timestamps.clear()

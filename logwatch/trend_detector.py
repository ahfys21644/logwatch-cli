"""Trend detector: tracks metric rates over rolling windows and fires events
when a sustained upward or downward trend is detected."""
from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, List, Optional, Tuple


@dataclass
class TrendConfig:
    name: str
    level: str = "error"
    window: float = 60.0          # seconds per bucket pair
    min_periods: int = 3          # minimum data points required
    deviation_pct: float = 50.0   # % rise/fall to call a trend

    def __post_init__(self) -> None:
        if self.window <= 0:
            raise ValueError("window must be positive")
        if self.min_periods < 2:
            raise ValueError("min_periods must be >= 2")
        if self.deviation_pct <= 0:
            raise ValueError("deviation_pct must be positive")


@dataclass
class TrendEvent:
    rule_name: str
    direction: str          # "up" or "down"
    start_rate: float
    end_rate: float
    periods: int

    def __str__(self) -> str:
        pct = abs(self.end_rate - self.start_rate) / max(self.start_rate, 1e-9) * 100
        return (
            f"[TREND:{self.rule_name}] {self.direction.upper()} trend over "
            f"{self.periods} periods ({pct:.1f}% change, "
            f"{self.start_rate:.2f} -> {self.end_rate:.2f} events/s)"
        )


class TrendDetector:
    """Accumulates bucketed counts and detects monotonic rate trends."""

    def __init__(self, config: TrendConfig) -> None:
        self.config = config
        self._buckets: Deque[Tuple[float, int]] = deque()  # (bucket_start, count)
        self._current_start: float = time.monotonic()
        self._current_count: int = 0

    def record(self, ts: Optional[float] = None) -> Optional[TrendEvent]:
        now = ts if ts is not None else time.monotonic()
        if now - self._current_start >= self.config.window:
            rate = self._current_count / max(self.config.window, 1e-9)
            self._buckets.append((self._current_start, rate))
            self._current_start = now
            self._current_count = 0
            return self._evaluate()
        self._current_count += 1
        return None

    def _evaluate(self) -> Optional[TrendEvent]:
        buckets = list(self._buckets)
        if len(buckets) < self.config.min_periods:
            return None
        rates: List[float] = [r for _, r in buckets]
        direction = self._monotonic_direction(rates)
        if direction is None:
            return None
        start_rate, end_rate = rates[0], rates[-1]
        base = max(start_rate, 1e-9)
        pct = abs(end_rate - start_rate) / base * 100
        if pct < self.config.deviation_pct:
            return None
        return TrendEvent(
            rule_name=self.config.name,
            direction=direction,
            start_rate=start_rate,
            end_rate=end_rate,
            periods=len(rates),
        )

    @staticmethod
    def _monotonic_direction(rates: List[float]) -> Optional[str]:
        if all(rates[i] <= rates[i + 1] for i in range(len(rates) - 1)):
            return "up"
        if all(rates[i] >= rates[i + 1] for i in range(len(rates) - 1)):
            return "down"
        return None

    def reset(self) -> None:
        self._buckets.clear()
        self._current_start = time.monotonic()
        self._current_count = 0

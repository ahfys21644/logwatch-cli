"""Baseline tracker: learns normal log-rate ranges and flags deviations."""
from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Optional


@dataclass
class BaselineConfig:
    name: str = "default"
    window_seconds: float = 60.0   # sliding window for live rate
    learn_periods: int = 10        # how many windows to keep for baseline
    deviation_factor: float = 3.0  # flag if live_rate > baseline_mean * factor

    def __post_init__(self) -> None:
        if self.window_seconds <= 0:
            raise ValueError("window_seconds must be positive")
        if self.learn_periods < 1:
            raise ValueError("learn_periods must be >= 1")
        if self.deviation_factor <= 0:
            raise ValueError("deviation_factor must be positive")


@dataclass
class BaselineEvent:
    name: str
    live_rate: float      # events / second in current window
    baseline_mean: float  # average rate over historical windows
    factor: float         # live_rate / baseline_mean

    def __str__(self) -> str:
        return (
            f"[BASELINE:{self.name}] rate={self.live_rate:.2f}/s "
            f"baseline={self.baseline_mean:.2f}/s "
            f"factor={self.factor:.1f}x"
        )


class BaselineTracker:
    """Feed log entries; returns a BaselineEvent when a deviation is detected."""

    def __init__(self, cfg: BaselineConfig) -> None:
        self.cfg = cfg
        self._window: Deque[float] = deque()
        self._history: Deque[float] = deque(maxlen=cfg.learn_periods)
        self._window_start: float = time.monotonic()

    # ------------------------------------------------------------------
    def feed(self, _entry: object, ts: Optional[float] = None) -> Optional[BaselineEvent]:
        """Record one entry.  *ts* overrides the real clock (for tests)."""
        now = ts if ts is not None else time.monotonic()
        self._window.append(now)
        return self._maybe_rotate(now)

    def flush(self, ts: Optional[float] = None) -> Optional[BaselineEvent]:
        """Force-close the current window and record its rate."""
        now = ts if ts is not None else time.monotonic()
        return self._rotate(now)

    # ------------------------------------------------------------------
    def _maybe_rotate(self, now: float) -> Optional[BaselineEvent]:
        elapsed = now - self._window_start
        if elapsed >= self.cfg.window_seconds:
            return self._rotate(now)
        return None

    def _rotate(self, now: float) -> Optional[BaselineEvent]:
        elapsed = max(now - self._window_start, 1e-9)
        count = len(self._window)
        rate = count / elapsed

        event: Optional[BaselineEvent] = None
        if self._history:
            mean = sum(self._history) / len(self._history)
            if mean > 0 and rate > mean * self.cfg.deviation_factor:
                event = BaselineEvent(
                    name=self.cfg.name,
                    live_rate=rate,
                    baseline_mean=mean,
                    factor=rate / mean,
                )

        self._history.append(rate)
        self._window.clear()
        self._window_start = now
        return event

"""Watchdog: monitors a log source and fires events when silence or inactivity is detected."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class WatchdogConfig:
    name: str
    silence_window: float  # seconds without any entry before firing
    level_filter: Optional[str] = None  # only watch entries at this level or above
    on_silence: Optional[Callable[["WatchdogEvent"], None]] = None

    def __post_init__(self) -> None:
        if self.silence_window <= 0:
            raise ValueError("silence_window must be positive")


@dataclass
class WatchdogEvent:
    name: str
    silence_seconds: float
    last_seen: Optional[float]

    def __str__(self) -> str:
        last = f"{self.silence_seconds:.1f}s ago" if self.last_seen else "never"
        return f"[WATCHDOG] '{self.name}' silent for {self.silence_seconds:.1f}s (last seen: {last})"


class Watchdog:
    def __init__(self, config: WatchdogConfig, clock: Callable[[], float] = time.monotonic) -> None:
        self.config = config
        self._clock = clock
        self._last_seen: Optional[float] = None
        self._fired: bool = False

    def feed(self, entry: dict) -> None:
        """Notify the watchdog that an entry was received."""
        level = entry.get("level", "info").upper()
        if self.config.level_filter:
            from logwatch.filter import _LEVELS  # type: ignore
            threshold = _LEVELS.get(self.config.level_filter.upper(), 0)
            if _LEVELS.get(level, 0) < threshold:
                return
        self._last_seen = self._clock()
        self._fired = False

    def check(self) -> Optional[WatchdogEvent]:
        """Return a WatchdogEvent if silence threshold exceeded, else None."""
        now = self._clock()
        if self._last_seen is None:
            elapsed = float("inf")
        else:
            elapsed = now - self._last_seen
        if elapsed >= self.config.silence_window and not self._fired:
            self._fired = True
            event = WatchdogEvent(
                name=self.config.name,
                silence_seconds=elapsed if elapsed != float("inf") else self.config.silence_window,
                last_seen=self._last_seen,
            )
            if self.config.on_silence:
                self.config.on_silence(event)
            return event
        return None

    def reset(self) -> None:
        self._last_seen = None
        self._fired = False

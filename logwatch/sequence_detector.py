"""Detect ordered sequences of log patterns within a time window."""
from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


@dataclass
class SequenceConfig:
    name: str
    steps: List[str]          # ordered list of regex patterns
    window: float             # seconds within which all steps must match
    level_filter: Optional[str] = None

    def __post_init__(self) -> None:
        if len(self.steps) < 2:
            raise ValueError("SequenceConfig requires at least 2 steps")
        if self.window <= 0:
            raise ValueError("window must be positive")
        self._compiled = [re.compile(p, re.IGNORECASE) for p in self.steps]

    @property
    def compiled(self) -> List[re.Pattern]:
        return self._compiled


@dataclass
class SequenceEvent:
    config_name: str
    matched_messages: List[str]
    duration: float

    def __str__(self) -> str:
        return (
            f"[SEQUENCE:{self.config_name}] "
            f"{len(self.matched_messages)} steps in {self.duration:.2f}s"
        )


@dataclass
class SequenceDetector:
    config: SequenceConfig
    on_event: Callable[[SequenceEvent], None] = field(default=lambda e: None)

    # internal state
    _step_index: int = field(default=0, init=False, repr=False)
    _matched: List[str] = field(default_factory=list, init=False, repr=False)
    _start_ts: Optional[float] = field(default=None, init=False, repr=False)

    def feed(self, entry: Dict) -> Optional[SequenceEvent]:
        message = entry.get("message", "")
        level = entry.get("level", "info").upper()
        now = time.time()

        if self.config.level_filter and level != self.config.level_filter.upper():
            return None

        # reset if window expired
        if self._start_ts is not None and (now - self._start_ts) > self.config.window:
            self._reset()

        pattern = self.config.compiled[self._step_index]
        if pattern.search(message):
            if self._step_index == 0:
                self._start_ts = now
            self._matched.append(message)
            self._step_index += 1

            if self._step_index == len(self.config.steps):
                duration = now - (self._start_ts or now)
                event = SequenceEvent(
                    config_name=self.config.name,
                    matched_messages=list(self._matched),
                    duration=duration,
                )
                self._reset()
                self.on_event(event)
                return event

        return None

    def _reset(self) -> None:
        self._step_index = 0
        self._matched = []
        self._start_ts = None

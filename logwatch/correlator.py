"""Entry correlation: group related log entries by a shared field or pattern."""
from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


@dataclass
class CorrelatorConfig:
    group_by: str  # field name to group on, e.g. "request_id"
    window_seconds: float = 5.0
    min_group_size: int = 2
    label: str = "correlated"

    def __post_init__(self) -> None:
        if self.window_seconds <= 0:
            raise ValueError("window_seconds must be positive")
        if self.min_group_size < 1:
            raise ValueError("min_group_size must be >= 1")


@dataclass
class Correlator:
    config: CorrelatorConfig
    _groups: Dict[str, List[dict]] = field(default_factory=dict, init=False)
    _timestamps: Dict[str, float] = field(default_factory=dict, init=False)

    def feed(self, entry: dict) -> Optional[List[dict]]:
        """Feed an entry; return a correlated group if the window closes."""
        key = entry.get("fields", {}).get(self.config.group_by) or entry.get(self.config.group_by)
        if key is None:
            return None

        now = time.monotonic()
        self._purge(now)

        if key not in self._groups:
            self._groups[key] = []
            self._timestamps[key] = now

        self._groups[key].append(entry)

        elapsed = now - self._timestamps[key]
        if elapsed >= self.config.window_seconds:
            return self._close_group(key)
        return None

    def flush(self) -> List[List[dict]]:
        """Close all open groups regardless of window and return them."""
        keys = list(self._groups.keys())
        result = []
        for key in keys:
            group = self._close_group(key)
            if group is not None:
                result.append(group)
        return result

    def _close_group(self, key: str) -> Optional[List[dict]]:
        group = self._groups.pop(key, [])
        self._timestamps.pop(key, None)
        if len(group) >= self.config.min_group_size:
            for entry in group:
                entry.setdefault("labels", set()).add(self.config.label)
            return group
        return None

    def _purge(self, now: float) -> None:
        expired = [
            k for k, ts in self._timestamps.items()
            if now - ts >= self.config.window_seconds
        ]
        for key in expired:
            self._close_group(key)


def build_correlator(group_by: str, window_seconds: float = 5.0,
                     min_group_size: int = 2, label: str = "correlated") -> Correlator:
    cfg = CorrelatorConfig(
        group_by=group_by,
        window_seconds=window_seconds,
        min_group_size=min_group_size,
        label=label,
    )
    return Correlator(config=cfg)

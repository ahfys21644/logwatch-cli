"""Retention policy: drop or archive log entries older than a configured age."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Iterable, List, Optional


@dataclass
class RetentionPolicy:
    """Drop entries whose timestamp exceeds *max_age_seconds* relative to now."""

    max_age_seconds: float
    timestamp_field: str = "timestamp"
    # Optional hook called with every dropped entry (e.g. for archiving).
    on_drop: Optional[Callable[[dict], None]] = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if self.max_age_seconds <= 0:
            raise ValueError("max_age_seconds must be positive")

    def is_expired(self, entry: dict, now: Optional[float] = None) -> bool:
        """Return True when *entry* is older than the configured window."""
        ts = entry.get(self.timestamp_field)
        if ts is None:
            return False
        try:
            age = (now if now is not None else time.time()) - float(ts)
            return age > self.max_age_seconds
        except (TypeError, ValueError):
            return False

    def apply(self, entry: dict, now: Optional[float] = None) -> Optional[dict]:
        """Return *entry* if it should be kept, else None (and fire on_drop)."""
        if self.is_expired(entry, now=now):
            if self.on_drop is not None:
                self.on_drop(entry)
            return None
        return entry


def apply_retention(
    entries: Iterable[dict],
    policy: RetentionPolicy,
    now: Optional[float] = None,
) -> List[dict]:
    """Filter *entries* through *policy*, returning only non-expired ones."""
    kept: List[dict] = []
    for entry in entries:
        result = policy.apply(entry, now=now)
        if result is not None:
            kept.append(result)
    return kept


def retention_step(
    policy: RetentionPolicy,
    now: Optional[float] = None,
) -> Callable[[dict], Optional[dict]]:
    """Return a transformer-compatible step function for *policy*."""

    def _step(entry: dict) -> Optional[dict]:
        return policy.apply(entry, now=now)

    return _step

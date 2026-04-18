"""Deduplication of repeated log entries within a sliding time window."""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from typing import Dict, Optional


def _entry_key(entry: dict) -> str:
    """Stable hash key from message + level."""
    raw = f"{entry.get('level', '')}:{entry.get('message', '')}"
    return hashlib.md5(raw.encode()).hexdigest()


@dataclass
class DedupFilter:
    """Suppress repeated identical log lines within *window_seconds*."""

    window_seconds: float = 5.0
    _seen: Dict[str, float] = field(default_factory=dict, init=False, repr=False)

    def is_duplicate(self, entry: dict) -> bool:
        """Return True if an identical entry was seen within the window."""
        key = _entry_key(entry)
        now = time.monotonic()
        last_seen = self._seen.get(key)
        if last_seen is not None and (now - last_seen) < self.window_seconds:
            return True
        self._seen[key] = now
        return False

    def filter(self, entry: dict) -> Optional[dict]:
        """Return *entry* if it is not a duplicate, else None."""
        return None if self.is_duplicate(entry) else entry

    def purge_expired(self) -> int:
        """Remove stale entries; return count removed."""
        now = time.monotonic()
        expired = [k for k, t in self._seen.items() if (now - t) >= self.window_seconds]
        for k in expired:
            del self._seen[k]
        return len(expired)

    def reset(self) -> None:
        """Clear all tracked entries."""
        self._seen.clear()

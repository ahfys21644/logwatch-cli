"""Per-field value frequency tracker for structured log entries."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Tuple


@dataclass
class FieldStats:
    """Tracks value frequencies for one or more entry fields."""

    fields: List[str]
    max_values: int = 50
    _counts: Dict[str, Dict[str, int]] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        if not self.fields:
            raise ValueError("fields must not be empty")
        if self.max_values < 1:
            raise ValueError("max_values must be >= 1")
        self._counts = {f: defaultdict(int) for f in self.fields}

    def record(self, entry: dict) -> None:
        """Record field values from a single log entry."""
        for f in self.fields:
            value = entry.get(f)
            if value is None:
                continue
            bucket = self._counts[f]
            key = str(value)
            if key in bucket or len(bucket) < self.max_values:
                bucket[key] += 1

    def record_all(self, entries: Iterable[dict]) -> None:
        """Record field values from multiple entries."""
        for entry in entries:
            self.record(entry)

    def top(self, field_name: str, n: int = 10) -> List[Tuple[str, int]]:
        """Return the top-n most frequent values for a field."""
        bucket = self._counts.get(field_name)
        if bucket is None:
            raise KeyError(f"Field {field_name!r} is not tracked")
        return sorted(bucket.items(), key=lambda kv: kv[1], reverse=True)[:n]

    def total(self, field_name: str) -> int:
        """Return total observations recorded for a field."""
        bucket = self._counts.get(field_name)
        if bucket is None:
            raise KeyError(f"Field {field_name!r} is not tracked")
        return sum(bucket.values())

    def unique_count(self, field_name: str) -> int:
        """Return the number of distinct values seen for a field."""
        bucket = self._counts.get(field_name)
        if bucket is None:
            raise KeyError(f"Field {field_name!r} is not tracked")
        return len(bucket)

    def reset(self, field_name: Optional[str] = None) -> None:
        """Clear counts for one field or all fields."""
        if field_name is not None:
            if field_name not in self._counts:
                raise KeyError(f"Field {field_name!r} is not tracked")
            self._counts[field_name] = defaultdict(int)
        else:
            self._counts = {f: defaultdict(int) for f in self.fields}

    def summary(self) -> Dict[str, List[Tuple[str, int]]]:
        """Return top-10 values for every tracked field."""
        return {f: self.top(f) for f in self.fields}

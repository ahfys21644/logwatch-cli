"""Label-based filtering for log entries.

Allows entries to be included or excluded based on the presence
or value of arbitrary label fields (e.g. service, host, env).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

LogEntry = Dict[str, object]


@dataclass
class LabelFilter:
    """Filter entries by label key/value pairs.

    Args:
        include: mapping of field -> accepted values.  An entry must
                 match ALL include rules to pass.
        exclude: mapping of field -> rejected values.  An entry is
                 dropped if it matches ANY exclude rule.
    """

    include: Dict[str, List[str]] = field(default_factory=dict)
    exclude: Dict[str, List[str]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Normalise all values to lowercase strings for comparison.
        self.include = {
            k: [str(v).lower() for v in vals]
            for k, vals in self.include.items()
        }
        self.exclude = {
            k: [str(v).lower() for v in vals]
            for k, vals in self.exclude.items()
        }

    def allows(self, entry: LogEntry) -> bool:
        """Return True if the entry passes all label rules."""
        for key, accepted in self.include.items():
            value = str(entry.get(key, "")).lower()
            if value not in accepted:
                return False

        for key, rejected in self.exclude.items():
            value = str(entry.get(key, "")).lower()
            if value in rejected:
                return False

        return True


def build_label_filter(
    include: Optional[Dict[str, List[str]]] = None,
    exclude: Optional[Dict[str, List[str]]] = None,
) -> LabelFilter:
    """Convenience constructor with optional arguments."""
    return LabelFilter(
        include=include or {},
        exclude=exclude or {},
    )


def label_filter_step(lf: LabelFilter) -> Callable[[LogEntry], Optional[LogEntry]]:
    """Return a transformer-compatible step function."""

    def _step(entry: LogEntry) -> Optional[LogEntry]:
        return entry if lf.allows(entry) else None

    return _step

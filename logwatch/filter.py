"""Filter and pattern-matching utilities for structured log entries."""

import re
from typing import Any, Callable, Optional


LEVEL_ORDER = {
    "debug": 0,
    "info": 1,
    "warn": 2,
    "warning": 2,
    "error": 3,
    "critical": 4,
    "fatal": 4,
}


def filter_by_level(entry: dict, min_level: str) -> bool:
    """Return True if entry level meets or exceeds min_level."""
    min_rank = LEVEL_ORDER.get(min_level.lower(), 0)
    entry_level = entry.get("level", "info").lower()
    entry_rank = LEVEL_ORDER.get(entry_level, 1)
    return entry_rank >= min_rank


def filter_by_pattern(entry: dict, pattern: str) -> bool:
    """Return True if any field value in entry matches the regex pattern."""
    compiled = re.compile(pattern, re.IGNORECASE)
    for value in entry.values():
        if compiled.search(str(value)):
            return True
    return False


def filter_by_field(entry: dict, field: str, value: str) -> bool:
    """Return True if entry[field] equals value (case-insensitive)."""
    entry_val = entry.get(field)
    if entry_val is None:
        return False
    return str(entry_val).lower() == value.lower()


def build_filter(
    min_level: Optional[str] = None,
    pattern: Optional[str] = None,
    field: Optional[str] = None,
    field_value: Optional[str] = None,
) -> Callable[[dict], bool]:
    """Compose multiple filters into a single callable."""
    checks: list[Callable[[dict], bool]] = []

    if min_level:
        checks.append(lambda e, lvl=min_level: filter_by_level(e, lvl))
    if pattern:
        checks.append(lambda e, pat=pattern: filter_by_pattern(e, pat))
    if field and field_value is not None:
        checks.append(lambda e, f=field, v=field_value: filter_by_field(e, f, v))

    def combined(entry: dict) -> bool:
        return all(check(entry) for check in checks)

    return combined

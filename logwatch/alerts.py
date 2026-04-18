"""Pattern-based alert system for logwatch-cli."""

import re
from dataclasses import dataclass, field
from typing import Callable, List, Optional

LEVEL_ORDER = ["debug", "info", "warn", "warning", "error", "critical"]


@dataclass
class AlertRule:
    name: str
    pattern: Optional[str] = None
    level_threshold: Optional[str] = None
    field_match: Optional[dict] = None
    _compiled: Optional[re.Pattern] = field(default=None, init=False, repr=False)

    def __post_init__(self):
        if self.pattern:
            self._compiled = re.compile(self.pattern, re.IGNORECASE)

    def matches(self, entry: dict) -> bool:
        if self.pattern:
            message = entry.get("message", "")
            if not self._compiled.search(message):
                return False

        if self.level_threshold:
            entry_level = entry.get("level", "info").lower()
            threshold = self.level_threshold.lower()
            entry_idx = _level_index(entry_level)
            threshold_idx = _level_index(threshold)
            if entry_idx < threshold_idx:
                return False

        if self.field_match:
            for key, value in self.field_match.items():
                if entry.get(key) != value:
                    return False

        return True


def _level_index(level: str) -> int:
    normalized = "warn" if level == "warning" else level
    try:
        return LEVEL_ORDER.index(normalized)
    except ValueError:
        return 1  # default to info index


def check_alerts(entry: dict, rules: List[AlertRule]) -> List[AlertRule]:
    """Return list of rules that match the given log entry."""
    return [rule for rule in rules if rule.matches(entry)]


def build_alert_handler(rules: List[AlertRule], callback: Callable[[dict, AlertRule], None]):
    """Return a function that checks an entry against rules and fires callback."""
    def handler(entry: dict):
        for rule in check_alerts(entry, rules):
            callback(entry, rule)
    return handler

"""Rate limiting for alerts to prevent alert storms."""
from dataclasses import dataclass, field
from time import monotonic
from collections import defaultdict
from typing import Optional


@dataclass
class RateLimiter:
    """Suppress repeated alerts for the same rule within a cooldown window."""
    cooldown_seconds: float = 60.0
    _last_fired: dict = field(default_factory=dict, init=False, repr=False)
    _suppressed_counts: dict = field(default_factory=lambda: defaultdict(int), init=False, repr=False)

    def allow(self, rule_name: str) -> bool:
        """Return True if the alert should fire, False if suppressed."""
        now = monotonic()
        last = self._last_fired.get(rule_name)
        if last is None or (now - last) >= self.cooldown_seconds:
            self._last_fired[rule_name] = now
            return True
        self._suppressed_counts[rule_name] += 1
        return False

    def suppressed_count(self, rule_name: str) -> int:
        """Return how many times the rule was suppressed since last fire."""
        return self._suppressed_counts.get(rule_name, 0)

    def reset(self, rule_name: str) -> None:
        """Manually reset the cooldown for a rule."""
        self._last_fired.pop(rule_name, None)
        self._suppressed_counts.pop(rule_name, None)

    def reset_all(self) -> None:
        self._last_fired.clear()
        self._suppressed_counts.clear()

    def summary(self) -> dict:
        """Return suppression summary keyed by rule name."""
        return {
            name: {
                "suppressed": self._suppressed_counts.get(name, 0),
                "last_fired": self._last_fired.get(name),
            }
            for name in set(list(self._last_fired) + list(self._suppressed_counts))
        }

"""Log entry sampler — keeps 1-in-N entries to reduce volume during high throughput."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class Sampler:
    """Rate-based sampler that passes every Nth entry per level."""
    rate: int = 1  # 1 = keep all, N = keep 1-in-N
    _counters: Dict[str, int] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.rate < 1:
            raise ValueError(f"Sampler rate must be >= 1, got {self.rate}")

    def should_keep(self, entry: dict) -> bool:
        """Return True if this entry should be kept."""
        if self.rate == 1:
            return True
        level = (entry.get("level") or "unknown").lower()
        count = self._counters.get(level, 0) + 1
        self._counters[level] = count
        return count % self.rate == 1

    def reset(self, level: str | None = None) -> None:
        """Reset counter(s). Pass a level string to reset only that level."""
        if level is None:
            self._counters.clear()
        else:
            self._counters.pop(level.lower(), None)

    def stats(self) -> Dict[str, int]:
        """Return a copy of the current counters."""
        return dict(self._counters)


def build_sampler(rate: int = 1) -> Sampler:
    """Factory used by the pipeline / CLI."""
    return Sampler(rate=rate)

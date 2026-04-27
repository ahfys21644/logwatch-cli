"""pattern_counter_middleware.py — pipeline integration for PatternCounter."""
from __future__ import annotations

from typing import Callable, Iterable, Iterator, List, Optional, Tuple

from logwatch.pattern_counter import PatternCounter, PatternCountEvent


AlertCallback = Callable[[PatternCountEvent], None]


def pattern_count_step(
    counters: List[PatternCounter],
    on_alert: Optional[AlertCallback] = None,
) -> Callable[[dict], Optional[dict]]:
    """Return a pipeline step that feeds each entry through all counters.

    The entry is always forwarded; alerts are delivered via *on_alert*.
    """

    def _step(entry: dict) -> Optional[dict]:
        for counter in counters:
            event = counter.feed(entry)
            if event is not None and on_alert is not None:
                on_alert(event)
        return entry

    return _step


def pattern_count_iter(
    entries: Iterable[dict],
    counters: List[PatternCounter],
    on_alert: Optional[AlertCallback] = None,
) -> Iterator[dict]:
    """Iterate *entries*, firing alerts when pattern thresholds are exceeded."""
    step = pattern_count_step(counters, on_alert=on_alert)
    for entry in entries:
        result = step(entry)
        if result is not None:
            yield result


def make_error_pattern_counter(
    pattern: str = r"error|exception|traceback",
    window: float = 30.0,
    threshold: int = 5,
) -> PatternCounter:
    """Convenience factory for a single error-pattern counter."""
    from logwatch.pattern_counter import PatternCounterConfig

    cfg = PatternCounterConfig(
        name="error-pattern",
        pattern=pattern,
        window=window,
        threshold=threshold,
        level_filter="error",
    )
    return PatternCounter(config=cfg)

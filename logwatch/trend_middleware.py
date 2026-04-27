"""Pipeline middleware that feeds entries into TrendDetectors and emits
TrendEvents as formatted alert strings via the output sink."""
from __future__ import annotations

from typing import Callable, Dict, Iterable, Iterator, List, Optional

from logwatch.trend_detector import TrendConfig, TrendDetector, TrendEvent


Entry = Dict  # type alias for log entry dicts


def _ts(entry: Entry) -> Optional[float]:
    """Extract a numeric timestamp from an entry if present."""
    raw = entry.get("timestamp") or entry.get("ts")
    try:
        return float(raw) if raw is not None else None
    except (TypeError, ValueError):
        return None


def trend_step(
    detectors: List[TrendDetector],
    on_event: Callable[[TrendEvent], None],
) -> Callable[[Entry], Optional[Entry]]:
    """Return a pipeline step that records each entry in all detectors."""

    def _step(entry: Entry) -> Optional[Entry]:
        ts = _ts(entry)
        for detector in detectors:
            event = detector.record(ts=ts)
            if event is not None:
                on_event(event)
        return entry

    return _step


def trend_iter(
    entries: Iterable[Entry],
    detectors: List[TrendDetector],
    on_event: Callable[[TrendEvent], None],
) -> Iterator[Entry]:
    """Wrap an iterable of entries, recording each and flushing at the end."""
    step = trend_step(detectors, on_event)
    for entry in entries:
        result = step(entry)
        if result is not None:
            yield result
    # Flush remaining partial buckets
    for detector in detectors:
        event = detector._evaluate()  # noqa: SLF001
        if event is not None:
            on_event(event)


def make_error_trend_detector(
    window: float = 60.0,
    min_periods: int = 3,
    deviation_pct: float = 50.0,
) -> TrendDetector:
    """Convenience factory for a single error-level trend detector."""
    cfg = TrendConfig(
        name="error_trend",
        level="error",
        window=window,
        min_periods=min_periods,
        deviation_pct=deviation_pct,
    )
    return TrendDetector(cfg)

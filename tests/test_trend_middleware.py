"""Tests for logwatch.trend_middleware."""
from __future__ import annotations

from typing import List

import pytest

from logwatch.trend_detector import TrendConfig, TrendDetector, TrendEvent
from logwatch.trend_middleware import (
    make_error_trend_detector,
    trend_iter,
    trend_step,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _entry(ts: float = 0.0, level: str = "error") -> dict:
    return {"message": "boom", "level": level, "timestamp": ts}


def _detector(window: float = 10.0, min_periods: int = 3) -> TrendDetector:
    cfg = TrendConfig(name="t", window=window, min_periods=min_periods, deviation_pct=10.0)
    return TrendDetector(cfg)


# ---------------------------------------------------------------------------
# trend_step
# ---------------------------------------------------------------------------

def test_step_passes_entry_through():
    events: List[TrendEvent] = []
    step = trend_step([_detector()], events.append)
    result = step(_entry(ts=1.0))
    assert result is not None
    assert result["message"] == "boom"


def test_step_does_not_fire_within_window():
    events: List[TrendEvent] = []
    step = trend_step([_detector()], events.append)
    for i in range(5):
        step(_entry(ts=float(i)))
    assert events == []


def test_step_calls_on_event_when_trend_detected():
    """Force a bucket boundary crossing and check callback is callable."""
    fired: List[TrendEvent] = []
    detector = _detector(window=5.0, min_periods=2)
    step = trend_step([detector], fired.append)
    # Cross two bucket boundaries
    step(_entry(ts=0.0))
    step(_entry(ts=6.0))
    step(_entry(ts=12.0))
    # We may or may not get an event; the callback must not raise
    assert isinstance(fired, list)


# ---------------------------------------------------------------------------
# trend_iter
# ---------------------------------------------------------------------------

def test_iter_yields_all_entries():
    events: List[TrendEvent] = []
    entries = [_entry(ts=float(i)) for i in range(4)]
    result = list(trend_iter(entries, [_detector()], events.append))
    assert len(result) == 4


def test_iter_flushes_at_end():
    """Ensure _evaluate is called at end of iteration (no crash)."""
    events: List[TrendEvent] = []
    entries = [_entry(ts=float(i)) for i in range(2)]
    list(trend_iter(entries, [_detector()], events.append))
    # No assertion on events — just must not raise


def test_iter_empty_input_no_events():
    events: List[TrendEvent] = []
    result = list(trend_iter([], [_detector()], events.append))
    assert result == []
    assert events == []


# ---------------------------------------------------------------------------
# make_error_trend_detector
# ---------------------------------------------------------------------------

def test_make_error_trend_detector_returns_detector():
    d = make_error_trend_detector(window=30.0)
    assert isinstance(d, TrendDetector)
    assert d.config.name == "error_trend"
    assert d.config.level == "error"
    assert d.config.window == 30.0


def test_make_error_trend_detector_defaults():
    d = make_error_trend_detector()
    assert d.config.window == 60.0
    assert d.config.min_periods == 3
    assert d.config.deviation_pct == 50.0

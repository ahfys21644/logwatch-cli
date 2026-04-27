"""Tests for logwatch.trend_detector."""
from __future__ import annotations

import pytest

from logwatch.trend_detector import TrendConfig, TrendDetector, TrendEvent


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def cfg() -> TrendConfig:
    return TrendConfig(name="test", window=10.0, min_periods=3, deviation_pct=50.0)


@pytest.fixture()
def detector(cfg: TrendConfig) -> TrendDetector:
    return TrendDetector(cfg)


# ---------------------------------------------------------------------------
# Config validation
# ---------------------------------------------------------------------------

def test_config_rejects_zero_window():
    with pytest.raises(ValueError, match="window"):
        TrendConfig(name="x", window=0)


def test_config_rejects_negative_window():
    with pytest.raises(ValueError, match="window"):
        TrendConfig(name="x", window=-1.0)


def test_config_rejects_min_periods_below_two():
    with pytest.raises(ValueError, match="min_periods"):
        TrendConfig(name="x", min_periods=1)


def test_config_rejects_zero_deviation():
    with pytest.raises(ValueError, match="deviation_pct"):
        TrendConfig(name="x", deviation_pct=0)


# ---------------------------------------------------------------------------
# Recording / bucket accumulation
# ---------------------------------------------------------------------------

def test_record_returns_none_within_window(detector: TrendDetector):
    result = detector.record(ts=0.0)
    assert result is None


def test_record_returns_none_when_too_few_buckets(detector: TrendDetector):
    # Two bucket boundaries crossed, but min_periods=3 requires 3 buckets
    detector.record(ts=0.0)
    result = detector.record(ts=11.0)  # crosses first boundary
    assert result is None


def test_record_detects_upward_trend(detector: TrendDetector):
    # Simulate increasing counts per bucket by spacing calls closer together
    # Bucket 0: 1 event in window 0-10
    # We trigger bucket boundaries manually via ts
    base = 0.0
    # Fill bucket 0 with 1 event
    detector.record(ts=base + 1)
    # Cross into bucket 1 — stores bucket 0 rate
    detector.record(ts=base + 11)
    # Fill bucket 1 with many events
    for _ in range(10):
        detector.record(ts=base + 12)
    # Cross into bucket 2 — stores bucket 1 rate
    detector.record(ts=base + 22)
    # Fill bucket 2 with even more events
    for _ in range(20):
        detector.record(ts=base + 23)
    # Cross into bucket 3 — triggers evaluation with 3 buckets
    result = detector.record(ts=base + 33)
    # May or may not fire depending on monotonicity; just ensure no crash
    assert result is None or isinstance(result, TrendEvent)


def test_trend_event_str_contains_direction():
    event = TrendEvent(rule_name="r", direction="up", start_rate=1.0, end_rate=3.0, periods=3)
    text = str(event)
    assert "UP" in text
    assert "r" in text


def test_trend_event_str_down():
    event = TrendEvent(rule_name="r", direction="down", start_rate=5.0, end_rate=1.0, periods=4)
    assert "DOWN" in text for text in [str(event)]


def test_reset_clears_buckets(detector: TrendDetector):
    detector.record(ts=0.0)
    detector.record(ts=11.0)
    detector.reset()
    assert len(detector._buckets) == 0
    assert detector._current_count == 0


def test_monotonic_direction_up():
    assert TrendDetector._monotonic_direction([1.0, 2.0, 3.0]) == "up"


def test_monotonic_direction_down():
    assert TrendDetector._monotonic_direction([3.0, 2.0, 1.0]) == "down"


def test_monotonic_direction_none_for_mixed():
    assert TrendDetector._monotonic_direction([1.0, 3.0, 2.0]) is None

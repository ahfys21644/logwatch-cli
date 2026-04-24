"""Tests for logwatch.anomaly_detector."""
from __future__ import annotations

import time
from unittest.mock import patch

import pytest

from logwatch.anomaly_detector import AnomalyConfig, AnomalyDetector, AnomalyEvent


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def cfg() -> AnomalyConfig:
    return AnomalyConfig(level="error", window_seconds=10.0, max_count=3, name="test_rule")


@pytest.fixture()
def detector(cfg: AnomalyConfig) -> AnomalyDetector:
    return AnomalyDetector([cfg])


def _entry(level: str = "error") -> dict:
    return {"level": level, "message": "boom"}


# ---------------------------------------------------------------------------
# AnomalyConfig validation
# ---------------------------------------------------------------------------

def test_config_rejects_non_positive_window() -> None:
    with pytest.raises(ValueError, match="window_seconds"):
        AnomalyConfig(level="error", window_seconds=0, max_count=5)


def test_config_rejects_non_positive_max_count() -> None:
    with pytest.raises(ValueError, match="max_count"):
        AnomalyConfig(level="error", window_seconds=10.0, max_count=0)


def test_config_auto_names_when_empty() -> None:
    cfg = AnomalyConfig(level="warn", window_seconds=30.0, max_count=10)
    assert "warn" in cfg.name
    assert "10" in cfg.name


# ---------------------------------------------------------------------------
# AnomalyDetector.feed
# ---------------------------------------------------------------------------

def test_feed_returns_none_below_threshold(detector: AnomalyDetector) -> None:
    for _ in range(3):  # exactly at threshold — not exceeded
        result = detector.feed(_entry())
    assert result is None


def test_feed_returns_event_when_exceeded(detector: AnomalyDetector) -> None:
    for _ in range(4):
        result = detector.feed(_entry())
    assert isinstance(result, AnomalyEvent)


def test_event_carries_correct_level(detector: AnomalyDetector) -> None:
    for _ in range(4):
        ev = detector.feed(_entry("error"))
    assert ev is not None
    assert ev.level == "error"


def test_event_carries_config_name(detector: AnomalyDetector) -> None:
    for _ in range(4):
        ev = detector.feed(_entry())
    assert ev is not None
    assert ev.config_name == "test_rule"


def test_different_level_not_counted(detector: AnomalyDetector) -> None:
    for _ in range(10):
        result = detector.feed(_entry("info"))
    assert result is None


def test_old_entries_expire_from_window(detector: AnomalyDetector) -> None:
    base = 1000.0
    with patch("time.monotonic", return_value=base):
        for _ in range(3):
            detector.feed(_entry())

    # Advance past window; old entries should be purged
    with patch("time.monotonic", return_value=base + 11.0):
        result = detector.feed(_entry())  # only 1 in window now
    assert result is None


def test_reset_clears_buckets(detector: AnomalyDetector) -> None:
    for _ in range(4):
        detector.feed(_entry())
    detector.reset()
    # After reset, counts start fresh
    result = detector.feed(_entry())
    assert result is None


def test_anomaly_event_str_contains_level() -> None:
    ev = AnomalyEvent(config_name="r", level="error", count=5, window_seconds=10.0)
    assert "error" in str(ev)


def test_anomaly_event_str_contains_count() -> None:
    ev = AnomalyEvent(config_name="r", level="error", count=7, window_seconds=10.0)
    assert "7" in str(ev)

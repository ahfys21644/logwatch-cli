"""Tests for logwatch.burst_detector."""
import pytest

from logwatch.burst_detector import BurstConfig, BurstDetector, BurstEvent, build_burst_detectors


@pytest.fixture
def cfg() -> BurstConfig:
    return BurstConfig(name="test_burst", window_seconds=10.0, max_count=3)


@pytest.fixture
def detector(cfg: BurstConfig) -> BurstDetector:
    return BurstDetector(cfg)


def _entry(msg: str = "hello") -> dict:
    return {"message": msg, "level": "info"}


# --- config validation ---

def test_config_rejects_zero_window():
    with pytest.raises(ValueError, match="window_seconds"):
        BurstConfig(name="x", window_seconds=0, max_count=5)


def test_config_rejects_negative_window():
    with pytest.raises(ValueError, match="window_seconds"):
        BurstConfig(name="x", window_seconds=-1.0, max_count=5)


def test_config_rejects_zero_max_count():
    with pytest.raises(ValueError, match="max_count"):
        BurstConfig(name="x", window_seconds=5.0, max_count=0)


# --- feed behaviour ---

def test_feed_returns_none_below_threshold(detector):
    t = 0.0
    for _ in range(3):
        result = detector.feed(_entry(), now=t)
        t += 0.1
    assert result is None


def test_feed_returns_event_on_threshold_exceeded(detector):
    t = 0.0
    event = None
    for _ in range(4):
        event = detector.feed(_entry(), now=t)
        t += 0.1
    assert isinstance(event, BurstEvent)


def test_event_contains_rule_name(detector):
    t = 0.0
    for _ in range(4):
        ev = detector.feed(_entry(), now=t)
        t += 0.1
    assert ev.rule_name == "test_burst"


def test_event_count_reflects_window(detector):
    t = 0.0
    for _ in range(4):
        ev = detector.feed(_entry(), now=t)
        t += 0.1
    assert ev.count == 4


def test_old_entries_purged_outside_window(detector):
    # fill window at t=0..2
    for i in range(3):
        detector.feed(_entry(), now=float(i))
    # advance past window; new entries should not trigger burst
    result = detector.feed(_entry(), now=20.0)
    assert result is None


def test_current_count_reflects_window(detector):
    for i in range(3):
        detector.feed(_entry(), now=float(i))
    assert detector.current_count(now=5.0) == 3
    assert detector.current_count(now=20.0) == 0


def test_reset_clears_timestamps(detector):
    for i in range(3):
        detector.feed(_entry(), now=float(i))
    detector.reset()
    assert detector.current_count(now=5.0) == 0


def test_burst_event_str_contains_rule_name():
    ev = BurstEvent(rule_name="my_rule", count=5, window_seconds=10.0, level="warn")
    assert "my_rule" in str(ev)
    assert "5" in str(ev)


def test_build_burst_detectors_returns_correct_count():
    cfgs = [
        BurstConfig(name="a", window_seconds=5.0, max_count=10),
        BurstConfig(name="b", window_seconds=60.0, max_count=100),
    ]
    detectors = build_burst_detectors(cfgs)
    assert len(detectors) == 2
    assert all(isinstance(d, BurstDetector) for d in detectors)

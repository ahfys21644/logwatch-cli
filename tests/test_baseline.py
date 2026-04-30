"""Tests for logwatch.baseline."""
import pytest
from logwatch.baseline import BaselineConfig, BaselineEvent, BaselineTracker


# ---------------------------------------------------------------------------
# Config validation
# ---------------------------------------------------------------------------

def test_config_rejects_zero_window():
    with pytest.raises(ValueError, match="window_seconds"):
        BaselineConfig(window_seconds=0)


def test_config_rejects_negative_window():
    with pytest.raises(ValueError, match="window_seconds"):
        BaselineConfig(window_seconds=-5)


def test_config_rejects_zero_learn_periods():
    with pytest.raises(ValueError, match="learn_periods"):
        BaselineConfig(learn_periods=0)


def test_config_rejects_zero_deviation_factor():
    with pytest.raises(ValueError, match="deviation_factor"):
        BaselineConfig(deviation_factor=0)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def cfg():
    return BaselineConfig(name="test", window_seconds=10.0, learn_periods=3, deviation_factor=2.0)


@pytest.fixture()
def tracker(cfg):
    return BaselineTracker(cfg)


# ---------------------------------------------------------------------------
# Feeding within a window
# ---------------------------------------------------------------------------

def test_feed_within_window_returns_none(tracker):
    result = tracker.feed(object(), ts=0.0)
    assert result is None


def test_multiple_feeds_within_window_return_none(tracker):
    for i in range(5):
        result = tracker.feed(object(), ts=float(i))
        assert result is None


# ---------------------------------------------------------------------------
# First rotation — no history yet, no event
# ---------------------------------------------------------------------------

def test_first_rotation_no_event(tracker):
    for i in range(5):
        tracker.feed(object(), ts=float(i))
    result = tracker.feed(object(), ts=11.0)  # triggers rotation
    assert result is None


# ---------------------------------------------------------------------------
# Deviation detection
# ---------------------------------------------------------------------------

def test_deviation_returns_event(cfg):
    t = BaselineTracker(cfg)
    # first window: 2 events in 10 s → rate ~0.2/s
    t.feed(object(), ts=0.0)
    t.feed(object(), ts=5.0)
    t.flush(ts=10.0)   # records ~0.2/s into history

    # second window: 2 events → another baseline period
    t.feed(object(), ts=10.0)
    t.feed(object(), ts=15.0)
    t.flush(ts=20.0)   # records ~0.2/s

    # third window: flood — 100 events → rate ~10/s, well above 2x baseline
    for i in range(100):
        t.feed(object(), ts=20.0 + i * 0.05)
    event = t.flush(ts=30.0)

    assert isinstance(event, BaselineEvent)
    assert event.name == "test"
    assert event.factor > cfg.deviation_factor


def test_no_deviation_within_normal_range(cfg):
    """Verify that a rate close to the baseline does not trigger an event."""
    t = BaselineTracker(cfg)
    # Establish two baseline windows at ~2 events per window
    t.feed(object(), ts=0.0)
    t.feed(object(), ts=5.0)
    t.flush(ts=10.0)

    t.feed(object(), ts=10.0)
    t.feed(object(), ts=15.0)
    t.flush(ts=20.0)

    # Third window: same rate — should not trigger a deviation event
    t.feed(object(), ts=20.0)
    t.feed(object(), ts=25.0)
    event = t.flush(ts=30.0)

    assert event is None

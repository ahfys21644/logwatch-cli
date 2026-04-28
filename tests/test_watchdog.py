"""Tests for logwatch.watchdog."""
from __future__ import annotations

import pytest

from logwatch.watchdog import Watchdog, WatchdogConfig, WatchdogEvent


@pytest.fixture
def cfg() -> WatchdogConfig:
    return WatchdogConfig(name="test", silence_window=10.0)


@pytest.fixture
def detector(cfg: WatchdogConfig) -> Watchdog:
    t = [0.0]
    return Watchdog(cfg, clock=lambda: t[0]), t


def test_config_rejects_zero_window():
    with pytest.raises(ValueError):
        WatchdogConfig(name="x", silence_window=0)


def test_config_rejects_negative_window():
    with pytest.raises(ValueError):
        WatchdogConfig(name="x", silence_window=-5.0)


def test_no_event_within_window():
    t = [0.0]
    wd = Watchdog(WatchdogConfig(name="x", silence_window=10.0), clock=lambda: t[0])
    t[0] = 5.0
    assert wd.check() is None


def test_event_fires_after_window():
    t = [0.0]
    wd = Watchdog(WatchdogConfig(name="x", silence_window=10.0), clock=lambda: t[0])
    wd.feed({"level": "info", "message": "hello"})
    t[0] = 15.0
    event = wd.check()
    assert event is not None
    assert event.name == "x"
    assert event.silence_seconds >= 10.0


def test_event_fires_only_once():
    t = [0.0]
    wd = Watchdog(WatchdogConfig(name="x", silence_window=10.0), clock=lambda: t[0])
    wd.feed({"level": "info", "message": "hi"})
    t[0] = 20.0
    assert wd.check() is not None
    assert wd.check() is None  # second call should not re-fire


def test_feed_resets_fired_flag():
    t = [0.0]
    wd = Watchdog(WatchdogConfig(name="x", silence_window=10.0), clock=lambda: t[0])
    wd.feed({"level": "info", "message": "a"})
    t[0] = 20.0
    wd.check()  # fires
    t[0] = 21.0
    wd.feed({"level": "info", "message": "b"})  # resets
    t[0] = 35.0
    assert wd.check() is not None


def test_on_silence_callback_invoked():
    received = []
    t = [0.0]
    cfg = WatchdogConfig(name="x", silence_window=5.0, on_silence=received.append)
    wd = Watchdog(cfg, clock=lambda: t[0])
    wd.feed({"level": "info", "message": "start"})
    t[0] = 10.0
    wd.check()
    assert len(received) == 1
    assert isinstance(received[0], WatchdogEvent)


def test_reset_clears_state():
    t = [0.0]
    wd = Watchdog(WatchdogConfig(name="x", silence_window=5.0), clock=lambda: t[0])
    wd.feed({"level": "info", "message": "x"})
    wd.reset()
    t[0] = 100.0
    # After reset last_seen is None; silence_seconds capped to window
    event = wd.check()
    assert event is not None


def test_watchdog_event_str():
    ev = WatchdogEvent(name="mywatch", silence_seconds=42.5, last_seen=1.0)
    s = str(ev)
    assert "mywatch" in s
    assert "42.5" in s

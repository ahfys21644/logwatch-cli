"""Tests for logwatch/pattern_counter.py."""
from __future__ import annotations

import time
from unittest.mock import patch

import pytest

from logwatch.pattern_counter import (
    PatternCounter,
    PatternCounterConfig,
    PatternCountEvent,
)


@pytest.fixture()
def cfg() -> PatternCounterConfig:
    return PatternCounterConfig(
        name="test",
        pattern=r"fail|error",
        window=10.0,
        threshold=3,
    )


@pytest.fixture()
def counter(cfg: PatternCounterConfig) -> PatternCounter:
    return PatternCounter(config=cfg)


def _entry(msg: str = "an error occurred", level: str = "error") -> dict:
    return {"message": msg, "level": level}


def test_config_rejects_zero_window():
    with pytest.raises(ValueError, match="window"):
        PatternCounterConfig(name="x", pattern="err", window=0, threshold=1)


def test_config_rejects_negative_window():
    with pytest.raises(ValueError, match="window"):
        PatternCounterConfig(name="x", pattern="err", window=-1.0, threshold=1)


def test_config_rejects_zero_threshold():
    with pytest.raises(ValueError, match="threshold"):
        PatternCounterConfig(name="x", pattern="err", window=5.0, threshold=0)


def test_no_match_returns_none(counter):
    assert counter.feed(_entry("all good")) is None


def test_below_threshold_returns_none(counter):
    counter.feed(_entry("fail 1"))
    result = counter.feed(_entry("fail 2"))
    assert result is None


def test_at_threshold_returns_event(counter):
    counter.feed(_entry("fail 1"))
    counter.feed(_entry("fail 2"))
    event = counter.feed(_entry("error 3"))
    assert isinstance(event, PatternCountEvent)
    assert event.count == 3
    assert event.name == "test"


def test_event_str_contains_name(counter):
    counter.feed(_entry("fail"))
    counter.feed(_entry("fail"))
    event = counter.feed(_entry("fail"))
    assert "test" in str(event)
    assert "3" in str(event)


def test_reset_clears_counts(counter):
    counter.feed(_entry("fail"))
    counter.feed(_entry("fail"))
    counter.reset()
    assert counter.current_count == 0


def test_level_filter_blocks_lower_level():
    cfg = PatternCounterConfig(
        name="lvl", pattern="fail", window=10.0, threshold=2, level_filter="error"
    )
    c = PatternCounter(config=cfg)
    c.feed(_entry("fail", level="debug"))
    result = c.feed(_entry("fail", level="info"))
    assert result is None
    assert c.current_count == 0


def test_level_filter_passes_equal_level():
    cfg = PatternCounterConfig(
        name="lvl", pattern="fail", window=10.0, threshold=2, level_filter="error"
    )
    c = PatternCounter(config=cfg)
    c.feed(_entry("fail", level="error"))
    event = c.feed(_entry("fail", level="critical"))
    assert isinstance(event, PatternCountEvent)


def test_expired_entries_not_counted(cfg):
    c = PatternCounter(config=cfg)
    base = 1_000_000.0
    with patch("logwatch.pattern_counter.time.monotonic", return_value=base):
        c.feed(_entry("fail"))
        c.feed(_entry("fail"))
    # advance time past window
    with patch(
        "logwatch.pattern_counter.time.monotonic", return_value=base + 11.0
    ):
        assert c.current_count == 0

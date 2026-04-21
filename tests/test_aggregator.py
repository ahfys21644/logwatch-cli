"""Tests for logwatch.aggregator."""
from __future__ import annotations

from time import monotonic
from unittest.mock import patch

import pytest

from logwatch.aggregator import Aggregator, AggregatorConfig, build_aggregator, _make_summary


@pytest.fixture()
def cfg() -> AggregatorConfig:
    return AggregatorConfig(group_by="level", window_seconds=5.0, min_count=1, label="test")


@pytest.fixture()
def agg(cfg) -> Aggregator:
    return Aggregator(config=cfg)


def _entry(level: str = "INFO", msg: str = "hello") -> dict:
    return {"level": level, "message": msg, "timestamp": "2024-01-01T00:00:00"}


# --- feed / windowing ---

def test_feed_returns_none_within_window(agg):
    result = agg.feed(_entry())
    assert result is None


def test_feed_returns_summaries_after_window(agg):
    future = monotonic() + 100
    with patch("logwatch.aggregator.monotonic", return_value=future):
        result = agg.feed(_entry("ERROR"))
    assert result is not None
    assert len(result) >= 1


def test_flush_empties_buckets(agg):
    agg.feed(_entry("INFO"))
    agg.feed(_entry("ERROR"))
    summaries = agg.flush()
    assert len(summaries) == 2
    # second flush should be empty
    assert agg.flush() == []


def test_flush_respects_min_count():
    cfg = AggregatorConfig(group_by="level", window_seconds=5.0, min_count=3, label="t")
    agg = Aggregator(config=cfg)
    agg.feed(_entry("INFO"))
    agg.feed(_entry("INFO"))
    summaries = agg.flush()
    # only 2 entries, min_count=3 → nothing emitted
    assert summaries == []


def test_reset_discards_data(agg):
    agg.feed(_entry())
    agg.reset()
    assert agg.flush() == []


# --- summary structure ---

def test_summary_contains_count():
    entries = [_entry("WARN"), _entry("WARN")]
    cfg = AggregatorConfig(group_by="level", window_seconds=5.0, min_count=1, label="lbl")
    s = _make_summary("WARN", entries, cfg)
    assert s["aggregated_count"] == 2


def test_summary_highest_level_wins():
    entries = [_entry("INFO"), _entry("ERROR"), _entry("WARN")]
    cfg = AggregatorConfig(group_by="level", window_seconds=5.0, min_count=1, label="lbl")
    s = _make_summary("mixed", entries, cfg)
    assert s["level"] == "ERROR"


def test_summary_label_in_message():
    entries = [_entry()]
    cfg = AggregatorConfig(group_by="level", window_seconds=5.0, min_count=1, label="my-label")
    s = _make_summary("INFO", entries, cfg)
    assert "my-label" in s["message"]


def test_summary_key_in_message():
    entries = [_entry("DEBUG")]
    cfg = AggregatorConfig(group_by="level", window_seconds=5.0, min_count=1, label="t")
    s = _make_summary("DEBUG", entries, cfg)
    assert "DEBUG" in s["message"]


# --- build_aggregator factory ---

def test_build_aggregator_defaults():
    agg = build_aggregator()
    assert agg.config.group_by == "level"
    assert agg.config.window_seconds == 10.0


def test_build_aggregator_custom():
    agg = build_aggregator(group_by="service", window_seconds=30.0, min_count=5, label="svc")
    assert agg.config.group_by == "service"
    assert agg.config.min_count == 5

"""Tests for logwatch.aggregator_middleware."""
from __future__ import annotations

from time import monotonic
from unittest.mock import patch

import pytest

from logwatch.aggregator import build_aggregator
from logwatch.aggregator_middleware import (
    aggregating_iter,
    aggregating_step,
    make_level_aggregator,
)


def _entry(level: str = "INFO", msg: str = "hi") -> dict:
    return {"level": level, "message": msg, "timestamp": "2024-01-01T00:00:00"}


# --- aggregating_step ---

def test_step_forwards_entry_within_window():
    received = []
    agg = build_aggregator(window_seconds=999)
    sink = aggregating_step(agg, received.append)
    sink(_entry())
    assert len(received) == 1
    assert received[0]["message"] == "hi"


def test_step_emits_summary_then_entry_on_window_expiry():
    received = []
    agg = build_aggregator(window_seconds=0.0001, min_count=1)
    sink = aggregating_step(agg, received.append)
    sink(_entry("WARN"))  # primes the bucket

    future = monotonic() + 100
    with patch("logwatch.aggregator.monotonic", return_value=future):
        sink(_entry("ERROR"))

    # at least one summary + the triggering entry
    levels = [e.get("aggregated_label") for e in received]
    assert any(l == "aggregated" for l in levels)


# --- aggregating_iter ---

def test_iter_yields_all_entries():
    agg = build_aggregator(window_seconds=999)
    entries = [_entry("INFO"), _entry("WARN"), _entry("ERROR")]
    result = list(aggregating_iter(agg, entries))
    non_summary = [e for e in result if "aggregated_count" not in e]
    assert len(non_summary) == 3


def test_iter_flushes_at_end():
    agg = build_aggregator(window_seconds=999, min_count=1)
    entries = [_entry("INFO"), _entry("ERROR")]
    result = list(aggregating_iter(agg, entries))
    summaries = [e for e in result if "aggregated_count" in e]
    # final flush should produce summaries for INFO and ERROR
    assert len(summaries) >= 2


def test_iter_empty_input_produces_no_output():
    agg = build_aggregator(window_seconds=999, min_count=1)
    result = list(aggregating_iter(agg, []))
    # flush on empty buckets → nothing
    assert result == []


# --- make_level_aggregator ---

def test_make_level_aggregator_group_by_level():
    agg = make_level_aggregator()
    assert agg.config.group_by == "level"


def test_make_level_aggregator_custom_window():
    agg = make_level_aggregator(window_seconds=60.0)
    assert agg.config.window_seconds == 60.0


def test_make_level_aggregator_label():
    agg = make_level_aggregator()
    assert agg.config.label == "level-summary"

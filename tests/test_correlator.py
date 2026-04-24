"""Tests for logwatch.correlator."""
from __future__ import annotations

import time
from unittest.mock import patch

import pytest

from logwatch.correlator import Correlator, CorrelatorConfig, build_correlator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _entry(request_id: str, message: str = "msg", level: str = "INFO") -> dict:
    return {"message": message, "level": level, "request_id": request_id}


@pytest.fixture
def correlator() -> Correlator:
    return build_correlator(group_by="request_id", window_seconds=2.0, min_group_size=2)


# ---------------------------------------------------------------------------
# CorrelatorConfig validation
# ---------------------------------------------------------------------------

def test_config_rejects_non_positive_window():
    with pytest.raises(ValueError, match="window_seconds"):
        CorrelatorConfig(group_by="id", window_seconds=0)


def test_config_rejects_zero_min_group_size():
    with pytest.raises(ValueError, match="min_group_size"):
        CorrelatorConfig(group_by="id", min_group_size=0)


# ---------------------------------------------------------------------------
# feed — within window
# ---------------------------------------------------------------------------

def test_feed_returns_none_within_window(correlator):
    assert correlator.feed(_entry("abc")) is None


def test_feed_second_entry_within_window_returns_none(correlator):
    correlator.feed(_entry("abc"))
    assert correlator.feed(_entry("abc", "second")) is None


# ---------------------------------------------------------------------------
# feed — window expires
# ---------------------------------------------------------------------------

def test_feed_returns_group_after_window_expires(correlator):
    t0 = 1000.0
    with patch("logwatch.correlator.time.monotonic", side_effect=[t0, t0 + 0.5, t0 + 2.1]):
        correlator.feed(_entry("req1"))
        correlator.feed(_entry("req1", "second"))
        result = correlator.feed(_entry("req1", "third"))
    assert result is not None
    assert len(result) == 2  # the two entries present when window closed


def test_group_below_min_size_not_returned():
    corr = build_correlator(group_by="request_id", window_seconds=1.0, min_group_size=3)
    t0 = 500.0
    with patch("logwatch.correlator.time.monotonic", side_effect=[t0, t0 + 1.5]):
        corr.feed(_entry("x"))
        result = corr.feed(_entry("x", "second"))
    assert result is None


# ---------------------------------------------------------------------------
# label applied
# ---------------------------------------------------------------------------

def test_group_entries_are_labelled(correlator):
    t0 = 100.0
    with patch("logwatch.correlator.time.monotonic", side_effect=[t0, t0 + 0.1, t0 + 2.5]):
        correlator.feed(_entry("r"))
        correlator.feed(_entry("r", "two"))
        group = correlator.feed(_entry("r", "three"))
    assert group is not None
    for entry in group:
        assert "correlated" in entry["labels"]


# ---------------------------------------------------------------------------
# flush
# ---------------------------------------------------------------------------

def test_flush_returns_qualifying_groups(correlator):
    correlator.feed(_entry("g1"))
    correlator.feed(_entry("g1", "second"))
    groups = correlator.flush()
    assert len(groups) == 1
    assert len(groups[0]) == 2


def test_flush_clears_internal_state(correlator):
    correlator.feed(_entry("g2"))
    correlator.feed(_entry("g2", "b"))
    correlator.flush()
    assert correlator.flush() == []


def test_flush_ignores_undersized_groups():
    corr = build_correlator(group_by="request_id", window_seconds=10.0, min_group_size=3)
    corr.feed(_entry("only_one"))
    assert corr.flush() == []


# ---------------------------------------------------------------------------
# entries missing the group_by field
# ---------------------------------------------------------------------------

def test_entry_missing_key_returns_none(correlator):
    entry = {"message": "no id", "level": "INFO"}
    assert correlator.feed(entry) is None

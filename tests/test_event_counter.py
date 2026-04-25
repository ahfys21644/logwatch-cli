"""Tests for logwatch.event_counter and logwatch.event_counter_config."""
from __future__ import annotations

from time import monotonic
from unittest.mock import patch

import pytest

from logwatch.event_counter import EventCounter, EventCounterConfig
from logwatch.event_counter_config import (
    build_counters,
    default_event_counter_config,
    load_event_counter_from_dict,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def cfg() -> EventCounterConfig:
    return EventCounterConfig(field="service", window=30.0, top_n=3)


@pytest.fixture()
def counter(cfg: EventCounterConfig) -> EventCounter:
    return EventCounter(config=cfg)


def _entry(service: str = "web", level: str = "info") -> dict:
    return {"service": service, "level": level, "message": "ok"}


# ---------------------------------------------------------------------------
# Config validation
# ---------------------------------------------------------------------------

def test_config_rejects_empty_field() -> None:
    with pytest.raises(ValueError, match="field"):
        EventCounterConfig(field="")


def test_config_rejects_zero_window() -> None:
    with pytest.raises(ValueError, match="window"):
        EventCounterConfig(field="level", window=0)


def test_config_rejects_negative_top_n() -> None:
    with pytest.raises(ValueError, match="top_n"):
        EventCounterConfig(field="level", top_n=0)


# ---------------------------------------------------------------------------
# Recording
# ---------------------------------------------------------------------------

def test_record_increments_count(counter: EventCounter) -> None:
    counter.record(_entry("web"))
    assert counter.count_for("web") == 1


def test_record_multiple_values(counter: EventCounter) -> None:
    counter.record(_entry("web"))
    counter.record(_entry("api"))
    counter.record(_entry("web"))
    assert counter.count_for("web") == 2
    assert counter.count_for("api") == 1


def test_record_missing_field_ignored(counter: EventCounter) -> None:
    counter.record({"level": "info", "message": "no service"})
    assert counter.total() == 0


def test_record_all_processes_list(counter: EventCounter) -> None:
    entries = [_entry("web"), _entry("db"), _entry("web")]
    counter.record_all(entries)
    assert counter.total() == 3


# ---------------------------------------------------------------------------
# Top-N
# ---------------------------------------------------------------------------

def test_top_returns_sorted_desc(counter: EventCounter) -> None:
    counter.record_all([_entry("web")] * 5 + [_entry("db")] * 2 + [_entry("api")] * 8)
    top = counter.top()
    assert top[0] == ("api", 8)
    assert top[1] == ("web", 5)


def test_top_respects_n_override(counter: EventCounter) -> None:
    counter.record_all([_entry("a"), _entry("b"), _entry("c")])
    assert len(counter.top(n=2)) == 2


# ---------------------------------------------------------------------------
# Window reset
# ---------------------------------------------------------------------------

def test_window_reset_clears_counts(counter: EventCounter) -> None:
    counter.record(_entry("web"))
    # Advance monotonic clock beyond window
    with patch("logwatch.event_counter.monotonic", return_value=monotonic() + 31):
        counter.record(_entry("api"))
    assert counter.count_for("web") == 0
    assert counter.count_for("api") == 1


def test_manual_reset_clears_counts(counter: EventCounter) -> None:
    counter.record(_entry("web"))
    counter.reset()
    assert counter.total() == 0


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def test_summary_contains_field(counter: EventCounter) -> None:
    assert counter.summary()["field"] == "service"


def test_summary_contains_total(counter: EventCounter) -> None:
    counter.record(_entry("web"))
    assert counter.summary()["total"] == 1


# ---------------------------------------------------------------------------
# Config loader
# ---------------------------------------------------------------------------

def test_load_from_dict_sets_field() -> None:
    cfg = load_event_counter_from_dict({"field": "host", "window": 120, "top_n": 5})
    assert cfg.field == "host"


def test_load_from_dict_missing_field_raises() -> None:
    with pytest.raises(ValueError):
        load_event_counter_from_dict({"window": 60})


def test_default_config_field_is_level() -> None:
    cfg = default_event_counter_config()
    assert cfg.field == "level"


def test_build_counters_returns_correct_count() -> None:
    cfgs = [EventCounterConfig(field="level"), EventCounterConfig(field="host")]
    counters = build_counters(cfgs)
    assert len(counters) == 2
    assert all(isinstance(c, EventCounter) for c in counters)

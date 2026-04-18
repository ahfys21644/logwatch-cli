"""Tests for logwatch.stats.SessionStats."""
import pytest
from logwatch.stats import SessionStats


@pytest.fixture
def stats():
    return SessionStats()


def _entry(level="INFO", msg="hello"):
    return {"level": level, "message": msg, "timestamp": "2024-01-01T00:00:00"}


def test_record_entry_increments_total(stats):
    stats.record_entry(_entry())
    assert stats.total == 1


def test_record_entry_tracks_level(stats):
    stats.record_entry(_entry("ERROR"))
    assert stats.by_level["ERROR"] == 1


def test_record_entry_case_normalised(stats):
    stats.record_entry(_entry("warning"))
    assert stats.by_level["WARNING"] == 1


def test_multiple_entries(stats):
    for _ in range(3):
        stats.record_entry(_entry("INFO"))
    stats.record_entry(_entry("ERROR"))
    assert stats.total == 4
    assert stats.by_level["INFO"] == 3
    assert stats.by_level["ERROR"] == 1


def test_record_alert(stats):
    stats.record_alert("high-error-rate")
    stats.record_alert("high-error-rate")
    assert stats.alerts_fired == 2
    assert stats.alert_names["high-error-rate"] == 2


def test_summary_contains_total(stats):
    stats.record_entry(_entry())
    s = stats.summary()
    assert s["total"] == 1


def test_summary_top_alerts(stats):
    stats.record_alert("rule-a")
    stats.record_alert("rule-a")
    stats.record_alert("rule-b")
    s = stats.summary()
    assert s["top_alerts"][0] == ("rule-a", 2)


def test_format_summary_contains_total(stats):
    stats.record_entry(_entry("ERROR"))
    out = stats.format_summary()
    assert "Total entries" in out
    assert "1" in out


def test_format_summary_shows_level(stats):
    stats.record_entry(_entry("CRITICAL"))
    out = stats.format_summary()
    assert "CRITICAL" in out


def test_format_summary_no_zero_levels(stats):
    stats.record_entry(_entry("INFO"))
    out = stats.format_summary()
    assert "DEBUG" not in out

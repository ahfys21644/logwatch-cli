"""Tests for logwatch.dedup."""

import time
import pytest
from logwatch.dedup import DedupFilter, _entry_key


@pytest.fixture
def dedup():
    return DedupFilter(window_seconds=2.0)


def _entry(msg="hello", level="info"):
    return {"message": msg, "level": level}


# --- _entry_key ---

def test_entry_key_same_content_equal():
    assert _entry_key(_entry()) == _entry_key(_entry())


def test_entry_key_different_message_differs():
    assert _entry_key(_entry("a")) != _entry_key(_entry("b"))


def test_entry_key_different_level_differs():
    assert _entry_key(_entry(level="info")) != _entry_key(_entry(level="error"))


# --- is_duplicate ---

def test_first_occurrence_not_duplicate(dedup):
    assert dedup.is_duplicate(_entry()) is False


def test_second_occurrence_within_window_is_duplicate(dedup):
    dedup.is_duplicate(_entry())
    assert dedup.is_duplicate(_entry()) is True


def test_different_message_not_duplicate(dedup):
    dedup.is_duplicate(_entry("x"))
    assert dedup.is_duplicate(_entry("y")) is False


def test_entry_allowed_after_window_expires(dedup):
    dedup.window_seconds = 0.05
    dedup.is_duplicate(_entry())
    time.sleep(0.1)
    assert dedup.is_duplicate(_entry()) is False


# --- filter ---

def test_filter_returns_entry_first_time(dedup):
    e = _entry()
    assert dedup.filter(e) is e


def test_filter_returns_none_on_duplicate(dedup):
    e = _entry()
    dedup.filter(e)
    assert dedup.filter(e) is None


# --- purge_expired ---

def test_purge_removes_expired_entries(dedup):
    dedup.window_seconds = 0.05
    dedup.is_duplicate(_entry("a"))
    dedup.is_duplicate(_entry("b"))
    time.sleep(0.1)
    removed = dedup.purge_expired()
    assert removed == 2
    assert len(dedup._seen) == 0


def test_purge_keeps_fresh_entries(dedup):
    dedup.is_duplicate(_entry("a"))
    removed = dedup.purge_expired()
    assert removed == 0


# --- reset ---

def test_reset_clears_all(dedup):
    dedup.is_duplicate(_entry())
    dedup.reset()
    assert dedup.is_duplicate(_entry()) is False

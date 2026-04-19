"""Tests for logwatch.context_buffer."""
import pytest
from logwatch.context_buffer import ContextBuffer


def _entry(msg: str, level: str = "info") -> dict:
    return {"message": msg, "level": level, "timestamp": "2024-01-01T00:00:00"}


def is_error(entry: dict) -> bool:
    return entry.get("level") == "error"


@pytest.fixture()
def buf() -> ContextBuffer:
    return ContextBuffer(before=2, after=2)


def test_match_is_labelled(buf):
    entries = [_entry("boom", "error")]
    results = list(buf.feed(entries, is_error))
    assert len(results) == 1
    assert results[0]["_context"] == "match"


def test_before_context_included(buf):
    entries = [_entry("a"), _entry("b"), _entry("boom", "error")]
    results = list(buf.feed(entries, is_error))
    roles = [r["_context"] for r in results]
    assert roles == ["before", "before", "match"]


def test_after_context_included(buf):
    entries = [_entry("boom", "error"), _entry("c"), _entry("d"), _entry("e")]
    results = list(buf.feed(entries, is_error))
    roles = [r["_context"] for r in results]
    assert roles == ["match", "after", "after"]


def test_before_capped_at_window(buf):
    entries = [_entry(str(i)) for i in range(5)] + [_entry("boom", "error")]
    results = list(buf.feed(entries, is_error))
    before = [r for r in results if r["_context"] == "before"]
    assert len(before) == 2
    assert before[0]["message"] == "3"
    assert before[1]["message"] == "4"


def test_no_duplicate_entries_in_overlapping_windows():
    buf = ContextBuffer(before=2, after=2)
    entries = [
        _entry("a"),
        _entry("err1", "error"),
        _entry("between"),
        _entry("err2", "error"),
        _entry("z"),
    ]
    results = list(buf.feed(entries, is_error))
    messages = [r["message"] for r in results]
    # 'between' appears as after of err1 AND before of err2 — should appear once
    assert messages.count("between") == 1


def test_no_match_yields_nothing(buf):
    entries = [_entry("x"), _entry("y")]
    results = list(buf.feed(entries, is_error))
    assert results == []


def test_zero_context_only_yields_match():
    buf = ContextBuffer(before=0, after=0)
    entries = [_entry("pre"), _entry("boom", "error"), _entry("post")]
    results = list(buf.feed(entries, is_error))
    assert len(results) == 1
    assert results[0]["_context"] == "match"


def test_reset_clears_pre_buffer(buf):
    pre_entries = [_entry("a"), _entry("b")]
    for e in pre_entries:
        list(buf.feed([e], is_error))  # feed without match to fill pre-buffer
    buf.reset()
    results = list(buf.feed([_entry("boom", "error")], is_error))
    before = [r for r in results if r["_context"] == "before"]
    assert before == []

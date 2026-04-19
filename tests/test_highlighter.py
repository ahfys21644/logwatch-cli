"""Tests for logwatch.highlighter."""
import pytest
from logwatch.highlighter import Highlighter, build_highlighter, ANSI_RESET


@pytest.fixture()
def hl() -> Highlighter:
    return Highlighter(patterns=["error", "warn"])


def test_no_patterns_returns_text_unchanged():
    h = Highlighter()
    assert h.highlight("hello world") == "hello world"


def test_single_pattern_wraps_match(hl):
    result = hl.highlight("an error occurred")
    assert "error" in result
    assert ANSI_RESET in result


def test_match_is_case_insensitive_by_default(hl):
    result = hl.highlight("An ERROR occurred")
    assert ANSI_RESET in result


def test_case_sensitive_misses_uppercase():
    h = Highlighter(patterns=["error"], case_sensitive=True)
    result = h.highlight("An ERROR occurred")
    assert ANSI_RESET not in result


def test_case_sensitive_matches_exact():
    h = Highlighter(patterns=["error"], case_sensitive=True)
    result = h.highlight("an error occurred")
    assert ANSI_RESET in result


def test_multiple_patterns_both_highlighted(hl):
    result = hl.highlight("warn: error detected")
    assert result.count(ANSI_RESET) >= 2


def test_no_match_leaves_text_unchanged(hl):
    text = "everything is fine"
    assert hl.highlight(text) == text


def test_highlight_field_stringifies_value(hl):
    result = hl.highlight_field(404)
    assert isinstance(result, str)


def test_any_match_true(hl):
    assert hl.any_match("a warning appeared") is True


def test_any_match_false(hl):
    assert hl.any_match("everything is fine") is False


def test_build_highlighter_returns_instance():
    h = build_highlighter(patterns=["foo"])
    assert isinstance(h, Highlighter)
    assert h.any_match("foobar") is True


def test_build_highlighter_empty_patterns():
    h = build_highlighter()
    assert h.highlight("text") == "text"

"""Tests for logwatch.formatter."""

import pytest
from logwatch.formatter import format_entry, format_alert, colorize_level


@pytest.fixture
def basic_entry():
    return {"level": "info", "message": "server started", "timestamp": "2024-01-01T00:00:00Z"}


@pytest.fixture
def rich_entry():
    return {"level": "error", "message": "connection failed", "host": "db01", "code": 500}


def test_format_entry_contains_message(basic_entry):
    result = format_entry(basic_entry, color=False)
    assert "server started" in result


def test_format_entry_contains_level(basic_entry):
    result = format_entry(basic_entry, color=False)
    assert "INFO" in result


def test_format_entry_contains_timestamp(basic_entry):
    result = format_entry(basic_entry, color=False)
    assert "2024-01-01T00:00:00Z" in result


def test_format_entry_shows_extra_fields(rich_entry):
    result = format_entry(rich_entry, color=False, show_fields=True)
    assert "host=db01" in result
    assert "code=500" in result


def test_format_entry_hides_extra_fields_when_disabled(rich_entry):
    result = format_entry(rich_entry, color=False, show_fields=False)
    assert "host" not in result


def test_format_entry_skips_missing_timestamp():
    entry = {"level": "debug", "message": "ping"}
    result = format_entry(entry, color=False)
    assert "DEBUG" in result
    assert "ping" in result


def test_format_entry_with_color_contains_ansi(basic_entry):
    result = format_entry(basic_entry, color=True)
    assert "\033[" in result


def test_format_entry_no_color_no_ansi(basic_entry):
    result = format_entry(basic_entry, color=False)
    assert "\033[" not in result


def test_colorize_level_error_is_red():
    result = colorize_level("error")
    assert "\033[31m" in result


def test_colorize_level_unknown_no_crash():
    result = colorize_level("unknown")
    assert "UNKNOWN" in result


def test_format_alert_contains_rule_name(basic_entry):
    result = format_alert("high-error-rate", basic_entry, color=False)
    assert "high-error-rate" in result


def test_format_alert_contains_message(basic_entry):
    result = format_alert("my-rule", basic_entry, color=False)
    assert "server started" in result

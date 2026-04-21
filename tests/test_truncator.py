"""Tests for logwatch.truncator."""

from __future__ import annotations

import pytest

from logwatch.truncator import Truncator, build_truncator


@pytest.fixture()
def truncator() -> Truncator:
    return Truncator(max_message_length=20, max_field_length=10)


@pytest.fixture()
def _entry() -> dict:
    return {
        "timestamp": "2024-01-01T00:00:00Z",
        "level": "INFO",
        "message": "This is a fairly long message that exceeds the limit",
        "service": "auth-service-with-a-long-name",
        "code": 200,
    }


# --- truncate_value ---

def test_short_value_unchanged(truncator):
    assert truncator.truncate_value("hello", 20) == "hello"


def test_exact_length_unchanged(truncator):
    s = "a" * 20
    assert truncator.truncate_value(s, 20) == s


def test_long_value_truncated_with_ellipsis(truncator):
    result = truncator.truncate_value("a" * 30, 20)
    assert result.endswith("...")
    assert len(result) == 20


def test_truncated_value_length_respected(truncator):
    result = truncator.truncate_value("x" * 100, 10)
    assert len(result) <= 10


# --- truncate_entry ---

def test_message_truncated(_entry, truncator):
    result = truncator.truncate_entry(_entry)
    assert len(result["message"]) <= 20
    assert result["message"].endswith("...")


def test_field_truncated(_entry, truncator):
    result = truncator.truncate_entry(_entry)
    assert len(result["service"]) <= 10
    assert result["service"].endswith("...")


def test_short_field_unchanged(_entry, truncator):
    result = truncator.truncate_entry(_entry)
    assert result["level"] == "INFO"


def test_non_string_field_unchanged(_entry, truncator):
    result = truncator.truncate_entry(_entry)
    assert result["code"] == 200


def test_original_entry_not_mutated(_entry, truncator):
    original_msg = _entry["message"]
    truncator.truncate_entry(_entry)
    assert _entry["message"] == original_msg


# --- fields_to_skip ---

def test_skipped_field_not_truncated(_entry):
    t = Truncator(max_message_length=20, max_field_length=10, fields_to_skip=["service"])
    result = t.truncate_entry(_entry)
    assert result["service"] == _entry["service"]


def test_skipped_message_not_truncated(_entry):
    t = Truncator(max_message_length=5, max_field_length=5, fields_to_skip=["message"])
    result = t.truncate_entry(_entry)
    assert result["message"] == _entry["message"]


# --- validation ---

def test_invalid_max_message_raises():
    with pytest.raises(ValueError, match="max_message_length"):
        Truncator(max_message_length=0)


def test_invalid_max_field_raises():
    with pytest.raises(ValueError, match="max_field_length"):
        Truncator(max_field_length=-1)


# --- build_truncator ---

def test_build_truncator_defaults():
    t = build_truncator()
    assert t.max_message_length == 200
    assert t.max_field_length == 120
    assert t.fields_to_skip == []


def test_build_truncator_custom():
    t = build_truncator(max_message=50, max_field=30, skip=["token"])
    assert t.max_message_length == 50
    assert t.fields_to_skip == ["token"]

"""Tests for logwatch.field_mapper."""

import pytest
from logwatch.field_mapper import FieldMapper, build_field_mapper, map_entry


@pytest.fixture()
def base_entry() -> dict:
    return {
        "timestamp": "2024-01-01T00:00:00Z",
        "level": "INFO",
        "message": "hello world",
        "request_id": "abc-123",
        "secret": "s3cr3t",
    }


# --- rename ---

def test_rename_changes_key(base_entry):
    mapper = build_field_mapper(rename={"request_id": "req_id"})
    result = mapper.apply(base_entry)
    assert "req_id" in result
    assert "request_id" not in result


def test_rename_preserves_value(base_entry):
    mapper = build_field_mapper(rename={"request_id": "req_id"})
    result = mapper.apply(base_entry)
    assert result["req_id"] == "abc-123"


def test_rename_is_case_insensitive(base_entry):
    mapper = build_field_mapper(rename={"REQUEST_ID": "req_id"})
    result = mapper.apply(base_entry)
    assert "req_id" in result


def test_rename_unknown_key_leaves_entry_unchanged(base_entry):
    mapper = build_field_mapper(rename={"nonexistent": "other"})
    result = mapper.apply(base_entry)
    assert set(result.keys()) == set(base_entry.keys())


def test_rename_multiple_fields(base_entry):
    mapper = build_field_mapper(rename={"level": "severity", "message": "msg"})
    result = mapper.apply(base_entry)
    assert "severity" in result
    assert "msg" in result
    assert "level" not in result
    assert "message" not in result


# --- drop ---

def test_drop_removes_field(base_entry):
    mapper = build_field_mapper(drop=["secret"])
    result = mapper.apply(base_entry)
    assert "secret" not in result


def test_drop_is_case_insensitive(base_entry):
    mapper = build_field_mapper(drop=["SECRET"])
    result = mapper.apply(base_entry)
    assert "secret" not in result


def test_drop_unknown_field_is_safe(base_entry):
    mapper = build_field_mapper(drop=["nonexistent"])
    result = mapper.apply(base_entry)
    assert set(result.keys()) == set(base_entry.keys())


def test_drop_multiple_fields(base_entry):
    mapper = build_field_mapper(drop=["secret", "request_id"])
    result = mapper.apply(base_entry)
    assert "secret" not in result
    assert "request_id" not in result


# --- combined ---

def test_rename_then_drop_order(base_entry):
    """Rename happens before drop; dropping the *new* name should work."""
    mapper = build_field_mapper(rename={"secret": "token"}, drop=["token"])
    result = mapper.apply(base_entry)
    assert "secret" not in result
    assert "token" not in result


def test_apply_does_not_mutate_original(base_entry):
    original_keys = set(base_entry.keys())
    mapper = build_field_mapper(rename={"level": "severity"}, drop=["secret"])
    mapper.apply(base_entry)
    assert set(base_entry.keys()) == original_keys


# --- map_entry helper ---

def test_map_entry_convenience(base_entry):
    mapper = build_field_mapper(drop=["secret"])
    result = map_entry(base_entry, mapper)
    assert "secret" not in result
    assert result["message"] == base_entry["message"]

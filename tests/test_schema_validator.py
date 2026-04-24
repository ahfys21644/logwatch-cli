"""Tests for logwatch.schema_validator."""
from __future__ import annotations

import pytest

from logwatch.schema_validator import (
    FieldSchema,
    SchemaValidator,
    build_schema_validator,
    validation_step,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def base_entry():
    return {"level": "error", "message": "boom", "ts": "2024-01-01T00:00:00Z"}


@pytest.fixture()
def validator():
    return SchemaValidator(
        schemas=[
            FieldSchema(name="level", required=True),
            FieldSchema(name="message", required=True),
            FieldSchema(name="code", expected_type=int),
            FieldSchema(name="request_id", pattern=r"^req-[0-9a-f]+$"),
        ],
        on_invalid="drop",
    )


# ---------------------------------------------------------------------------
# FieldSchema.validate
# ---------------------------------------------------------------------------


def test_required_field_present_no_error(base_entry):
    schema = FieldSchema(name="level", required=True)
    assert schema.validate(base_entry) == []


def test_required_field_missing_returns_error():
    schema = FieldSchema(name="level", required=True)
    assert schema.validate({}) != []


def test_optional_field_missing_no_error():
    schema = FieldSchema(name="code", required=False, expected_type=int)
    assert schema.validate({}) == []


def test_type_mismatch_returns_error(base_entry):
    schema = FieldSchema(name="level", expected_type=int)
    errors = schema.validate(base_entry)
    assert any("expected int" in e for e in errors)


def test_type_match_no_error():
    schema = FieldSchema(name="code", expected_type=int)
    assert schema.validate({"code": 42}) == []


def test_pattern_match_no_error():
    schema = FieldSchema(name="request_id", pattern=r"^req-[0-9a-f]+$")
    assert schema.validate({"request_id": "req-deadbeef"}) == []


def test_pattern_mismatch_returns_error():
    schema = FieldSchema(name="request_id", pattern=r"^req-[0-9a-f]+$")
    errors = schema.validate({"request_id": "bad-id"})
    assert errors
    assert "request_id" in errors[0]


# ---------------------------------------------------------------------------
# SchemaValidator.apply — on_invalid policies
# ---------------------------------------------------------------------------


def test_valid_entry_passes(validator, base_entry):
    assert validator.apply(base_entry) is base_entry


def test_drop_policy_returns_none_on_invalid(base_entry):
    v = SchemaValidator(
        schemas=[FieldSchema(name="missing_field", required=True)],
        on_invalid="drop",
    )
    assert v.apply(base_entry) is None


def test_tag_policy_adds_invalid_field(base_entry):
    v = SchemaValidator(
        schemas=[FieldSchema(name="missing_field", required=True)],
        on_invalid="tag",
    )
    result = v.apply(base_entry)
    assert result is not None
    assert "_invalid" in result
    assert isinstance(result["_invalid"], list)


def test_tag_policy_does_not_mutate_original(base_entry):
    v = SchemaValidator(
        schemas=[FieldSchema(name="missing_field", required=True)],
        on_invalid="tag",
    )
    v.apply(base_entry)
    assert "_invalid" not in base_entry


def test_pass_policy_returns_entry_unchanged(base_entry):
    v = SchemaValidator(
        schemas=[FieldSchema(name="missing_field", required=True)],
        on_invalid="pass",
    )
    assert v.apply(base_entry) is base_entry


# ---------------------------------------------------------------------------
# validation_step helper
# ---------------------------------------------------------------------------


def test_validation_step_passes_valid(validator, base_entry):
    step = validation_step(validator)
    assert step(base_entry) is not None


def test_validation_step_drops_invalid():
    v = SchemaValidator(
        schemas=[FieldSchema(name="level", required=True)],
        on_invalid="drop",
    )
    step = validation_step(v)
    assert step({"message": "no level here"}) is None

"""Tests for logwatch.label_filter."""
import pytest

from logwatch.label_filter import (
    LabelFilter,
    build_label_filter,
    label_filter_step,
)


@pytest.fixture()
def entry():
    return {
        "message": "hello",
        "level": "info",
        "service": "auth",
        "env": "production",
        "host": "web-01",
    }


# ---------------------------------------------------------------------------
# LabelFilter.allows — include rules
# ---------------------------------------------------------------------------

def test_include_matching_value_passes(entry):
    lf = build_label_filter(include={"service": ["auth"]})
    assert lf.allows(entry) is True


def test_include_non_matching_value_blocked(entry):
    lf = build_label_filter(include={"service": ["payments"]})
    assert lf.allows(entry) is False


def test_include_multiple_values_any_match_passes(entry):
    lf = build_label_filter(include={"service": ["payments", "auth"]})
    assert lf.allows(entry) is True


def test_include_multiple_keys_all_must_match(entry):
    lf = build_label_filter(include={"service": ["auth"], "env": ["staging"]})
    assert lf.allows(entry) is False


def test_include_missing_field_blocks_entry(entry):
    lf = build_label_filter(include={"region": ["eu-west"]})
    assert lf.allows(entry) is False


def test_include_match_is_case_insensitive(entry):
    entry["service"] = "Auth"
    lf = build_label_filter(include={"service": ["auth"]})
    assert lf.allows(entry) is True


# ---------------------------------------------------------------------------
# LabelFilter.allows — exclude rules
# ---------------------------------------------------------------------------

def test_exclude_matching_value_blocked(entry):
    lf = build_label_filter(exclude={"env": ["production"]})
    assert lf.allows(entry) is False


def test_exclude_non_matching_value_passes(entry):
    lf = build_label_filter(exclude={"env": ["staging"]})
    assert lf.allows(entry) is True


def test_exclude_missing_field_passes(entry):
    lf = build_label_filter(exclude={"region": ["us-east"]})
    assert lf.allows(entry) is True


def test_exclude_match_is_case_insensitive(entry):
    entry["env"] = "PRODUCTION"
    lf = build_label_filter(exclude={"env": ["production"]})
    assert lf.allows(entry) is False


# ---------------------------------------------------------------------------
# Combined include + exclude
# ---------------------------------------------------------------------------

def test_include_and_exclude_both_satisfied_passes(entry):
    lf = build_label_filter(
        include={"service": ["auth"]},
        exclude={"env": ["staging"]},
    )
    assert lf.allows(entry) is True


def test_include_passes_but_exclude_blocks(entry):
    lf = build_label_filter(
        include={"service": ["auth"]},
        exclude={"env": ["production"]},
    )
    assert lf.allows(entry) is False


# ---------------------------------------------------------------------------
# label_filter_step
# ---------------------------------------------------------------------------

def test_step_returns_entry_when_allowed(entry):
    step = label_filter_step(build_label_filter(include={"service": ["auth"]}))
    assert step(entry) is entry


def test_step_returns_none_when_blocked(entry):
    step = label_filter_step(build_label_filter(include={"service": ["payments"]}))
    assert step(entry) is None


def test_empty_filter_passes_everything(entry):
    lf = build_label_filter()
    assert lf.allows(entry) is True

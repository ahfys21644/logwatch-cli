"""Tests for logwatch.retention."""
from __future__ import annotations

import time
from typing import Optional

import pytest

from logwatch.retention import RetentionPolicy, apply_retention, retention_step


NOW = 1_700_000_000.0  # fixed epoch for deterministic tests


def _entry(age_seconds: float, ts_field: str = "timestamp") -> dict:
    return {ts_field: NOW - age_seconds, "message": "hello", "level": "info"}


@pytest.fixture
def policy() -> RetentionPolicy:
    return RetentionPolicy(max_age_seconds=60.0)


# --- construction -----------------------------------------------------------

def test_policy_rejects_zero_max_age():
    with pytest.raises(ValueError):
        RetentionPolicy(max_age_seconds=0)


def test_policy_rejects_negative_max_age():
    with pytest.raises(ValueError):
        RetentionPolicy(max_age_seconds=-5)


# --- is_expired -------------------------------------------------------------

def test_fresh_entry_not_expired(policy):
    assert not policy.is_expired(_entry(10), now=NOW)


def test_exactly_at_boundary_not_expired(policy):
    assert not policy.is_expired(_entry(60), now=NOW)


def test_old_entry_expired(policy):
    assert policy.is_expired(_entry(61), now=NOW)


def test_missing_timestamp_not_expired(policy):
    assert not policy.is_expired({"message": "no ts"}, now=NOW)


def test_invalid_timestamp_not_expired(policy):
    assert not policy.is_expired({"timestamp": "not-a-number"}, now=NOW)


def test_custom_timestamp_field():
    pol = RetentionPolicy(max_age_seconds=30, timestamp_field="ts")
    entry = {"ts": NOW - 40, "message": "x"}
    assert pol.is_expired(entry, now=NOW)


# --- apply ------------------------------------------------------------------

def test_apply_keeps_fresh_entry(policy):
    e = _entry(5)
    assert policy.apply(e, now=NOW) is e


def test_apply_drops_old_entry(policy):
    assert policy.apply(_entry(90), now=NOW) is None


def test_apply_calls_on_drop(policy):
    dropped = []
    pol = RetentionPolicy(max_age_seconds=60, on_drop=dropped.append)
    pol.apply(_entry(90), now=NOW)
    assert len(dropped) == 1


def test_apply_does_not_call_on_drop_for_kept_entry():
    dropped = []
    pol = RetentionPolicy(max_age_seconds=60, on_drop=dropped.append)
    pol.apply(_entry(5), now=NOW)
    assert dropped == []


# --- apply_retention --------------------------------------------------------

def test_apply_retention_filters_old_entries(policy):
    entries = [_entry(5), _entry(90), _entry(10), _entry(120)]
    result = apply_retention(entries, policy, now=NOW)
    assert len(result) == 2


def test_apply_retention_empty_input(policy):
    assert apply_retention([], policy, now=NOW) == []


# --- retention_step ---------------------------------------------------------

def test_retention_step_keeps_fresh(policy):
    step = retention_step(policy, now=NOW)
    e = _entry(5)
    assert step(e) is e


def test_retention_step_drops_old(policy):
    step = retention_step(policy, now=NOW)
    assert step(_entry(200)) is None

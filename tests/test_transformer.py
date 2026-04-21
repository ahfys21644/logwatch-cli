"""Tests for logwatch.transformer."""
import pytest
from logwatch.transformer import (
    Transformer,
    build_transformer,
    drop_field,
    set_field,
    drop_if,
)


@pytest.fixture()
def entry():
    return {"level": "info", "message": "hello", "host": "web-01"}


# --- Transformer.apply ---

def test_apply_no_steps_returns_entry_unchanged(entry):
    t = Transformer()
    assert t.apply(entry) == entry


def test_apply_step_mutates_entry(entry):
    t = Transformer()
    t.add_step(set_field("env", "prod"))
    result = t.apply(entry)
    assert result["env"] == "prod"


def test_apply_does_not_mutate_original(entry):
    t = build_transformer([set_field("env", "prod")])
    t.apply(entry)
    assert "env" not in entry


def test_apply_returns_none_when_step_drops_entry(entry):
    t = build_transformer([drop_if(lambda e: e["level"] == "info")])
    assert t.apply(entry) is None


def test_apply_stops_after_drop(entry):
    called = []
    def recorder(e):
        called.append(True)
        return e

    t = build_transformer([
        drop_if(lambda e: True),
        recorder,
    ])
    t.apply(entry)
    assert called == [], "step after drop should never be called"


def test_add_step_returns_self_for_chaining(entry):
    t = Transformer()
    returned = t.add_step(set_field("x", 1))
    assert returned is t


# --- apply_all ---

def test_apply_all_yields_transformed_entries():
    entries = [{"level": "info", "message": "a"}, {"level": "error", "message": "b"}]
    t = build_transformer([set_field("tagged", True)])
    results = list(t.apply_all(entries))
    assert all(r["tagged"] is True for r in results)


def test_apply_all_filters_dropped_entries():
    entries = [
        {"level": "debug", "message": "x"},
        {"level": "error", "message": "y"},
    ]
    t = build_transformer([drop_if(lambda e: e["level"] == "debug")])
    results = list(t.apply_all(entries))
    assert len(results) == 1
    assert results[0]["level"] == "error"


# --- drop_field ---

def test_drop_field_removes_key(entry):
    step = drop_field("host")
    result = step(entry)
    assert "host" not in result


def test_drop_field_missing_key_is_noop(entry):
    step = drop_field("nonexistent")
    result = step(entry)
    assert result == entry


# --- set_field ---

def test_set_field_adds_new_key(entry):
    step = set_field("region", "eu-west")
    result = step(entry)
    assert result["region"] == "eu-west"


def test_set_field_overwrites_existing_key(entry):
    step = set_field("level", "warning")
    result = step(entry)
    assert result["level"] == "warning"


# --- drop_if ---

def test_drop_if_returns_none_on_match(entry):
    step = drop_if(lambda e: "message" in e)
    assert step(entry) is None


def test_drop_if_returns_entry_on_no_match(entry):
    step = drop_if(lambda e: "missing_key" in e)
    assert step(entry) is entry

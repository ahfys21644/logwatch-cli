"""Tests for logwatch.field_filter."""
import pytest
from logwatch.field_filter import FieldFilter, FieldFilterRule, build_field_filter, field_filter_step


@pytest.fixture()
def entry():
    return {"level": "error", "service": "auth", "message": "login failed", "env": "prod"}


# --- FieldFilterRule.matches ---

def test_rule_matches_present_field_no_values(entry):
    rule = FieldFilterRule(field="service", values=[])
    assert rule.matches(entry) is True


def test_rule_no_match_absent_field(entry):
    rule = FieldFilterRule(field="host", values=[])
    assert rule.matches(entry) is False


def test_rule_matches_value_case_insensitive(entry):
    rule = FieldFilterRule(field="service", values=["AUTH"])
    assert rule.matches(entry) is True


def test_rule_no_match_wrong_value(entry):
    rule = FieldFilterRule(field="service", values=["payments"])
    assert rule.matches(entry) is False


def test_rule_case_sensitive_misses(entry):
    rule = FieldFilterRule(field="service", values=["AUTH"], case_sensitive=True)
    assert rule.matches(entry) is False


def test_rule_case_sensitive_hits(entry):
    rule = FieldFilterRule(field="service", values=["auth"], case_sensitive=True)
    assert rule.matches(entry) is True


def test_rule_empty_field_raises():
    with pytest.raises(ValueError):
        FieldFilterRule(field="", values=[])


# --- FieldFilter.allows ---

def test_no_rules_allows_everything(entry):
    ff = FieldFilter()
    assert ff.allows(entry) is True


def test_include_rule_passes_matching(entry):
    ff = FieldFilter(rules=[FieldFilterRule(field="env", values=["prod"])])
    assert ff.allows(entry) is True


def test_include_rule_blocks_non_matching(entry):
    ff = FieldFilter(rules=[FieldFilterRule(field="env", values=["staging"])])
    assert ff.allows(entry) is False


def test_exclude_rule_blocks_matching(entry):
    ff = FieldFilter(rules=[FieldFilterRule(field="level", values=["error"], exclude=True)])
    assert ff.allows(entry) is False


def test_exclude_rule_passes_non_matching(entry):
    ff = FieldFilter(rules=[FieldFilterRule(field="level", values=["debug"], exclude=True)])
    assert ff.allows(entry) is True


def test_multiple_include_rules_all_must_match(entry):
    ff = FieldFilter(rules=[
        FieldFilterRule(field="env", values=["prod"]),
        FieldFilterRule(field="service", values=["payments"]),
    ])
    assert ff.allows(entry) is False


def test_filter_iterable_removes_blocked(entry):
    other = {"level": "info", "service": "payments", "message": "ok", "env": "prod"}
    ff = FieldFilter(rules=[FieldFilterRule(field="service", values=["auth"])])
    result = list(ff.filter([entry, other]))
    assert result == [entry]


# --- build_field_filter ---

def test_build_from_list(entry):
    cfg = [{"field": "env", "values": ["prod"], "exclude": False}]
    ff = build_field_filter(cfg)
    assert ff.allows(entry) is True


def test_build_exclude_from_list(entry):
    cfg = [{"field": "level", "values": ["error"], "exclude": True}]
    ff = build_field_filter(cfg)
    assert ff.allows(entry) is False


# --- field_filter_step ---

def test_step_returns_entry_when_allowed(entry):
    ff = FieldFilter(rules=[FieldFilterRule(field="env", values=["prod"])])
    step = field_filter_step(ff)
    assert step(entry) is entry


def test_step_returns_none_when_blocked(entry):
    ff = FieldFilter(rules=[FieldFilterRule(field="env", values=["staging"])])
    step = field_filter_step(ff)
    assert step(entry) is None

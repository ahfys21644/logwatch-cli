"""Tests for logwatch.alerts module."""

import pytest
from logwatch.alerts import AlertRule, check_alerts, build_alert_handler


@pytest.fixture
def error_rule():
    return AlertRule(name="errors", level_threshold="error")


@pytest.fixture
def pattern_rule():
    return AlertRule(name="oom", pattern=r"out of memory")


@pytest.fixture
def field_rule():
    return AlertRule(name="svc-auth", field_match={"service": "auth"})


def test_alert_matches_level_threshold(error_rule):
    entry = {"level": "error", "message": "boom"}
    assert error_rule.matches(entry) is True


def test_alert_blocks_below_threshold(error_rule):
    entry = {"level": "info", "message": "ok"}
    assert error_rule.matches(entry) is False


def test_alert_matches_critical_above_error(error_rule):
    entry = {"level": "critical", "message": "fatal"}
    assert error_rule.matches(entry) is True


def test_alert_matches_pattern(pattern_rule):
    entry = {"level": "error", "message": "Out of Memory error occurred"}
    assert pattern_rule.matches(entry) is True


def test_alert_blocks_non_matching_pattern(pattern_rule):
    entry = {"level": "error", "message": "disk full"}
    assert pattern_rule.matches(entry) is False


def test_alert_pattern_case_insensitive(pattern_rule):
    entry = {"level": "warn", "message": "OUT OF MEMORY"}
    assert pattern_rule.matches(entry) is True


def test_alert_matches_field(field_rule):
    entry = {"level": "info", "message": "login", "service": "auth"}
    assert field_rule.matches(entry) is True


def test_alert_blocks_wrong_field(field_rule):
    entry = {"level": "info", "message": "login", "service": "billing"}
    assert field_rule.matches(entry) is False


def test_check_alerts_returns_matching_rules():
    rules = [
        AlertRule(name="r1", pattern="error"),
        AlertRule(name="r2", pattern="timeout"),
    ]
    entry = {"level": "error", "message": "connection error"}
    matched = check_alerts(entry, rules)
    assert len(matched) == 1
    assert matched[0].name == "r1"


def test_build_alert_handler_fires_callback():
    fired = []
    rule = AlertRule(name="test", pattern="fail")
    handler = build_alert_handler([rule], lambda e, r: fired.append(r.name))
    handler({"level": "error", "message": "fail hard"})
    assert fired == ["test"]


def test_build_alert_handler_no_match_no_callback():
    fired = []
    rule = AlertRule(name="test", pattern="fail")
    handler = build_alert_handler([rule], lambda e, r: fired.append(r.name))
    handler({"level": "info", "message": "all good"})
    assert fired == []

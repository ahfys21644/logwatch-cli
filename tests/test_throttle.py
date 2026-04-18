"""Tests for logwatch.throttle."""
import pytest
from logwatch.throttle import AlertThrottle, ThrottleConfig


@pytest.fixture
def throttle() -> AlertThrottle:
    return AlertThrottle(ThrottleConfig(window_seconds=60.0, max_per_window=3))


def test_first_alert_allowed(throttle):
    assert throttle.allow("rule_a", now=0.0) is True


def test_alerts_allowed_up_to_max(throttle):
    for i in range(3):
        assert throttle.allow("rule_a", now=float(i)) is True


def test_alert_throttled_after_max(throttle):
    for i in range(3):
        throttle.allow("rule_a", now=float(i))
    assert throttle.allow("rule_a", now=3.0) is False


def test_alert_allowed_after_window_expires(throttle):
    for i in range(3):
        throttle.allow("rule_a", now=float(i))
    # advance past window
    assert throttle.allow("rule_a", now=120.0) is True


def test_different_rules_are_independent(throttle):
    for i in range(3):
        throttle.allow("rule_a", now=float(i))
    # rule_a is throttled, rule_b should still pass
    assert throttle.allow("rule_b", now=3.0) is True


def test_emission_count_reflects_window(throttle):
    throttle.allow("rule_a", now=0.0)
    throttle.allow("rule_a", now=1.0)
    assert throttle.emission_count("rule_a", now=2.0) == 2


def test_emission_count_excludes_expired(throttle):
    throttle.allow("rule_a", now=0.0)
    throttle.allow("rule_a", now=1.0)
    # advance past window
    assert throttle.emission_count("rule_a", now=120.0) == 0


def test_reset_clears_single_rule(throttle):
    for i in range(3):
        throttle.allow("rule_a", now=float(i))
    throttle.reset("rule_a")
    assert throttle.allow("rule_a", now=3.0) is True


def test_reset_all_clears_everything(throttle):
    for i in range(3):
        throttle.allow("rule_a", now=float(i))
        throttle.allow("rule_b", now=float(i))
    throttle.reset_all()
    assert throttle.allow("rule_a", now=3.0) is True
    assert throttle.allow("rule_b", now=3.0) is True


def test_unknown_rule_emission_count_is_zero(throttle):
    assert throttle.emission_count("nonexistent", now=0.0) == 0

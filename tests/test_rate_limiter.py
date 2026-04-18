"""Tests for logwatch.rate_limiter."""
import pytest
from unittest.mock import patch
from logwatch.rate_limiter import RateLimiter


@pytest.fixture
def limiter():
    return RateLimiter(cooldown_seconds=30.0)


def test_first_alert_always_allowed(limiter):
    assert limiter.allow("error_rule") is True


def test_second_alert_within_cooldown_suppressed(limiter):
    limiter.allow("error_rule")
    assert limiter.allow("error_rule") is False


def test_alert_allowed_after_cooldown_expires(limiter):
    with patch("logwatch.rate_limiter.monotonic", side_effect=[0.0, 31.0]):
        limiter.allow("error_rule")
        assert limiter.allow("error_rule") is True


def test_alert_suppressed_before_cooldown_expires(limiter):
    with patch("logwatch.rate_limiter.monotonic", side_effect=[0.0, 10.0]):
        limiter.allow("error_rule")
        assert limiter.allow("error_rule") is False


def test_suppressed_count_increments(limiter):
    limiter.allow("error_rule")
    limiter.allow("error_rule")
    limiter.allow("error_rule")
    assert limiter.suppressed_count("error_rule") == 2


def test_suppressed_count_zero_for_unknown_rule(limiter):
    assert limiter.suppressed_count("nonexistent") == 0


def test_different_rules_are_independent(limiter):
    limiter.allow("rule_a")
    assert limiter.allow("rule_b") is True


def test_reset_clears_cooldown(limiter):
    limiter.allow("error_rule")
    limiter.reset("error_rule")
    assert limiter.allow("error_rule") is True


def test_reset_clears_suppressed_count(limiter):
    limiter.allow("error_rule")
    limiter.allow("error_rule")
    limiter.reset("error_rule")
    assert limiter.suppressed_count("error_rule") == 0


def test_reset_all_clears_everything(limiter):
    limiter.allow("rule_a")
    limiter.allow("rule_b")
    limiter.reset_all()
    assert limiter.allow("rule_a") is True
    assert limiter.allow("rule_b") is True


def test_summary_contains_fired_rules(limiter):
    limiter.allow("error_rule")
    limiter.allow("error_rule")
    s = limiter.summary()
    assert "error_rule" in s
    assert s["error_rule"]["suppressed"] == 1


def test_summary_empty_when_no_alerts_fired(limiter):
    s = limiter.summary()
    assert s == {}


def test_summary_multiple_rules(limiter):
    limiter.allow("rule_a")
    limiter.allow("rule_a")
    limiter.allow("rule_b")
    s = limiter.summary()
    assert s["rule_a"]["suppressed"] == 1
    assert s["rule_b"]["suppressed"] == 0

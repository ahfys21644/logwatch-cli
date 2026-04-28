"""Tests for logwatch.tag_router_config."""
import pytest
from logwatch.tag_router_config import (
    load_tag_rules_from_list,
    default_tag_router,
)


def _entry(level="INFO", message="hello", **kw):
    return {"level": level, "message": message, **kw}


def test_load_list_returns_correct_count():
    rules = load_tag_rules_from_list([
        {"tag": "error", "level": "ERROR"},
        {"tag": "warn", "level": "WARN"},
    ])
    assert len(rules) == 2


def test_load_list_sets_tag():
    rules = load_tag_rules_from_list([{"tag": "critical", "level": "ERROR"}])
    assert rules[0].tag == "critical"


def test_load_list_missing_tag_raises():
    with pytest.raises(ValueError, match="tag"):
        load_tag_rules_from_list([{"level": "ERROR"}])


def test_load_list_level_predicate_matches():
    rules = load_tag_rules_from_list([{"tag": "err", "level": "error"}])
    assert rules[0].predicate(_entry(level="ERROR")) is True


def test_load_list_level_predicate_blocks_other():
    rules = load_tag_rules_from_list([{"tag": "err", "level": "error"}])
    assert rules[0].predicate(_entry(level="INFO")) is False


def test_load_list_pattern_predicate_matches():
    rules = load_tag_rules_from_list([{"tag": "db", "pattern": "database"}])
    assert rules[0].predicate(_entry(message="database error")) is True


def test_load_list_pattern_predicate_blocks_non_match():
    rules = load_tag_rules_from_list([{"tag": "db", "pattern": "database"}])
    assert rules[0].predicate(_entry(message="network error")) is False


def test_load_list_field_value_predicate_matches():
    rules = load_tag_rules_from_list([{"tag": "svc", "field": "service", "value": "auth"}])
    assert rules[0].predicate({**_entry(), "service": "auth"}) is True


def test_load_list_field_value_predicate_blocks_mismatch():
    rules = load_tag_rules_from_list([{"tag": "svc", "field": "service", "value": "auth"}])
    assert rules[0].predicate({**_entry(), "service": "payments"}) is False


def test_default_tag_router_has_three_rules():
    router = default_tag_router()
    assert len(router.rules) == 3


def test_default_tag_router_tags_error():
    router = default_tag_router()
    tags = router.tag_entry(_entry(level="ERROR"))
    assert "error" in tags


def test_default_tag_router_tags_info():
    router = default_tag_router()
    tags = router.tag_entry(_entry(level="INFO"))
    assert "info" in tags

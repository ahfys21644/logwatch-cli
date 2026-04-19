"""Tests for logwatch.enricher — EnrichRule, enrich_entry, build_enricher."""
import pytest
from logwatch.enricher import EnrichRule, apply, enrich_entry, build_enricher


@pytest.fixture
def base_entry():
    return {
        "timestamp": "2024-01-01T00:00:00Z",
        "level": "INFO",
        "message": "user logged in from 192.168.1.10",
        "service": "auth",
    }


def test_static_value_added(base_entry):
    rule = EnrichRule(field="env", value="production")
    result = rule.apply(base_entry)
    assert result["env"] == "production"


def test_static_value_does_not_mutate_original(base_entry):
    rule = EnrichRule(field="env", value="production")
    result = rule.apply(base_entry)
    assert "env" not in base_entry
    assert result is not base_entry


def test_pattern_extracts_named_group(base_entry):
    rule = EnrichRule(
        field="ip",
        source_field="message",
        pattern=r"from (?P<ip>\d+\.\d+\.\d+\.\d+)",
    )
    result = rule.apply(base_entry)
    assert result["ip"] == "192.168.1.10"


def test_pattern_no_match_leaves_field_absent(base_entry):
    rule = EnrichRule(
        field="ip",
        source_field="message",
        pattern=r"from (?P<ip>NOMATCH)",
    )
    result = rule.apply(base_entry)
    assert "ip" not in result


def test_pattern_missing_source_field_leaves_field_absent(base_entry):
    rule = EnrichRule(
        field="ip",
        source_field="nonexistent",
        pattern=r"(?P<ip>\d+)",
    )
    result = rule.apply(base_entry)
    assert "ip" not in result


def test_enrich_entry_applies_all_rules(base_entry):
    rules = [
        EnrichRule(field="env", value="staging"),
        EnrichRule(field="region", value="eu-west"),
    ]
    result = enrich_entry(base_entry, rules)
    assert result["env"] == "staging"
    assert result["region"] == "eu-west"


def test_enrich_entry_empty_rules_returns_copy(base_entry):
    result = enrich_entry(base_entry, [])
    assert result == base_entry
    assert result is not base_entry


def test_build_enricher_returns_callable(base_entry):
    rules = [EnrichRule(field="app", value="logwatch")]
    enricher = build_enricher(rules)
    result = enricher(base_entry)
    assert result["app"] == "logwatch"


def test_build_enricher_no_rules_is_identity(base_entry):
    enricher = build_enricher([])
    result = enricher(base_entry)
    assert result == base_entry


def test_rule_overwrite_existing_field(base_entry):
    rule = EnrichRule(field="service", value="overridden")
    result = rule.apply(base_entry)
    assert result["service"] == "overridden"
    assert base_entry["service"] == "auth"


def test_pattern_group_name_matches_field(base_entry):
    """Named group in pattern must match field name for extraction."""
    rule = EnrichRule(
        field="user",
        source_field="message",
        pattern=r"(?P<user>user)",
    )
    result = rule.apply(base_entry)
    assert result["user"] == "user"

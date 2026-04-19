"""Tests for logwatch.enricher."""
import pytest
from logwatch.enricher import EnrichRule, enrich_entry, build_enricher


@pytest.fixture
def base_entry():
    return {
        "timestamp": "2024-01-01T00:00:00Z",
        "level": "error",
        "message": "Connection refused to host 10.0.0.5:8080",
        "service": "api-gateway",
    }


def test_static_value_added(base_entry):
    rule = EnrichRule(target_field="env", static_value="production")
    result = enrich_entry(base_entry, [rule])
    assert result["env"] == "production"


def test_static_value_does_not_mutate_original(base_entry):
    rule = EnrichRule(target_field="env", static_value="staging")
    enrich_entry(base_entry, [rule])
    assert "env" not in base_entry


def test_pattern_extracts_named_group(base_entry):
    rule = EnrichRule(
        target_field="host",
        source_field="message",
        pattern=r"to host (?P<host>[\d.]+)",
    )
    result = enrich_entry(base_entry, [rule])
    assert result["host"] == {"host": "10.0.0.5"}


def test_pattern_no_match_leaves_field_absent(base_entry):
    rule = EnrichRule(
        target_field="request_id",
        source_field="message",
        pattern=r"req=(?P<id>\w+)",
    )
    result = enrich_entry(base_entry, [rule])
    assert "request_id" not in result


def test_pattern_unnamed_group_returns_match_string(base_entry):
    rule = EnrichRule(
        target_field="port",
        source_field="message",
        pattern=r":(\d+)",
    )
    result = enrich_entry(base_entry, [rule])
    assert result["port"] == ":8080"


def test_transform_applied(base_entry):
    rule = EnrichRule(
        target_field="level_upper",
        source_field="level",
        transform=str.upper,
    )
    result = enrich_entry(base_entry, [rule])
    assert result["level_upper"] == "ERROR"


def test_transform_missing_source_skips(base_entry):
    rule = EnrichRule(
        target_field="derived",
        source_field="nonexistent",
        transform=str.upper,
    )
    result = enrich_entry(base_entry, [rule])
    assert "derived" not in result


def test_multiple_rules_applied_in_order(base_entry):
    rules = [
        EnrichRule(target_field="env", static_value="prod"),
        EnrichRule(target_field="tag", source_field="env", transform=lambda v: f"[{v}]"),
    ]
    result = enrich_entry(base_entry, rules)
    assert result["env"] == "prod"
    assert result["tag"] == "[prod]"


def test_build_enricher_returns_callable(base_entry):
    enricher = build_enricher([
        EnrichRule(target_field="env", static_value="test"),
    ])
    result = enricher(base_entry)
    assert result["env"] == "test"


def test_build_enricher_empty_rules(base_entry):
    enricher = build_enricher([])
    result = enricher(base_entry)
    assert result == base_entry

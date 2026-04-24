"""Tests for logwatch.retention_config."""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from logwatch.retention_config import (
    default_retention_policy,
    load_retention_policies_from_yaml,
    load_retention_policy_from_dict,
)


# --- load_retention_policy_from_dict ----------------------------------------

def test_load_dict_sets_max_age():
    pol = load_retention_policy_from_dict({"max_age_seconds": 120})
    assert pol.max_age_seconds == 120.0


def test_load_dict_default_timestamp_field():
    pol = load_retention_policy_from_dict({"max_age_seconds": 60})
    assert pol.timestamp_field == "timestamp"


def test_load_dict_custom_timestamp_field():
    pol = load_retention_policy_from_dict(
        {"max_age_seconds": 60, "timestamp_field": "ts"}
    )
    assert pol.timestamp_field == "ts"


def test_load_dict_missing_max_age_raises():
    with pytest.raises(KeyError):
        load_retention_policy_from_dict({"timestamp_field": "ts"})


def test_load_dict_string_max_age_coerced():
    pol = load_retention_policy_from_dict({"max_age_seconds": "300"})
    assert pol.max_age_seconds == 300.0


# --- load_retention_policies_from_yaml --------------------------------------

def test_load_yaml_returns_list(tmp_path: Path):
    yaml_text = textwrap.dedent("""\
        retention:
          - max_age_seconds: 600
          - max_age_seconds: 3600
            timestamp_field: ts
    """)
    cfg = tmp_path / "retention.yaml"
    cfg.write_text(yaml_text)
    policies = load_retention_policies_from_yaml(str(cfg))
    assert len(policies) == 2


def test_load_yaml_first_policy_max_age(tmp_path: Path):
    yaml_text = "retention:\n  - max_age_seconds: 600\n"
    cfg = tmp_path / "r.yaml"
    cfg.write_text(yaml_text)
    policies = load_retention_policies_from_yaml(str(cfg))
    assert policies[0].max_age_seconds == 600.0


def test_load_yaml_custom_ts_field(tmp_path: Path):
    yaml_text = "retention:\n  - max_age_seconds: 60\n    timestamp_field: logged_at\n"
    cfg = tmp_path / "r.yaml"
    cfg.write_text(yaml_text)
    policies = load_retention_policies_from_yaml(str(cfg))
    assert policies[0].timestamp_field == "logged_at"


def test_load_yaml_empty_section_returns_empty_list(tmp_path: Path):
    cfg = tmp_path / "empty.yaml"
    cfg.write_text("retention: []\n")
    assert load_retention_policies_from_yaml(str(cfg)) == []


# --- default_retention_policy -----------------------------------------------

def test_default_policy_max_age():
    pol = default_retention_policy()
    assert pol.max_age_seconds == 3600.0


def test_default_policy_timestamp_field():
    pol = default_retention_policy()
    assert pol.timestamp_field == "timestamp"


def test_default_policy_custom_max_age():
    pol = default_retention_policy(max_age_seconds=120)
    assert pol.max_age_seconds == 120.0

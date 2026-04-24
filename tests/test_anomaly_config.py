"""Tests for logwatch.anomaly_config."""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from logwatch.anomaly_config import (
    default_anomaly_configs,
    load_anomaly_configs_from_list,
    load_anomaly_configs_from_yaml,
)
from logwatch.anomaly_detector import AnomalyConfig


# ---------------------------------------------------------------------------
# load_anomaly_configs_from_list
# ---------------------------------------------------------------------------

def test_load_list_returns_correct_count() -> None:
    raw = [
        {"level": "error", "window_seconds": 60, "max_count": 10},
        {"level": "warn", "window_seconds": 30, "max_count": 5},
    ]
    result = load_anomaly_configs_from_list(raw)
    assert len(result) == 2


def test_load_list_sets_level() -> None:
    raw = [{"level": "critical", "window_seconds": 10, "max_count": 2}]
    result = load_anomaly_configs_from_list(raw)
    assert result[0].level == "critical"


def test_load_list_sets_window() -> None:
    raw = [{"level": "error", "window_seconds": 45.5, "max_count": 8}]
    result = load_anomaly_configs_from_list(raw)
    assert result[0].window_seconds == 45.5


def test_load_list_sets_max_count() -> None:
    raw = [{"level": "error", "window_seconds": 60, "max_count": 15}]
    result = load_anomaly_configs_from_list(raw)
    assert result[0].max_count == 15


def test_load_list_uses_provided_name() -> None:
    raw = [{"level": "error", "window_seconds": 60, "max_count": 5, "name": "my_rule"}]
    result = load_anomaly_configs_from_list(raw)
    assert result[0].name == "my_rule"


def test_load_list_auto_names_when_absent() -> None:
    raw = [{"level": "warn", "window_seconds": 20, "max_count": 4}]
    result = load_anomaly_configs_from_list(raw)
    assert result[0].name != ""


def test_load_empty_list_returns_empty() -> None:
    assert load_anomaly_configs_from_list([]) == []


# ---------------------------------------------------------------------------
# load_anomaly_configs_from_yaml
# ---------------------------------------------------------------------------

def test_load_yaml_returns_configs(tmp_path: Path) -> None:
    yaml_text = textwrap.dedent("""\
        anomalies:
          - level: error
            window_seconds: 60
            max_count: 10
            name: yaml_rule
    """)
    p = tmp_path / "anomalies.yaml"
    p.write_text(yaml_text)
    result = load_anomaly_configs_from_yaml(str(p))
    assert len(result) == 1
    assert result[0].name == "yaml_rule"


def test_load_yaml_empty_file_returns_empty(tmp_path: Path) -> None:
    p = tmp_path / "empty.yaml"
    p.write_text("anomalies: []")
    result = load_anomaly_configs_from_yaml(str(p))
    assert result == []


# ---------------------------------------------------------------------------
# default_anomaly_configs
# ---------------------------------------------------------------------------

def test_default_configs_returns_list() -> None:
    result = default_anomaly_configs()
    assert isinstance(result, list)
    assert len(result) > 0


def test_default_configs_all_valid() -> None:
    for cfg in default_anomaly_configs():
        assert isinstance(cfg, AnomalyConfig)
        assert cfg.window_seconds > 0
        assert cfg.max_count > 0

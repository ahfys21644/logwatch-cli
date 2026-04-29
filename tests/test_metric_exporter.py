"""Tests for logwatch.metric_exporter and logwatch.metric_exporter_config."""
from __future__ import annotations

import os
import pytest

from logwatch.stats import SessionStats
from logwatch.metric_exporter import (
    MetricExporterConfig,
    export_metrics,
    export_metrics_to_file,
)
from logwatch.metric_exporter_config import (
    default_exporter_config,
    load_exporter_config_from_dict,
)


@pytest.fixture()
def stats() -> SessionStats:
    s = SessionStats()
    for level in ("INFO", "INFO", "WARN", "ERROR"):
        s.record_entry({"level": level, "message": "msg"})
    s.record_alert()
    s.record_alert()
    return s


# --- MetricExporterConfig ---

def test_config_default_namespace():
    cfg = MetricExporterConfig()
    assert cfg.namespace == "logwatch"


def test_config_rejects_empty_namespace():
    with pytest.raises(ValueError, match="namespace"):
        MetricExporterConfig(namespace="")


def test_config_rejects_invalid_namespace():
    with pytest.raises(ValueError, match="namespace"):
        MetricExporterConfig(namespace="my-ns")


def test_config_custom_namespace():
    cfg = MetricExporterConfig(namespace="myapp")
    assert cfg.namespace == "myapp"


# --- export_metrics ---

def test_export_contains_entries_total(stats):
    output = export_metrics(stats)
    assert "logwatch_entries_total" in output


def test_export_entries_total_value(stats):
    output = export_metrics(stats)
    line = next(l for l in output.splitlines() if l.startswith("logwatch_entries_total{") or l == "logwatch_entries_total 4")
    assert "4" in line


def test_export_contains_per_level(stats):
    output = export_metrics(stats)
    assert 'level="info"' in output
    assert 'level="error"' in output


def test_export_info_count(stats):
    output = export_metrics(stats)
    info_line = next(l for l in output.splitlines() if 'level="info"' in l)
    assert info_line.endswith(" 2")


def test_export_alerts_total(stats):
    output = export_metrics(stats)
    assert "logwatch_alerts_total" in output
    alerts_line = next(l for l in output.splitlines() if l.startswith("logwatch_alerts_total") and not l.startswith("#"))
    assert alerts_line.endswith(" 2")


def test_export_custom_namespace(stats):
    cfg = MetricExporterConfig(namespace="myapp")
    output = export_metrics(stats, cfg)
    assert "myapp_entries_total" in output
    assert "logwatch_entries_total" not in output


def test_export_extra_labels(stats):
    cfg = MetricExporterConfig(extra_labels={"env": "prod"})
    output = export_metrics(stats, cfg)
    assert 'env="prod"' in output


def test_export_to_file(stats, tmp_path):
    path = str(tmp_path / "metrics.txt")
    export_metrics_to_file(stats, path)
    assert os.path.exists(path)
    content = open(path).read()
    assert "logwatch_entries_total" in content


# --- load_exporter_config_from_dict ---

def test_load_dict_sets_namespace():
    cfg = load_exporter_config_from_dict({"namespace": "testns"})
    assert cfg.namespace == "testns"


def test_load_dict_sets_extra_labels():
    cfg = load_exporter_config_from_dict({"extra_labels": {"host": "srv1"}})
    assert cfg.extra_labels == {"host": "srv1"}


def test_load_dict_invalid_extra_labels_raises():
    with pytest.raises(ValueError, match="extra_labels"):
        load_exporter_config_from_dict({"extra_labels": "bad"})


def test_default_exporter_config():
    cfg = default_exporter_config()
    assert cfg.namespace == "logwatch"
    assert cfg.extra_labels == {}

"""Tests for logwatch.pipeline module."""

import pytest
from logwatch.pipeline import run_pipeline, build_pipeline
from logwatch.output import OutputSink
from logwatch.alerts import AlertRule
from logwatch.filter import filter_by_level


@pytest.fixture
def info_entry():
    return {"level": "INFO", "message": "all good", "timestamp": "2024-01-01T00:00:00Z"}


@pytest.fixture
def error_entry():
    return {"level": "ERROR", "message": "boom", "timestamp": "2024-01-01T00:00:01Z"}


@pytest.fixture
def sink(capsys):
    return OutputSink(no_color=True)


def test_pipeline_passes_matching_entries(sink, info_entry, capsys):
    stats = run_pipeline(iter([info_entry]), [], [], sink)
    assert stats["passed"] == 1
    assert "all good" in capsys.readouterr().out


def test_pipeline_blocks_filtered_entries(sink, info_entry, capsys):
    f = filter_by_level("ERROR")
    stats = run_pipeline(iter([info_entry]), [f], [], sink)
    assert stats["passed"] == 0
    assert stats["total"] == 1


def test_pipeline_counts_alerts(sink, error_entry, capsys):
    rule = AlertRule(name="err-rule", level_threshold="ERROR")
    stats = run_pipeline(iter([error_entry]), [], [rule], sink)
    assert stats["alerts"] == 1


def test_pipeline_calls_on_alert_callback(sink, error_entry, capsys):
    rule = AlertRule(name="err-rule", level_threshold="ERROR")
    triggered = []
    run_pipeline(iter([error_entry]), [], [rule], sink, on_alert=lambda r, e: triggered.append(r.name))
    assert triggered == ["err-rule"]


def test_pipeline_no_alerts_for_info(sink, info_entry, capsys):
    rule = AlertRule(name="err-rule", level_threshold="ERROR")
    stats = run_pipeline(iter([info_entry]), [], [rule], sink)
    assert stats["alerts"] == 0


def test_build_pipeline_returns_stats(info_entry, capsys):
    stats = build_pipeline(iter([info_entry]), no_color=True)
    assert stats["total"] == 1
    assert stats["passed"] == 1


def test_build_pipeline_writes_to_file(tmp_path, info_entry, capsys):
    out = tmp_path / "pipeline.log"
    build_pipeline(iter([info_entry]), file_path=str(out), no_color=True)
    assert "all good" in out.read_text()


def test_pipeline_empty_entries(sink, capsys):
    stats = run_pipeline(iter([]), [], [], sink)
    assert stats == {"total": 0, "passed": 0, "alerts": 0}


def test_pipeline_multiple_rules_trigger_independently(sink, error_entry, capsys):
    """Each matching alert rule should be counted and trigger its own callback."""
    rule_a = AlertRule(name="rule-a", level_threshold="ERROR")
    rule_b = AlertRule(name="rule-b", level_threshold="ERROR")
    triggered = []
    stats = run_pipeline(
        iter([error_entry]),
        [],
        [rule_a, rule_b],
        sink,
        on_alert=lambda r, e: triggered.append(r.name),
    )
    assert stats["alerts"] == 2
    assert triggered == ["rule-a", "rule-b"]

"""Tests for logwatch.replay and logwatch.replay_runner."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from logwatch.replay import replay_from_file, replay_from_jsonl, replay_from_snapshot
from logwatch.replay_runner import run_replay


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def plain_log(tmp_path: Path) -> Path:
    p = tmp_path / "app.log"
    p.write_text(
        'level=INFO msg="service started"\n'
        'level=ERROR msg="disk full"\n'
        'level=DEBUG msg="heartbeat"\n',
        encoding="utf-8",
    )
    return p


@pytest.fixture()
def jsonl_log(tmp_path: Path) -> Path:
    p = tmp_path / "app.jsonl"
    lines = [
        json.dumps({"level": "INFO", "message": "boot"}),
        json.dumps({"level": "WARN", "message": "slow query"}),
        "",  # blank line — should be skipped
        json.dumps({"level": "ERROR", "message": "crash"}),
    ]
    p.write_text("\n".join(lines), encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# replay_from_file
# ---------------------------------------------------------------------------

def test_replay_file_yields_all_entries(plain_log):
    entries = list(replay_from_file(plain_log))
    assert len(entries) == 3


def test_replay_file_respects_limit(plain_log):
    entries = list(replay_from_file(plain_log, limit=2))
    assert len(entries) == 2


def test_replay_file_entries_have_level(plain_log):
    entries = list(replay_from_file(plain_log))
    levels = {e.get("level") for e in entries}
    assert "INFO" in levels
    assert "ERROR" in levels


# ---------------------------------------------------------------------------
# replay_from_jsonl
# ---------------------------------------------------------------------------

def test_replay_jsonl_skips_blank_lines(jsonl_log):
    entries = list(replay_from_jsonl(jsonl_log))
    assert len(entries) == 3


def test_replay_jsonl_respects_limit(jsonl_log):
    entries = list(replay_from_jsonl(jsonl_log, limit=1))
    assert len(entries) == 1
    assert entries[0]["level"] == "INFO"


def test_replay_jsonl_preserves_fields(jsonl_log):
    entries = list(replay_from_jsonl(jsonl_log))
    messages = [e["message"] for e in entries]
    assert "slow query" in messages


# ---------------------------------------------------------------------------
# replay_from_snapshot (delegates to load_snapshot)
# ---------------------------------------------------------------------------

def test_replay_snapshot_empty_when_missing(monkeypatch):
    monkeypatch.setattr(
        "logwatch.replay.load_snapshot",
        lambda name: {},
    )
    entries = list(replay_from_snapshot("nonexistent"))
    assert entries == []


def test_replay_snapshot_yields_stored_entries(monkeypatch):
    fake = {"entries": [{"level": "INFO", "message": "ok"}, {"level": "ERROR", "message": "bad"}]}
    monkeypatch.setattr("logwatch.replay.load_snapshot", lambda name: fake)
    entries = list(replay_from_snapshot("mysnap"))
    assert len(entries) == 2


# ---------------------------------------------------------------------------
# run_replay (runner)
# ---------------------------------------------------------------------------

def test_run_replay_collects_stats(plain_log):
    collected: list[dict] = []
    stats = run_replay(str(plain_log), kind="file", pipeline=[], sink=collected.append)
    assert stats.total == 3


def test_run_replay_pipeline_filters_entries(plain_log):
    def only_error(entry):
        return entry if entry.get("level") == "ERROR" else None

    collected: list[dict] = []
    run_replay(str(plain_log), kind="file", pipeline=[only_error], sink=collected.append)
    assert len(collected) == 1
    assert collected[0]["level"] == "ERROR"

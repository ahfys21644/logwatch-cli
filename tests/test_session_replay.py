"""Tests for logwatch.session_replay."""
from __future__ import annotations

import pytest
from unittest.mock import patch

from logwatch.session_replay import SessionReplayConfig, replay_session, iter_replay_session


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _entry(level: str = "info", msg: str = "hello") -> dict:
    return {"level": level, "message": msg, "timestamp": "2024-01-01T00:00:00Z"}


FAKE_SNAPSHOT = {
    "entries": [
        _entry("debug", "debug msg"),
        _entry("info", "info msg"),
        _entry("warning", "warn msg"),
        _entry("error", "error msg"),
    ]
}


@pytest.fixture()
def config() -> SessionReplayConfig:
    return SessionReplayConfig(snapshot_name="test_snap")


# ---------------------------------------------------------------------------
# SessionReplayConfig validation
# ---------------------------------------------------------------------------

def test_config_rejects_zero_speed():
    with pytest.raises(ValueError, match="speed"):
        SessionReplayConfig(snapshot_name="x", speed=0)


def test_config_rejects_negative_speed():
    with pytest.raises(ValueError, match="speed"):
        SessionReplayConfig(snapshot_name="x", speed=-1.0)


def test_config_rejects_zero_limit():
    with pytest.raises(ValueError, match="limit"):
        SessionReplayConfig(snapshot_name="x", limit=0)


def test_config_accepts_positive_limit():
    cfg = SessionReplayConfig(snapshot_name="x", limit=5)
    assert cfg.limit == 5


# ---------------------------------------------------------------------------
# replay_session
# ---------------------------------------------------------------------------

def test_replay_session_calls_on_entry_for_each_passing_entry(config):
    collected = []
    with patch("logwatch.session_replay.load_snapshot", return_value=FAKE_SNAPSHOT):
        replay_session(config, on_entry=collected.append)
    # default min_level is debug so all 4 entries pass
    assert len(collected) == 4


def test_replay_session_filters_by_min_level():
    collected = []
    cfg = SessionReplayConfig(snapshot_name="x", min_level="error")
    with patch("logwatch.session_replay.load_snapshot", return_value=FAKE_SNAPSHOT):
        replay_session(cfg, on_entry=collected.append)
    assert all(e["level"] == "error" for e in collected)
    assert len(collected) == 1


def test_replay_session_respects_limit():
    collected = []
    cfg = SessionReplayConfig(snapshot_name="x", limit=2)
    with patch("logwatch.session_replay.load_snapshot", return_value=FAKE_SNAPSHOT):
        replay_session(cfg, on_entry=collected.append)
    assert len(collected) == 2


def test_replay_session_returns_stats(config):
    with patch("logwatch.session_replay.load_snapshot", return_value=FAKE_SNAPSHOT):
        stats = replay_session(config, on_entry=lambda e: None)
    assert stats.total >= 1


def test_replay_session_stats_total_matches_entries(config):
    with patch("logwatch.session_replay.load_snapshot", return_value=FAKE_SNAPSHOT):
        stats = replay_session(config, on_entry=lambda e: None)
    assert stats.total == 4


def test_replay_session_empty_snapshot():
    collected = []
    with patch("logwatch.session_replay.load_snapshot", return_value={"entries": []}):
        stats = replay_session(
            SessionReplayConfig(snapshot_name="empty"),
            on_entry=collected.append,
        )
    assert collected == []
    assert stats.total == 0


# ---------------------------------------------------------------------------
# iter_replay_session
# ---------------------------------------------------------------------------

def test_iter_replay_session_yields_entries(config):
    with patch("logwatch.session_replay.load_snapshot", return_value=FAKE_SNAPSHOT):
        entries = list(iter_replay_session(config))
    assert len(entries) == 4


def test_iter_replay_session_respects_limit():
    cfg = SessionReplayConfig(snapshot_name="x", limit=1)
    with patch("logwatch.session_replay.load_snapshot", return_value=FAKE_SNAPSHOT):
        entries = list(iter_replay_session(cfg))
    assert len(entries) == 1


def test_iter_replay_session_filters_level():
    cfg = SessionReplayConfig(snapshot_name="x", min_level="warning")
    with patch("logwatch.session_replay.load_snapshot", return_value=FAKE_SNAPSHOT):
        entries = list(iter_replay_session(cfg))
    levels = {e["level"] for e in entries}
    assert "debug" not in levels
    assert "info" not in levels

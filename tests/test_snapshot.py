"""Tests for logwatch.snapshot."""
from __future__ import annotations

import json
import os
import pytest

from logwatch.stats import SessionStats
from logwatch import snapshot as snap


@pytest.fixture()
def tmp_path_snap(tmp_path):
    return str(tmp_path / "snapshot.json")


@pytest.fixture()
def populated_stats():
    s = SessionStats()
    s.total = 10
    s.by_level = {"info": 7, "error": 3}
    s.alerts_fired = 2
    return s


def test_save_creates_file(populated_stats, tmp_path_snap):
    snap.save_snapshot(populated_stats, tmp_path_snap)
    assert os.path.exists(tmp_path_snap)


def test_save_content(populated_stats, tmp_path_snap):
    snap.save_snapshot(populated_stats, tmp_path_snap)
    with open(tmp_path_snap) as fh:
        data = json.load(fh)
    assert data["total"] == 10
    assert data["by_level"]["error"] == 3
    assert data["alerts_fired"] == 2
    assert "saved_at" in data


def test_load_missing_returns_empty(tmp_path_snap):
    result = snap.load_snapshot(tmp_path_snap)
    assert result == {}


def test_load_returns_dict(populated_stats, tmp_path_snap):
    snap.save_snapshot(populated_stats, tmp_path_snap)
    data = snap.load_snapshot(tmp_path_snap)
    assert data["total"] == 10


def test_merge_adds_counts(populated_stats, tmp_path_snap):
    snap.save_snapshot(populated_stats, tmp_path_snap)
    fresh = SessionStats()
    fresh.total = 5
    fresh.by_level = {"info": 5}
    fresh.alerts_fired = 1
    snap.merge_snapshot(fresh, tmp_path_snap)
    assert fresh.total == 15
    assert fresh.by_level["info"] == 12
    assert fresh.by_level["error"] == 3
    assert fresh.alerts_fired == 3


def test_merge_no_file_is_noop(tmp_path_snap):
    s = SessionStats()
    s.total = 4
    snap.merge_snapshot(s, tmp_path_snap)
    assert s.total == 4


def test_delete_removes_file(populated_stats, tmp_path_snap):
    snap.save_snapshot(populated_stats, tmp_path_snap)
    result = snap.delete_snapshot(tmp_path_snap)
    assert result is True
    assert not os.path.exists(tmp_path_snap)


def test_delete_missing_returns_false(tmp_path_snap):
    assert snap.delete_snapshot(tmp_path_snap) is False

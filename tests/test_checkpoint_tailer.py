"""Tests for logwatch.checkpoint_tailer."""

from __future__ import annotations

from pathlib import Path

import pytest

from logwatch.checkpoint import load_checkpoint, save_checkpoint
from logwatch.checkpoint_tailer import replay_from_checkpoint


@pytest.fixture()
def log_file(tmp_path: Path) -> Path:
    p = tmp_path / "app.log"
    lines = [
        '{"level": "info", "message": "started"}',
        '{"level": "warn", "message": "slow query"}',
        '{"level": "error", "message": "disk full"}',
        '{"level": "info", "message": "resumed"}',
    ]
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return p


@pytest.fixture()
def cp_dir(tmp_path: Path) -> Path:
    return tmp_path / "cp"


def test_replay_all_from_zero(log_file: Path, cp_dir: Path) -> None:
    entries = replay_from_checkpoint(str(log_file), checkpoint_dir=cp_dir)
    assert len(entries) == 4


def test_replay_respects_limit(log_file: Path, cp_dir: Path) -> None:
    entries = replay_from_checkpoint(str(log_file), checkpoint_dir=cp_dir, limit=2)
    assert len(entries) == 2


def test_replay_entries_have_level(log_file: Path, cp_dir: Path) -> None:
    entries = replay_from_checkpoint(str(log_file), checkpoint_dir=cp_dir)
    assert entries[0]["level"] == "info"
    assert entries[2]["level"] == "error"


def test_replay_from_checkpoint_skips_earlier_lines(log_file: Path, cp_dir: Path) -> None:
    # Seek past the first two lines
    with open(log_file, "r", encoding="utf-8") as fh:
        fh.readline()
        fh.readline()
        mid_offset = fh.tell()
    save_checkpoint(str(log_file), mid_offset, cp_dir)
    entries = replay_from_checkpoint(str(log_file), checkpoint_dir=cp_dir)
    assert len(entries) == 2
    assert entries[0]["message"] == "disk full"


def test_replay_from_zero_when_no_checkpoint(log_file: Path, cp_dir: Path) -> None:
    entries = replay_from_checkpoint(str(log_file), checkpoint_dir=cp_dir)
    assert entries[0]["message"] == "started"


def test_replay_returns_empty_when_at_eof(log_file: Path, cp_dir: Path) -> None:
    eof = log_file.stat().st_size
    save_checkpoint(str(log_file), eof, cp_dir)
    entries = replay_from_checkpoint(str(log_file), checkpoint_dir=cp_dir)
    assert entries == []

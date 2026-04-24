"""Tests for logwatch.checkpoint."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from logwatch.checkpoint import (
    delete_checkpoint,
    list_checkpoints,
    load_checkpoint,
    save_checkpoint,
)


@pytest.fixture()
def cp_dir(tmp_path: Path) -> Path:
    return tmp_path / "checkpoints"


def test_save_creates_file(cp_dir: Path) -> None:
    save_checkpoint("/var/log/app.log", 1024, cp_dir)
    assert any(cp_dir.iterdir())


def test_save_content_contains_offset(cp_dir: Path) -> None:
    path = save_checkpoint("/var/log/app.log", 2048, cp_dir)
    data = json.loads(path.read_text())
    assert data["offset"] == 2048


def test_save_content_contains_path(cp_dir: Path) -> None:
    path = save_checkpoint("/var/log/app.log", 0, cp_dir)
    data = json.loads(path.read_text())
    assert data["path"] == "/var/log/app.log"


def test_load_returns_saved_offset(cp_dir: Path) -> None:
    save_checkpoint("/var/log/app.log", 512, cp_dir)
    assert load_checkpoint("/var/log/app.log", cp_dir) == 512


def test_load_missing_returns_zero(cp_dir: Path) -> None:
    assert load_checkpoint("/no/such/file.log", cp_dir) == 0


def test_load_corrupt_file_returns_zero(cp_dir: Path) -> None:
    cp_dir.mkdir(parents=True)
    bad = cp_dir / "var_log_app.log.json"
    bad.write_text("not-json")
    assert load_checkpoint("/var/log/app.log", cp_dir) == 0


def test_delete_removes_file(cp_dir: Path) -> None:
    save_checkpoint("/var/log/app.log", 100, cp_dir)
    result = delete_checkpoint("/var/log/app.log", cp_dir)
    assert result is True
    assert load_checkpoint("/var/log/app.log", cp_dir) == 0


def test_delete_missing_returns_false(cp_dir: Path) -> None:
    assert delete_checkpoint("/no/such/file.log", cp_dir) is False


def test_list_checkpoints_returns_all(cp_dir: Path) -> None:
    save_checkpoint("/var/log/a.log", 10, cp_dir)
    save_checkpoint("/var/log/b.log", 20, cp_dir)
    result = list_checkpoints(cp_dir)
    assert result["/var/log/a.log"] == 10
    assert result["/var/log/b.log"] == 20


def test_list_checkpoints_empty_dir(cp_dir: Path) -> None:
    assert list_checkpoints(cp_dir) == {}


def test_overwrite_updates_offset(cp_dir: Path) -> None:
    save_checkpoint("/var/log/app.log", 100, cp_dir)
    save_checkpoint("/var/log/app.log", 999, cp_dir)
    assert load_checkpoint("/var/log/app.log", cp_dir) == 999

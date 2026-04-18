"""Tests for logwatch.tailer (tail_lines; tail_file tested via tmp file)."""

import os
import time
import threading
import pytest
from logwatch.tailer import tail_lines, tail_file


@pytest.fixture()
def log_file(tmp_path):
    f = tmp_path / "app.log"
    f.write_text(
        '{"level": "info", "message": "started"}\n'
        '{"level": "warn", "message": "slow query"}\n'
        '{"level": "error", "message": "boom"}\n',
        encoding="utf-8",
    )
    return f


def test_tail_lines_returns_last_n(log_file):
    entries = tail_lines(str(log_file), n=2)
    assert len(entries) == 2
    assert entries[-1]["message"] == "boom"


def test_tail_lines_fewer_than_n(log_file):
    entries = tail_lines(str(log_file), n=100)
    assert len(entries) == 3


def test_tail_lines_parses_level(log_file):
    entries = tail_lines(str(log_file), n=3)
    assert entries[0]["level"] == "info"
    assert entries[1]["level"] == "warn"


def test_tail_file_yields_new_lines(tmp_path):
    f = tmp_path / "stream.log"
    f.write_text("", encoding="utf-8")

    collected = []
    stop = threading.Event()

    def reader():
        for entry in tail_file(str(f), poll_interval=0.05, from_start=True):
            collected.append(entry)
            if len(collected) >= 2:
                break

    t = threading.Thread(target=reader, daemon=True)
    t.start()

    time.sleep(0.1)
    with open(f, "a", encoding="utf-8") as fh:
        fh.write('{"level": "info", "message": "line1"}\n')
        fh.flush()
        time.sleep(0.15)
        fh.write('{"level": "error", "message": "line2"}\n')
        fh.flush()

    t.join(timeout=3)
    assert len(collected) == 2
    assert collected[0]["message"] == "line1"
    assert collected[1]["level"] == "error"


def test_tail_file_from_start(log_file):
    collected = []
    for entry in tail_file(str(log_file), poll_interval=0.05, from_start=True):
        collected.append(entry)
        if len(collected) >= 3:
            break
    assert len(collected) == 3
    assert collected[0]["message"] == "started"

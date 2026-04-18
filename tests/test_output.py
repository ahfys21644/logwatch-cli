"""Tests for logwatch.output module."""

import pytest
from unittest.mock import patch, MagicMock
from io import StringIO

from logwatch.output import OutputSink, write_entries


@pytest.fixture
def basic_entry():
    return {"level": "INFO", "message": "hello world", "timestamp": "2024-01-01T00:00:00Z"}


@pytest.fixture
def sink():
    return OutputSink(no_color=True)


def test_write_entry_prints_to_stdout(sink, basic_entry, capsys):
    sink.write_entry(basic_entry)
    captured = capsys.readouterr()
    assert "hello world" in captured.out


def test_write_entry_contains_level(sink, basic_entry, capsys):
    sink.write_entry(basic_entry)
    captured = capsys.readouterr()
    assert "INFO" in captured.out


def test_write_alert_prints_rule_name(sink, basic_entry, capsys):
    sink.write_alert("my-rule", basic_entry)
    captured = capsys.readouterr()
    assert "my-rule" in captured.out


def test_write_entries_returns_count(sink, basic_entry, capsys):
    entries = [basic_entry, basic_entry, basic_entry]
    count = write_entries(iter(entries), sink)
    assert count == 3


def test_write_entries_empty(sink, capsys):
    count = write_entries(iter([]), sink)
    assert count == 0


def test_sink_writes_to_file(tmp_path, basic_entry, capsys):
    out_file = tmp_path / "out.log"
    with OutputSink(file_path=str(out_file), no_color=True) as s:
        s.write_entry(basic_entry)
    content = out_file.read_text()
    assert "hello world" in content


def test_sink_appends_to_existing_file(tmp_path, basic_entry, capsys):
    out_file = tmp_path / "out.log"
    out_file.write_text("existing\n")
    with OutputSink(file_path=str(out_file), no_color=True) as s:
        s.write_entry(basic_entry)
    content = out_file.read_text()
    assert content.startswith("existing")
    assert "hello world" in content


def test_sink_context_manager_closes_file(tmp_path, basic_entry):
    out_file = tmp_path / "out.log"
    s = OutputSink(file_path=str(out_file), no_color=True)
    s.open()
    assert s._file_handle is not None
    s.close()
    assert s._file_handle is None


def test_no_file_handle_without_path(basic_entry, capsys):
    s = OutputSink(no_color=True)
    s.open()
    assert s._file_handle is None
    s.write_entry(basic_entry)
    s.close()

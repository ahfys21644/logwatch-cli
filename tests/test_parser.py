"""Tests for logwatch.parser module."""

import pytest
from logwatch.parser import parse_line, extract_level


def test_parse_json_line():
    line = '{"level": "info", "message": "service started", "pid": 42}'
    result = parse_line(line)
    assert result["level"] == "info"
    assert result["message"] == "service started"
    assert result["pid"] == 42


def test_parse_json_normalizes_severity():
    line = '{"severity": "fatal", "msg": "out of memory"}'
    result = parse_line(line)
    assert result["level"] == "critical"
    assert result["message"] == "out of memory"
    assert "severity" not in result


def test_parse_kv_line():
    line = 'level=error msg="disk full" host=server01'
    result = parse_line(line)
    assert result["level"] == "error"
    assert result["message"] == "disk full"
    assert result["host"] == "server01"


def test_parse_kv_normalizes_warn():
    line = "level=warn message=retrying"
    result = parse_line(line)
    assert result["level"] == "warning"


def test_parse_plain_text():
    line = "Something unexpected happened"
    result = parse_line(line)
    assert result["message"] == "Something unexpected happened"
    assert result["level"] == "unknown"


def test_parse_empty_line():
    assert parse_line("") == {}
    assert parse_line("   ") == {}


def test_extract_level_known():
    parsed = {"level": "error", "message": "boom"}
    assert extract_level(parsed) == "error"


def test_extract_level_unknown():
    parsed = {"level": "unknown", "message": "hmm"}
    assert extract_level(parsed) is None


def test_extract_level_missing():
    assert extract_level({}) is None

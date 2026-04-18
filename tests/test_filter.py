"""Tests for logwatch.filter module."""

import pytest
from logwatch.filter import (
    filter_by_level,
    filter_by_pattern,
    filter_by_field,
    build_filter,
)


SAMPLE_ERROR = {"level": "error", "message": "Disk quota exceeded", "host": "web-01"}
SAMPLE_INFO = {"level": "info", "message": "Server started", "host": "web-02"}
SAMPLE_DEBUG = {"level": "debug", "message": "Connecting to database", "host": "db-01"}


def test_filter_by_level_passes_equal():
    assert filter_by_level(SAMPLE_ERROR, "error") is True


def test_filter_by_level_passes_higher():
    assert filter_by_level(SAMPLE_ERROR, "warn") is True


def test_filter_by_level_blocks_lower():
    assert filter_by_level(SAMPLE_DEBUG, "info") is False


def test_filter_by_level_case_insensitive():
    assert filter_by_level(SAMPLE_INFO, "INFO") is True


def test_filter_by_level_missing_defaults_info():
    assert filter_by_level({"message": "no level"}, "debug") is True


def test_filter_by_pattern_matches_message():
    assert filter_by_pattern(SAMPLE_ERROR, r"disk") is True


def test_filter_by_pattern_matches_field_value():
    assert filter_by_pattern(SAMPLE_ERROR, r"web-\d+") is True


def test_filter_by_pattern_no_match():
    assert filter_by_pattern(SAMPLE_INFO, r"quota") is False


def test_filter_by_field_match():
    assert filter_by_field(SAMPLE_ERROR, "host", "web-01") is True


def test_filter_by_field_case_insensitive():
    assert filter_by_field(SAMPLE_ERROR, "level", "ERROR") is True


def test_filter_by_field_missing_field():
    assert filter_by_field(SAMPLE_INFO, "service", "api") is False


def test_build_filter_no_criteria_passes_all():
    f = build_filter()
    assert f(SAMPLE_DEBUG) is True


def test_build_filter_combined_passes():
    f = build_filter(min_level="warn", pattern=r"quota")
    assert f(SAMPLE_ERROR) is True


def test_build_filter_combined_blocks_on_level():
    f = build_filter(min_level="error", pattern=r"started")
    assert f(SAMPLE_INFO) is False


def test_build_filter_with_field():
    f = build_filter(min_level="info", field="host", field_value="web-02")
    assert f(SAMPLE_INFO) is True
    assert f(SAMPLE_ERROR) is False

"""Tests for logwatch.watchdog_config."""
from __future__ import annotations

import pytest

from logwatch.watchdog_config import (
    build_watchdogs,
    default_watchdog_config,
    load_watchdog_config_from_dict,
)
from logwatch.watchdog import Watchdog


def test_load_dict_sets_name():
    cfg = load_watchdog_config_from_dict({"name": "prod", "silence_window": 30})
    assert cfg.name == "prod"


def test_load_dict_sets_silence_window():
    cfg = load_watchdog_config_from_dict({"name": "x", "silence_window": "45"})
    assert cfg.silence_window == 45.0


def test_load_dict_missing_window_raises():
    with pytest.raises((ValueError, KeyError)):
        load_watchdog_config_from_dict({"name": "x"})


def test_load_dict_sets_level_filter():
    cfg = load_watchdog_config_from_dict(
        {"name": "x", "silence_window": 10, "level_filter": "error"}
    )
    assert cfg.level_filter == "error"


def test_load_dict_defaults_level_filter_to_none():
    cfg = load_watchdog_config_from_dict({"name": "x", "silence_window": 10})
    assert cfg.level_filter is None


def test_load_dict_defaults_name_to_unnamed():
    cfg = load_watchdog_config_from_dict({"silence_window": 20})
    assert cfg.name == "unnamed"


def test_default_watchdog_config_valid():
    cfg = default_watchdog_config()
    assert cfg.silence_window > 0
    assert cfg.name == "default"


def test_build_watchdogs_returns_instances():
    wds = build_watchdogs([
        {"name": "a", "silence_window": 10},
        {"name": "b", "silence_window": 20},
    ])
    assert len(wds) == 2
    assert all(isinstance(w, Watchdog) for w in wds)


def test_build_watchdogs_empty_list():
    assert build_watchdogs([]) == []

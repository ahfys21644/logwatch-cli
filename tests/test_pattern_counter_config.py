"""Tests for logwatch/pattern_counter_config.py."""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from logwatch.pattern_counter import PatternCounter, PatternCounterConfig
from logwatch.pattern_counter_config import (
    build_counters,
    default_pattern_counter_config,
    load_pattern_counter_from_dict,
    load_pattern_counters_from_yaml,
)


def test_load_dict_sets_name():
    cfg = load_pattern_counter_from_dict(
        {"name": "my-rule", "pattern": "fail", "window": 30, "threshold": 5}
    )
    assert cfg.name == "my-rule"


def test_load_dict_sets_pattern():
    cfg = load_pattern_counter_from_dict(
        {"pattern": "error", "window": 10, "threshold": 2}
    )
    assert cfg.pattern == "error"


def test_load_dict_sets_window():
    cfg = load_pattern_counter_from_dict(
        {"pattern": "x", "window": "45", "threshold": 1}
    )
    assert cfg.window == 45.0


def test_load_dict_sets_threshold():
    cfg = load_pattern_counter_from_dict(
        {"pattern": "x", "window": 10, "threshold": "7"}
    )
    assert cfg.threshold == 7


def test_load_dict_sets_level_filter():
    cfg = load_pattern_counter_from_dict(
        {"pattern": "x", "window": 10, "threshold": 1, "level_filter": "warn"}
    )
    assert cfg.level_filter == "warn"


def test_load_dict_default_name():
    cfg = load_pattern_counter_from_dict({"pattern": "x", "window": 5, "threshold": 1})
    assert cfg.name == "unnamed"


def test_load_dict_missing_pattern_raises():
    with pytest.raises(KeyError):
        load_pattern_counter_from_dict({"window": 5, "threshold": 1})


def test_default_config_is_valid():
    cfg = default_pattern_counter_config()
    assert isinstance(cfg, PatternCounterConfig)
    assert cfg.threshold > 0
    assert cfg.window > 0


def test_build_counters_returns_list():
    configs = [
        PatternCounterConfig(name="a", pattern="x", window=5.0, threshold=2),
        PatternCounterConfig(name="b", pattern="y", window=10.0, threshold=3),
    ]
    counters = build_counters(configs)
    assert len(counters) == 2
    assert all(isinstance(c, PatternCounter) for c in counters)


def test_load_from_yaml(tmp_path: Path):
    yaml_content = textwrap.dedent(
        """\
        - name: yaml-rule
          pattern: "timeout"
          window: 60
          threshold: 4
          level_filter: warn
        """
    )
    p = tmp_path / "counters.yaml"
    p.write_text(yaml_content)
    configs = load_pattern_counters_from_yaml(str(p))
    assert len(configs) == 1
    assert configs[0].name == "yaml-rule"
    assert configs[0].threshold == 4
    assert configs[0].level_filter == "warn"

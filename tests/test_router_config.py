"""Tests for logwatch.router_config loader."""
import textwrap
import pytest

from logwatch.router_config import (
    load_router_config_from_list,
    load_router_config_from_yaml,
    default_router_config,
    DEFAULT_ROUTER_CONFIG,
)


def test_load_list_preserves_name():
    cfg = load_router_config_from_list([{"name": "my_rule", "sink": "stdout"}])
    assert cfg[0]["name"] == "my_rule"


def test_load_list_defaults_name_to_unnamed():
    cfg = load_router_config_from_list([{"sink": "stdout"}])
    assert cfg[0]["name"] == "unnamed"


def test_load_list_defaults_stop_to_true():
    cfg = load_router_config_from_list([{"sink": "stdout"}])
    assert cfg[0]["stop"] is True


def test_load_list_respects_stop_false():
    cfg = load_router_config_from_list([{"sink": "stdout", "stop": False}])
    assert cfg[0]["stop"] is False


def test_load_list_includes_optional_level():
    cfg = load_router_config_from_list([{"sink": "stdout", "level": "warn"}])
    assert cfg[0]["level"] == "warn"


def test_load_list_includes_optional_pattern():
    cfg = load_router_config_from_list([{"sink": "stdout", "pattern": "error.*"}])
    assert cfg[0]["pattern"] == "error.*"


def test_load_list_raises_without_sink():
    with pytest.raises(ValueError):
        load_router_config_from_list([{"name": "x"}])


def test_load_yaml_parses_routes(tmp_path):
    yaml_content = textwrap.dedent("""\
        routes:
          - name: errors
            level: error
            sink: stderr
            stop: true
          - name: default
            sink: stdout
    """)
    p = tmp_path / "routes.yaml"
    p.write_text(yaml_content)
    cfg = load_router_config_from_yaml(str(p))
    assert len(cfg) == 2
    assert cfg[0]["name"] == "errors"
    assert cfg[1]["sink"] == "stdout"


def test_load_yaml_empty_file_returns_empty(tmp_path):
    p = tmp_path / "empty.yaml"
    p.write_text("")
    cfg = load_router_config_from_yaml(str(p))
    assert cfg == []


def test_default_router_config_is_valid():
    cfg = default_router_config()
    assert all("sink" in r for r in cfg)


def test_default_router_config_matches_constant():
    cfg = default_router_config()
    assert len(cfg) == len(DEFAULT_ROUTER_CONFIG)

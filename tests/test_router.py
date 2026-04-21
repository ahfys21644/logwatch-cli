"""Tests for logwatch.router and logwatch.router_config."""
import pytest
from unittest.mock import MagicMock

from logwatch.router import RouteRule, Router, build_router
from logwatch.router_config import (
    load_router_config_from_list,
    default_router_config,
)


def _entry(level="info", message="hello"):
    return {"level": level, "message": message, "timestamp": "2024-01-01T00:00:00"}


@pytest.fixture
def mock_sink():
    sink = MagicMock()
    sink.write_entry = MagicMock()
    return sink


@pytest.fixture
def alt_sink():
    sink = MagicMock()
    sink.write_entry = MagicMock()
    return sink


def test_route_matches_predicate(mock_sink):
    router = Router()
    router.add_rule(RouteRule("r1", lambda e: e["level"] == "error", mock_sink))
    router.route(_entry(level="error"))
    mock_sink.write_entry.assert_called_once()


def test_route_no_match_uses_default(mock_sink, alt_sink):
    router = Router(default_sink=alt_sink)
    router.add_rule(RouteRule("r1", lambda e: e["level"] == "error", mock_sink))
    router.route(_entry(level="info"))
    mock_sink.write_entry.assert_not_called()
    alt_sink.write_entry.assert_called_once()


def test_stop_prevents_further_rules(mock_sink, alt_sink):
    router = Router()
    router.add_rule(RouteRule("r1", lambda e: True, mock_sink, stop=True))
    router.add_rule(RouteRule("r2", lambda e: True, alt_sink, stop=True))
    router.route(_entry())
    mock_sink.write_entry.assert_called_once()
    alt_sink.write_entry.assert_not_called()


def test_no_stop_continues_to_next_rule(mock_sink, alt_sink):
    router = Router()
    router.add_rule(RouteRule("r1", lambda e: True, mock_sink, stop=False))
    router.add_rule(RouteRule("r2", lambda e: True, alt_sink, stop=True))
    router.route(_entry())
    mock_sink.write_entry.assert_called_once()
    alt_sink.write_entry.assert_called_once()


def test_route_returns_matched_rule_name(mock_sink):
    router = Router()
    router.add_rule(RouteRule("errors", lambda e: True, mock_sink))
    result = router.route(_entry())
    assert result == "errors"


def test_route_returns_none_when_no_match(mock_sink):
    router = Router()
    router.add_rule(RouteRule("r1", lambda e: False, mock_sink))
    result = router.route(_entry())
    assert result is None


def test_route_all_processes_multiple_entries(mock_sink):
    router = Router()
    router.add_rule(RouteRule("all", lambda e: True, mock_sink))
    router.route_all([_entry(), _entry(), _entry()])
    assert mock_sink.write_entry.call_count == 3


def test_build_router_level_rule(mock_sink, alt_sink):
    cfg = [{"name": "err", "level": "error", "sink": "err_sink", "stop": True}]
    router = build_router(cfg, {"err_sink": mock_sink}, default_sink=alt_sink)
    router.route(_entry(level="error"))
    mock_sink.write_entry.assert_called_once()
    alt_sink.write_entry.assert_not_called()


def test_load_router_config_missing_sink_raises():
    with pytest.raises(ValueError, match="sink"):
        load_router_config_from_list([{"name": "bad", "level": "error"}])


def test_default_router_config_returns_list():
    cfg = default_router_config()
    assert isinstance(cfg, list)
    assert len(cfg) >= 1
    assert all("sink" in r for r in cfg)

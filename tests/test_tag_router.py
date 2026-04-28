"""Tests for logwatch.tag_router."""
import pytest
from logwatch.tag_router import TagRule, TagRouter, make_level_tag_router


def _entry(level="INFO", message="hello", **kw):
    return {"level": level, "message": message, **kw}


@pytest.fixture()
def collected():
    return []


@pytest.fixture()
def router(collected):
    r = TagRouter(default_sink=collected.append)
    r.add_rule(TagRule("error", lambda e: str(e.get("level", "")).upper() == "ERROR"))
    r.add_rule(TagRule("warn", lambda e: str(e.get("level", "")).upper() in ("WARN", "WARNING")))
    return r


def test_tag_entry_error(router):
    tags = router.tag_entry(_entry(level="ERROR"))
    assert "error" in tags


def test_tag_entry_warn(router):
    tags = router.tag_entry(_entry(level="WARN"))
    assert "warn" in tags


def test_tag_entry_info_no_tags(router):
    tags = router.tag_entry(_entry(level="INFO"))
    assert tags == set()


def test_route_dispatches_to_sink(router):
    received = []
    router.register_sink("error", received.append)
    router.route(_entry(level="ERROR"))
    assert len(received) == 1


def test_route_enriches_with_tags(router):
    received = []
    router.register_sink("error", received.append)
    router.route(_entry(level="ERROR"))
    assert "tags" in received[0]
    assert "error" in received[0]["tags"]


def test_route_falls_back_to_default_sink(collected):
    router = TagRouter(default_sink=collected.append)
    router.route(_entry(level="INFO"))
    assert len(collected) == 1


def test_route_no_default_no_match_silent(router):
    router.default_sink = None
    router.route(_entry(level="INFO"))  # should not raise


def test_route_all_processes_every_entry(router):
    received = []
    router.register_sink("error", received.append)
    router.route_all([_entry(level="ERROR"), _entry(level="ERROR")])
    assert len(received) == 2


def test_make_level_tag_router_routes_error():
    errors, warns = [], []
    r = make_level_tag_router(errors.append, warns.append)
    r.route(_entry(level="ERROR"))
    assert len(errors) == 1 and len(warns) == 0


def test_make_level_tag_router_routes_warn():
    errors, warns = [], []
    r = make_level_tag_router(errors.append, warns.append)
    r.route(_entry(level="WARNING"))
    assert len(warns) == 1 and len(errors) == 0


def test_tags_field_is_sorted_list(router):
    received = []
    router.add_rule(TagRule("alpha", lambda e: True))
    router.register_sink("alpha", received.append)
    router.route(_entry(level="INFO"))
    assert received[0]["tags"] == sorted(received[0]["tags"])

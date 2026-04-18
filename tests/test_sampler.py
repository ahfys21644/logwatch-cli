"""Tests for logwatch.sampler."""
import pytest
from logwatch.sampler import Sampler, build_sampler


@pytest.fixture()
def entry():
    def _make(level="info", msg="hello"):
        return {"level": level, "message": msg, "timestamp": "2024-01-01T00:00:00"}
    return _make


def test_rate_one_keeps_all(entry):
    s = Sampler(rate=1)
    assert all(s.should_keep(entry()) for _ in range(10))


def test_rate_two_keeps_every_other(entry):
    s = Sampler(rate=2)
    results = [s.should_keep(entry()) for _ in range(6)]
    assert results == [True, False, True, False, True, False]


def test_rate_three_keeps_first_then_every_third(entry):
    s = Sampler(rate=3)
    results = [s.should_keep(entry()) for _ in range(7)]
    assert results[0] is True
    assert results[3] is True
    assert results[6] is True
    assert results[1] is False
    assert results[2] is False


def test_counters_are_per_level(entry):
    s = Sampler(rate=2)
    # first of each level should be kept
    assert s.should_keep(entry("info")) is True
    assert s.should_keep(entry("error")) is True
    # second of each level should be dropped
    assert s.should_keep(entry("info")) is False
    assert s.should_keep(entry("error")) is False


def test_missing_level_treated_as_unknown(entry):
    s = Sampler(rate=2)
    e = {"message": "no level"}
    assert s.should_keep(e) is True
    assert s.should_keep(e) is False


def test_reset_all_clears_counters(entry):
    s = Sampler(rate=2)
    s.should_keep(entry())  # count=1 keep
    s.should_keep(entry())  # count=2 drop
    s.reset()
    assert s.should_keep(entry()) is True  # restarted


def test_reset_specific_level(entry):
    s = Sampler(rate=2)
    s.should_keep(entry("info"))
    s.should_keep(entry("info"))  # drop
    s.should_keep(entry("error"))
    s.reset(level="info")
    assert s.should_keep(entry("info")) is True   # reset
    assert s.should_keep(entry("error")) is False  # error still at count 2


def test_stats_returns_counters(entry):
    s = Sampler(rate=2)
    s.should_keep(entry("info"))
    s.should_keep(entry("info"))
    st = s.stats()
    assert st["info"] == 2


def test_invalid_rate_raises():
    with pytest.raises(ValueError):
        Sampler(rate=0)


def test_build_sampler_factory():
    s = build_sampler(rate=5)
    assert isinstance(s, Sampler)
    assert s.rate == 5

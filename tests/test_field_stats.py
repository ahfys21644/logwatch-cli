"""Tests for logwatch.field_stats."""
import pytest

from logwatch.field_stats import FieldStats


@pytest.fixture()
def stats() -> FieldStats:
    return FieldStats(fields=["level", "service"])


def _entry(level: str = "info", service: str = "api") -> dict:
    return {"level": level, "service": service, "message": "hello"}


# --- construction ---

def test_empty_fields_raises() -> None:
    with pytest.raises(ValueError, match="fields must not be empty"):
        FieldStats(fields=[])


def test_zero_max_values_raises() -> None:
    with pytest.raises(ValueError, match="max_values must be"):
        FieldStats(fields=["level"], max_values=0)


# --- record / top ---

def test_record_increments_count(stats: FieldStats) -> None:
    stats.record(_entry("info"))
    stats.record(_entry("info"))
    top = stats.top("level")
    assert top[0] == ("info", 2)


def test_top_returns_sorted_descending(stats: FieldStats) -> None:
    for _ in range(3):
        stats.record(_entry("error"))
    for _ in range(5):
        stats.record(_entry("info"))
    stats.record(_entry("warn"))
    top = stats.top("level")
    assert top[0][0] == "info"
    assert top[1][0] == "error"
    assert top[2][0] == "warn"


def test_top_respects_n_limit(stats: FieldStats) -> None:
    for val in ["a", "b", "c", "d"]:
        stats.record({"level": val, "service": "x"})
    assert len(stats.top("level", n=2)) == 2


def test_missing_field_value_skipped(stats: FieldStats) -> None:
    stats.record({"message": "no level here"})
    assert stats.total("level") == 0


def test_unknown_field_raises_key_error(stats: FieldStats) -> None:
    with pytest.raises(KeyError):
        stats.top("nonexistent")


# --- record_all ---

def test_record_all_processes_multiple_entries(stats: FieldStats) -> None:
    entries = [_entry("debug"), _entry("info"), _entry("debug")]
    stats.record_all(entries)
    assert stats.total("level") == 3


# --- total / unique_count ---

def test_total_counts_all_observations(stats: FieldStats) -> None:
    stats.record(_entry("info"))
    stats.record(_entry("info"))
    stats.record(_entry("error"))
    assert stats.total("level") == 3


def test_unique_count_distinct_values(stats: FieldStats) -> None:
    stats.record(_entry("info"))
    stats.record(_entry("info"))
    stats.record(_entry("error"))
    assert stats.unique_count("level") == 2


def test_unique_count_unknown_field_raises(stats: FieldStats) -> None:
    with pytest.raises(KeyError):
        stats.unique_count("bogus")


# --- max_values cap ---

def test_max_values_caps_distinct_keys() -> None:
    fs = FieldStats(fields=["code"], max_values=3)
    for i in range(10):
        fs.record({"code": str(i)})
    assert fs.unique_count("code") == 3


def test_existing_key_still_increments_beyond_cap() -> None:
    fs = FieldStats(fields=["code"], max_values=2)
    fs.record({"code": "a"})
    fs.record({"code": "b"})
    fs.record({"code": "a"})  # already tracked — should increment
    assert fs.top("code")[0] == ("a", 2)


# --- reset ---

def test_reset_single_field_clears_counts(stats: FieldStats) -> None:
    stats.record(_entry("info"))
    stats.reset("level")
    assert stats.total("level") == 0


def test_reset_all_fields(stats: FieldStats) -> None:
    stats.record(_entry("info", "api"))
    stats.reset()
    assert stats.total("level") == 0
    assert stats.total("service") == 0


def test_reset_unknown_field_raises(stats: FieldStats) -> None:
    with pytest.raises(KeyError):
        stats.reset("bogus")


# --- summary ---

def test_summary_contains_all_tracked_fields(stats: FieldStats) -> None:
    stats.record(_entry("info", "api"))
    result = stats.summary()
    assert set(result.keys()) == {"level", "service"}


def test_summary_values_are_sorted_tuples(stats: FieldStats) -> None:
    stats.record(_entry("error"))
    stats.record(_entry("error"))
    stats.record(_entry("info"))
    top = stats.summary()["level"]
    assert top[0] == ("error", 2)

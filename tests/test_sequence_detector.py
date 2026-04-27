"""Tests for SequenceConfig, SequenceDetector, and sequence_middleware."""
from __future__ import annotations

import time
from typing import Dict

import pytest

from logwatch.sequence_detector import SequenceConfig, SequenceDetector, SequenceEvent
from logwatch.sequence_middleware import make_login_sequence_detector, sequence_iter


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def cfg() -> SequenceConfig:
    return SequenceConfig(name="test_seq", steps=[r"start", r"middle", r"end"], window=5.0)


@pytest.fixture()
def detector(cfg: SequenceConfig) -> SequenceDetector:
    return SequenceDetector(config=cfg)


def _entry(msg: str, level: str = "info") -> Dict:
    return {"message": msg, "level": level, "timestamp": "2024-01-01T00:00:00Z"}


# ---------------------------------------------------------------------------
# SequenceConfig validation
# ---------------------------------------------------------------------------

def test_config_rejects_single_step() -> None:
    with pytest.raises(ValueError, match="at least 2 steps"):
        SequenceConfig(name="x", steps=["only"], window=10.0)


def test_config_rejects_zero_window() -> None:
    with pytest.raises(ValueError, match="positive"):
        SequenceConfig(name="x", steps=["a", "b"], window=0.0)


def test_config_rejects_negative_window() -> None:
    with pytest.raises(ValueError, match="positive"):
        SequenceConfig(name="x", steps=["a", "b"], window=-1.0)


# ---------------------------------------------------------------------------
# SequenceDetector — happy path
# ---------------------------------------------------------------------------

def test_partial_sequence_returns_none(detector: SequenceDetector) -> None:
    assert detector.feed(_entry("start here")) is None


def test_full_sequence_returns_event(detector: SequenceDetector) -> None:
    detector.feed(_entry("start here"))
    detector.feed(_entry("middle part"))
    event = detector.feed(_entry("end reached"))
    assert isinstance(event, SequenceEvent)
    assert event.config_name == "test_seq"
    assert len(event.matched_messages) == 3


def test_event_str_contains_name(detector: SequenceDetector) -> None:
    detector.feed(_entry("start here"))
    detector.feed(_entry("middle part"))
    event = detector.feed(_entry("end reached"))
    assert "test_seq" in str(event)


def test_detector_resets_after_completion(detector: SequenceDetector) -> None:
    for msg in ("start here", "middle part", "end reached"):
        detector.feed(_entry(msg))
    # second round should work
    detector.feed(_entry("start here"))
    detector.feed(_entry("middle part"))
    event = detector.feed(_entry("end reached"))
    assert event is not None


def test_out_of_order_does_not_complete(detector: SequenceDetector) -> None:
    detector.feed(_entry("middle part"))
    detector.feed(_entry("start here"))
    result = detector.feed(_entry("end reached"))
    assert result is None


def test_level_filter_skips_non_matching(cfg: SequenceConfig) -> None:
    cfg2 = SequenceConfig(name="lf", steps=["a", "b"], window=5.0, level_filter="error")
    det = SequenceDetector(config=cfg2)
    det.feed(_entry("a", level="info"))
    result = det.feed(_entry("b", level="info"))
    assert result is None


def test_window_expiry_resets_state(detector: SequenceDetector, monkeypatch) -> None:
    monkeypatch.setattr("logwatch.sequence_detector.time.time", lambda: 0.0)
    detector.feed(_entry("start here"))
    # advance time past window
    monkeypatch.setattr("logwatch.sequence_detector.time.time", lambda: 10.0)
    detector.feed(_entry("middle part"))
    result = detector.feed(_entry("end reached"))
    assert result is None


def test_on_event_callback_called(detector: SequenceDetector) -> None:
    fired: list = []
    detector.on_event = fired.append
    for msg in ("start here", "middle part", "end reached"):
        detector.feed(_entry(msg))
    assert len(fired) == 1
    assert fired[0].config_name == "test_seq"


# ---------------------------------------------------------------------------
# sequence_iter middleware
# ---------------------------------------------------------------------------

def test_sequence_iter_passes_all_entries(detector: SequenceDetector) -> None:
    entries = [_entry("start here"), _entry("middle part"), _entry("end reached")]
    result = list(sequence_iter(entries, [detector]))
    assert len(result) == 3


def test_sequence_iter_fires_callback(detector: SequenceDetector) -> None:
    fired: list = []
    entries = [_entry("start here"), _entry("middle part"), _entry("end reached")]
    list(sequence_iter(entries, [detector], on_event=fired.append))
    assert len(fired) == 1


# ---------------------------------------------------------------------------
# Convenience factory
# ---------------------------------------------------------------------------

def test_login_sequence_detector_factory() -> None:
    det = make_login_sequence_detector()
    assert det.config.name == "login_flow"
    assert len(det.config.steps) == 3

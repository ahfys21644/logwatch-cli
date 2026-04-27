"""Session replay: replay a saved snapshot through the active pipeline."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable, Iterator, List, Optional

from logwatch.snapshot import load_snapshot
from logwatch.replay import replay_from_jsonl
from logwatch.pipeline import build_pipeline, process
from logwatch.filter import build_filter
from logwatch.stats import SessionStats


@dataclass
class SessionReplayConfig:
    """Configuration for replaying a saved session."""
    snapshot_name: str
    min_level: str = "debug"
    pattern: Optional[str] = None
    limit: Optional[int] = None
    speed: float = 1.0  # reserved for future timed replay
    tags: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.speed <= 0:
            raise ValueError("speed must be positive")
        if self.limit is not None and self.limit < 1:
            raise ValueError("limit must be >= 1 when provided")


def replay_session(
    config: SessionReplayConfig,
    on_entry: Callable[[dict], None],
    on_alert: Optional[Callable[[object], None]] = None,
) -> SessionStats:
    """Load a snapshot and replay all stored entries through a fresh pipeline.

    Returns a :class:`~logwatch.stats.SessionStats` for the replayed session.
    """
    snapshot = load_snapshot(config.snapshot_name)
    entries: Iterable[dict] = snapshot.get("entries", [])

    filt = build_filter(min_level=config.min_level, pattern=config.pattern)
    stats = SessionStats()
    count = 0

    for entry in entries:
        if config.limit is not None and count >= config.limit:
            break
        if not filt(entry):
            continue
        stats.record_entry(entry)
        on_entry(entry)
        count += 1

    return stats


def iter_replay_session(
    config: SessionReplayConfig,
) -> Iterator[dict]:
    """Yield entries from a saved snapshot, applying configured filters."""
    snapshot = load_snapshot(config.snapshot_name)
    entries: Iterable[dict] = snapshot.get("entries", [])
    filt = build_filter(min_level=config.min_level, pattern=config.pattern)
    count = 0

    for entry in entries:
        if config.limit is not None and count >= config.limit:
            break
        if filt(entry):
            yield entry
            count += 1

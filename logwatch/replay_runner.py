"""High-level replay runner: feeds replayed entries through the active pipeline."""

from __future__ import annotations

from typing import Callable, Iterable, Optional

from logwatch.pipeline import process
from logwatch.replay import replay_from_file, replay_from_jsonl, replay_from_snapshot
from logwatch.stats import SessionStats


SourceKind = str  # "file" | "jsonl" | "snapshot"


def run_replay(
    source: str,
    *,
    kind: SourceKind = "file",
    pipeline: list[Callable[[dict], Optional[dict]]],
    sink: Callable[[dict], None],
    stats: Optional[SessionStats] = None,
    limit: Optional[int] = None,
) -> SessionStats:
    """Replay *source* through *pipeline*, sending accepted entries to *sink*.

    Returns the populated :class:`SessionStats` instance.
    """
    if stats is None:
        stats = SessionStats()

    entries: Iterable[dict]
    if kind == "snapshot":
        entries = replay_from_snapshot(source, limit=limit)
    elif kind == "jsonl":
        entries = replay_from_jsonl(source, limit=limit)
    else:
        entries = replay_from_file(source, limit=limit)

    for entry in entries:
        stats.record_entry(entry)
        result = process(entry, pipeline)
        if result is not None:
            sink(result)

    return stats

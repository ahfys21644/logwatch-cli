"""Replay historical log entries through the pipeline from a snapshot or file."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator, Optional

from logwatch.parser import parse_line
from logwatch.snapshot import load_snapshot


def replay_from_file(path: str | Path, *, limit: Optional[int] = None) -> Iterator[dict]:
    """Yield parsed log entries from a plain log file, up to *limit* lines."""
    path = Path(path)
    count = 0
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        for raw in fh:
            raw = raw.rstrip("\n")
            if not raw:
                continue
            entry = parse_line(raw)
            yield entry
            count += 1
            if limit is not None and count >= limit:
                break


def replay_from_snapshot(name: str, *, limit: Optional[int] = None) -> Iterator[dict]:
    """Yield log entries stored inside a snapshot's *entries* list."""
    data = load_snapshot(name)
    entries = data.get("entries", [])
    if limit is not None:
        entries = entries[:limit]
    for entry in entries:
        yield entry


def replay_from_jsonl(path: str | Path, *, limit: Optional[int] = None) -> Iterator[dict]:
    """Yield entries from a newline-delimited JSON (JSONL) file."""
    path = Path(path)
    count = 0
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                entry = parse_line(line)
            yield entry
            count += 1
            if limit is not None and count >= limit:
                break

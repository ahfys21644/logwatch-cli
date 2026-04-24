"""Checkpoint-aware tailer — resumes from the last saved position."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Generator, Optional

from logwatch.checkpoint import load_checkpoint, save_checkpoint
from logwatch.parser import parse_line


def tail_from_checkpoint(
    log_path: str,
    *,
    checkpoint_dir: Optional[Path] = None,
    poll_interval: float = 0.25,
    save_every: int = 50,
) -> Generator[dict, None, None]:
    """Yield parsed log entries, starting from the last checkpointed offset.

    Saves the current offset every *save_every* lines so progress is durable.
    """
    offset = load_checkpoint(log_path, checkpoint_dir)
    lines_since_save = 0

    with open(log_path, "r", encoding="utf-8", errors="replace") as fh:
        fh.seek(offset)
        while True:
            line = fh.readline()
            if not line:
                time.sleep(poll_interval)
                continue
            entry = parse_line(line.rstrip("\n"))
            yield entry
            lines_since_save += 1
            if lines_since_save >= save_every:
                save_checkpoint(log_path, fh.tell(), checkpoint_dir)
                lines_since_save = 0


def replay_from_checkpoint(
    log_path: str,
    *,
    checkpoint_dir: Optional[Path] = None,
    limit: Optional[int] = None,
) -> list[dict]:
    """Read all lines from the checkpointed offset without blocking.

    Returns a list of parsed entries (up to *limit* if given).
    """
    offset = load_checkpoint(log_path, checkpoint_dir)
    entries: list[dict] = []
    with open(log_path, "r", encoding="utf-8", errors="replace") as fh:
        fh.seek(offset)
        for line in fh:
            entries.append(parse_line(line.rstrip("\n")))
            if limit is not None and len(entries) >= limit:
                break
    return entries

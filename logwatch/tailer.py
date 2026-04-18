"""Tail a log file and yield parsed log entries in real time."""

import time
import os
from typing import Iterator, Optional, Callable
from logwatch.parser import parse_line


def tail_file(
    path: str,
    poll_interval: float = 0.2,
    from_start: bool = False,
    on_rotate: Optional[Callable[[], None]] = None,
) -> Iterator[dict]:
    """Yield parsed log entries from *path*, following new lines as they appear.

    Handles log rotation by detecting inode changes.
    """
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        if not from_start:
            fh.seek(0, os.SEEK_END)
        current_inode = os.fstat(fh.fileno()).st_ino

        while True:
            line = fh.readline()
            if line:
                entry = parse_line(line.rstrip("\n"))
                yield entry
            else:
                # Check for rotation
                try:
                    new_inode = os.stat(path).st_ino
                except FileNotFoundError:
                    time.sleep(poll_interval)
                    continue

                if new_inode != current_inode:
                    if on_rotate:
                        on_rotate()
                    fh.close()
                    fh = open(path, "r", encoding="utf-8", errors="replace")
                    current_inode = new_inode
                else:
                    time.sleep(poll_interval)


def tail_lines(
    path: str,
    n: int = 20,
) -> list[dict]:
    """Return the last *n* parsed log entries from *path* without following."""
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        lines = fh.readlines()
    tail = lines[-n:] if len(lines) >= n else lines
    return [parse_line(line.rstrip("\n")) for line in tail]

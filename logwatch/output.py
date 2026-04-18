"""Output sink management: write formatted log entries to file or stdout."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import IO, Iterator

from logwatch.formatter import format_entry, format_alert


class OutputSink:
    """Writes formatted log entries and alerts to one or more destinations."""

    def __init__(self, file_path: str | None = None, no_color: bool = False):
        self._file_path = file_path
        self._no_color = no_color
        self._file_handle: IO[str] | None = None

    def open(self) -> None:
        if self._file_path:
            self._file_handle = open(self._file_path, "a", encoding="utf-8")

    def close(self) -> None:
        if self._file_handle:
            self._file_handle.close()
            self._file_handle = None

    def __enter__(self) -> "OutputSink":
        self.open()
        return self

    def __exit__(self, *args) -> None:
        self.close()

    def write_entry(self, entry: dict) -> None:
        line = format_entry(entry, colorize=not self._no_color)
        self._emit(line)

    def write_alert(self, rule_name: str, entry: dict) -> None:
        line = format_alert(rule_name, entry, colorize=not self._no_color)
        self._emit(line)

    def _emit(self, line: str) -> None:
        print(line, file=sys.stdout)
        if self._file_handle:
            self._file_handle.write(line + "\n")
            self._file_handle.flush()


def write_entries(entries: Iterator[dict], sink: OutputSink) -> int:
    """Write all entries to the sink. Returns count of entries written."""
    count = 0
    for entry in entries:
        sink.write_entry(entry)
        count += 1
    return count

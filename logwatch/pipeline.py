"""Pipeline: wires together tailer, filter, alerts, and output sink."""

from __future__ import annotations

from typing import Iterator

from logwatch.filter import combined
from logwatch.alerts import check_alerts, AlertRule
from logwatch.output import OutputSink


def run_pipeline(
    entries: Iterator[dict],
    filters,
    rules: list[AlertRule],
    sink: OutputSink,
    on_alert=None,
) -> dict:
    """
    Process log entries through filter -> alert check -> output.

    Returns summary dict with counts.
    """
    stats = {"total": 0, "passed": 0, "alerts": 0}

    filter_fn = combined(filters) if filters else lambda e: True

    for entry in entries:
        stats["total"] += 1
        if not filter_fn(entry):
            continue
        stats["passed"] += 1
        sink.write_entry(entry)

        triggered = check_alerts(entry, rules)
        for rule in triggered:
            stats["alerts"] += 1
            sink.write_alert(rule.name, entry)
            if on_alert:
                on_alert(rule, entry)

    return stats


def build_pipeline(
    entries: Iterator[dict],
    filters=None,
    rules: list[AlertRule] | None = None,
    file_path: str | None = None,
    no_color: bool = False,
    on_alert=None,
) -> dict:
    """Convenience wrapper that manages the sink lifecycle."""
    with OutputSink(file_path=file_path, no_color=no_color) as sink:
        return run_pipeline(
            entries,
            filters or [],
            rules or [],
            sink,
            on_alert=on_alert,
        )

"""Pipeline orchestration — wires parser, filters, dedup, sampler, alerts, output."""
from __future__ import annotations
from typing import Iterable, List, Callable

from logwatch.filter import combined
from logwatch.alerts import check_alerts, AlertRule
from logwatch.dedup import DedupFilter
from logwatch.sampler import Sampler
from logwatch.stats import SessionStats
from logwatch.output import OutputSink


def build_pipeline(
    *,
    filters: List[Callable[[dict], bool]] | None = None,
    rules: List[AlertRule] | None = None,
    dedup: DedupFilter | None = None,
    sampler: Sampler | None = None,
    stats: SessionStats | None = None,
    sink: OutputSink,
) -> Callable[[dict], None]:
    """Return a callable that processes a single parsed log entry end-to-end."""
    _filters = filters or []
    _rules = rules or []

    def process(entry: dict) -> None:
        # 1. combined field/level/pattern filters
        if _filters and not combined(_filters)(entry):
            return
        # 2. deduplication
        if dedup is not None and dedup.is_duplicate(entry):
            return
        # 3. sampling
        if sampler is not None and not sampler.should_keep(entry):
            return
        # 4. stats
        if stats is not None:
            stats.record_entry(entry)
        # 5. output
        sink.write_entry(entry)
        # 6. alert evaluation
        triggered = check_alerts(entry, _rules)
        for rule, matched_entry in triggered:
            if stats is not None:
                stats.record_alert(rule.name)
            sink.write_alert(rule, matched_entry)

    return process


def run_pipeline(entries: Iterable[dict], process: Callable[[dict], None]) -> int:
    """Drive *process* over *entries*; return count of entries fed in."""
    count = 0
    for entry in entries:
        process(entry)
        count += 1
    return count

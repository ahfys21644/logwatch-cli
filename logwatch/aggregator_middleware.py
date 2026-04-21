"""Pipeline middleware that wraps an Aggregator, injecting summary entries."""
from __future__ import annotations

from typing import Callable, Iterable, Iterator, List, Optional

from logwatch.aggregator import Aggregator, build_aggregator

LogEntry = dict
Sink = Callable[[LogEntry], None]


def aggregating_step(
    aggregator: Aggregator,
    downstream: Sink,
) -> Sink:
    """Return a sink that feeds entries into *aggregator*.

    When the aggregator's window expires it forwards summary entries
    to *downstream* before the triggering entry itself.
    """
    def _step(entry: LogEntry) -> None:
        summaries = aggregator.feed(entry)
        if summaries:
            for summary in summaries:
                downstream(summary)
        downstream(entry)

    return _step


def aggregating_iter(
    aggregator: Aggregator,
    entries: Iterable[LogEntry],
) -> Iterator[LogEntry]:
    """Yield entries interleaved with aggregation summaries.

    A final :meth:`flush` is performed after the iterable is exhausted
    so no buffered data is lost.
    """
    for entry in entries:
        summaries = aggregator.feed(entry)
        if summaries:
            yield from summaries
        yield entry

    # flush any remaining buckets
    for summary in aggregator.flush():
        yield summary


def make_level_aggregator(
    window_seconds: float = 10.0,
    min_count: int = 2,
) -> Aggregator:
    """Convenience factory: aggregate by *level* with sensible defaults."""
    return build_aggregator(
        group_by="level",
        window_seconds=window_seconds,
        min_count=min_count,
        label="level-summary",
    )

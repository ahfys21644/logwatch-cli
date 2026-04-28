"""Middleware helpers that integrate TagRouter into a processing pipeline."""
from __future__ import annotations

from typing import Callable, Dict, Iterable, Iterator, List, Optional

from logwatch.tag_router import TagRouter

LogEntry = Dict[str, object]
Sink = Callable[[LogEntry], None]


def tag_step(router: TagRouter) -> Callable[[LogEntry], Optional[LogEntry]]:
    """Return a pipeline step that tags the entry *and* passes it downstream.

    The entry returned always carries a ``tags`` field; routing side-effects
    (dispatching to per-tag sinks) happen as a by-product.
    """
    def _step(entry: LogEntry) -> Optional[LogEntry]:
        tags = router.tag_entry(entry)
        enriched = {**entry, "tags": sorted(tags)}
        for tag in tags:
            sink = router.sinks.get(tag)
            if sink is not None:
                sink(enriched)
        return enriched

    return _step


def tag_iter(
    entries: Iterable[LogEntry],
    router: TagRouter,
) -> Iterator[LogEntry]:
    """Yield every entry after tagging; side-route to registered sinks."""
    for entry in entries:
        tags = router.tag_entry(entry)
        enriched = {**entry, "tags": sorted(tags)}
        for tag in tags:
            sink = router.sinks.get(tag)
            if sink is not None:
                sink(enriched)
        yield enriched


def make_tag_splitter(
    router: TagRouter,
    pass_through: bool = True,
) -> Callable[[LogEntry], Optional[LogEntry]]:
    """Return a step that routes by tag and optionally drops the entry from
    the main pipeline (``pass_through=False``).
    """
    def _step(entry: LogEntry) -> Optional[LogEntry]:
        tags = router.tag_entry(entry)
        enriched = {**entry, "tags": sorted(tags)}
        for tag in tags:
            sink = router.sinks.get(tag)
            if sink is not None:
                sink(enriched)
        return enriched if pass_through else None

    return _step

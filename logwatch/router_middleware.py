"""Middleware helpers that wrap a Router into a pipeline step."""
from __future__ import annotations

from typing import Iterable, Iterator

from logwatch.router import Router


def routing_step(router: Router, entries: Iterable[dict]) -> Iterator[dict]:
    """Pass each entry through the router and yield every entry unchanged.

    The router handles side-effect dispatch (writing to sinks); this step
    keeps entries flowing through the rest of the pipeline.
    """
    for entry in entries:
        router.route(entry)
        yield entry


def routing_sink(router: Router, entries: Iterable[dict]) -> None:
    """Terminal pipeline step: route all entries, yield nothing."""
    router.route_all(entries)


def make_level_splitter(low_sink, high_sink, threshold: str = "error"):
    """Return a simple two-way router that splits on level threshold.

    Entries at or above *threshold* are dispatched to *high_sink*; all
    other entries fall through to *low_sink* (the router's default sink).

    Args:
        low_sink:  Sink that receives entries below the threshold.
        high_sink: Sink that receives entries at or above the threshold.
        threshold: Minimum level string that routes to *high_sink*
                   (default: ``"error"``).

    Returns:
        A configured :class:`~logwatch.router.Router` instance.
    """
    from logwatch.router import RouteRule, Router
    from logwatch.filter import filter_by_level

    router = Router(default_sink=low_sink)
    router.add_rule(RouteRule(
        name="high_level",
        predicate=filter_by_level(threshold),
        sink=high_sink,
        stop=True,
    ))
    return router

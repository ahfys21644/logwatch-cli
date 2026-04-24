"""Pipeline middleware that applies a RetentionPolicy to a stream of entries."""
from __future__ import annotations

import time
from typing import Callable, Iterable, Iterator, List, Optional

from logwatch.retention import RetentionPolicy


def make_retention_step(
    policy: RetentionPolicy,
    clock: Callable[[], float] = time.time,
) -> Callable[[dict], Optional[dict]]:
    """Return a single-entry transformer step backed by *policy*.

    The *clock* parameter is injectable for deterministic testing.
    """

    def _step(entry: dict) -> Optional[dict]:
        return policy.apply(entry, now=clock())

    return _step


def retention_iter(
    entries: Iterable[dict],
    policy: RetentionPolicy,
    clock: Callable[[], float] = time.time,
) -> Iterator[dict]:
    """Yield only entries that pass *policy*, evaluated at call time."""
    for entry in entries:
        result = policy.apply(entry, now=clock())
        if result is not None:
            yield result


def build_retention_middleware(
    policies: List[RetentionPolicy],
    clock: Callable[[], float] = time.time,
) -> Callable[[dict], Optional[dict]]:
    """Compose multiple policies: an entry is kept only when ALL pass it."""

    def _step(entry: dict) -> Optional[dict]:
        now = clock()
        for pol in policies:
            if pol.apply(entry, now=now) is None:
                return None
        return entry

    return _step

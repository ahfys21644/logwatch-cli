"""Middleware helpers for integrating Watchdog into a processing pipeline."""
from __future__ import annotations

from typing import Callable, Iterable, Iterator, List, Optional

from logwatch.watchdog import Watchdog, WatchdogEvent


def watchdog_step(
    watchdogs: List[Watchdog],
    on_event: Optional[Callable[[WatchdogEvent], None]] = None,
) -> Callable[[dict], dict]:
    """Return a pipeline step that feeds each entry to all watchdogs."""

    def _step(entry: dict) -> dict:
        for wd in watchdogs:
            wd.feed(entry)
        return entry

    return _step


def watchdog_iter(
    entries: Iterable[dict],
    watchdogs: List[Watchdog],
    poll_interval: float = 1.0,
    on_event: Optional[Callable[[WatchdogEvent], None]] = None,
) -> Iterator[dict]:
    """Yield entries while periodically checking watchdogs for silence events."""
    import time

    last_check = time.monotonic()

    for entry in entries:
        for wd in watchdogs:
            wd.feed(entry)
        yield entry

        now = time.monotonic()
        if now - last_check >= poll_interval:
            last_check = now
            for wd in watchdogs:
                event = wd.check()
                if event and on_event:
                    on_event(event)

    # Final flush check
    for wd in watchdogs:
        event = wd.check()
        if event and on_event:
            on_event(event)


def make_default_watchdog(
    silence_window: float = 30.0,
    on_event: Optional[Callable[[WatchdogEvent], None]] = None,
) -> Watchdog:
    from logwatch.watchdog import WatchdogConfig

    cfg = WatchdogConfig(name="default", silence_window=silence_window, on_silence=on_event)
    return Watchdog(cfg)

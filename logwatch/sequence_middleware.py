"""Pipeline middleware that runs SequenceDetectors alongside log entries."""
from __future__ import annotations

from typing import Callable, Dict, Generator, Iterable, List, Optional

from logwatch.sequence_detector import SequenceConfig, SequenceDetector, SequenceEvent


def sequence_step(
    detectors: List[SequenceDetector],
    on_event: Optional[Callable[[SequenceEvent], None]] = None,
) -> Callable[[Dict], Dict]:
    """Return a transformer step that feeds each entry through all detectors."""

    def _step(entry: Dict) -> Dict:
        for detector in detectors:
            event = detector.feed(entry)
            if event is not None and on_event is not None:
                on_event(event)
        return entry

    return _step


def sequence_iter(
    entries: Iterable[Dict],
    detectors: List[SequenceDetector],
    on_event: Optional[Callable[[SequenceEvent], None]] = None,
) -> Generator[Dict, None, None]:
    """Iterate over entries, firing callbacks when a sequence completes."""
    step = sequence_step(detectors, on_event)
    for entry in entries:
        yield step(entry)


def make_login_sequence_detector(
    on_event: Optional[Callable[[SequenceEvent], None]] = None,
) -> SequenceDetector:
    """Convenience factory: detects login → auth → session-start sequence."""
    cfg = SequenceConfig(
        name="login_flow",
        steps=[r"login attempt", r"auth(enticated|orized)", r"session started"],
        window=60.0,
    )
    return SequenceDetector(config=cfg, on_event=on_event or (lambda e: None))

"""Context buffer: capture N lines before/after a matching log entry."""
from collections import deque
from dataclasses import dataclass, field
from typing import Callable, Iterable, Iterator, List


@dataclass
class ContextBuffer:
    """Yields matching entries with surrounding context lines."""

    before: int = 2
    after: int = 2
    _pre: deque = field(init=False, repr=False)
    _pending_after: List = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._pre = deque(maxlen=max(self.before, 0))
        self._pending_after = []

    def feed(
        self,
        entries: Iterable[dict],
        predicate: Callable[[dict], bool],
    ) -> Iterator[dict]:
        """Iterate *entries*, yielding context windows around matching ones.

        Each yielded dict is the original entry annotated with
        ``_context`` key: ``'match'``, ``'before'``, or ``'after'``.
        Duplicate emissions within overlapping windows are deduplicated.
        """
        emitted_ids: set = set()

        def _emit(entry: dict, role: str) -> Iterator[dict]:
            eid = id(entry)
            if eid not in emitted_ids:
                emitted_ids.add(eid)
                yield {**entry, "_context": role}

        after_countdown = 0
        after_queue: deque = deque()

        for entry in entries:
            if after_countdown > 0:
                yield from _emit(entry, "after")
                after_countdown -= 1

            if predicate(entry):
                # flush pre-context
                for pre_entry in self._pre:
                    yield from _emit(pre_entry, "before")
                yield from _emit(entry, "match")
                after_countdown = self.after
            else:
                self._pre.append(entry)

    def reset(self) -> None:
        self._pre.clear()
        self._pending_after.clear()

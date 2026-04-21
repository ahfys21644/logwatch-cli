"""Entry transformer: applies an ordered chain of mutation functions to log entries."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable, List, Optional

Entry = dict
TransformFn = Callable[[Entry], Optional[Entry]]


@dataclass
class Transformer:
    """Applies a sequence of transform functions to each entry.

    A transform function may:
      - return a (possibly mutated) copy of the entry to keep it,
      - return None to drop the entry from the stream.
    """

    steps: List[TransformFn] = field(default_factory=list)

    def add_step(self, fn: TransformFn) -> "Transformer":
        """Append a transform step and return self for chaining."""
        self.steps.append(fn)
        return self

    def apply(self, entry: Entry) -> Optional[Entry]:
        """Run all steps on *entry*; return the final entry or None if dropped."""
        current: Optional[Entry] = entry
        for step in self.steps:
            if current is None:
                return None
            current = step(current)
        return current

    def apply_all(self, entries: Iterable[Entry]) -> Iterable[Entry]:
        """Yield transformed entries, skipping any that are dropped."""
        for entry in entries:
            result = self.apply(entry)
            if result is not None:
                yield result


def build_transformer(steps: List[TransformFn]) -> Transformer:
    """Convenience factory: create a Transformer pre-loaded with *steps*."""
    t = Transformer()
    for step in steps:
        t.add_step(step)
    return t


def drop_field(field_name: str) -> TransformFn:
    """Return a step that removes *field_name* from an entry (if present)."""
    def _step(entry: Entry) -> Entry:
        result = dict(entry)
        result.pop(field_name, None)
        return result
    return _step


def set_field(field_name: str, value: object) -> TransformFn:
    """Return a step that sets *field_name* to a static *value*."""
    def _step(entry: Entry) -> Entry:
        result = dict(entry)
        result[field_name] = value
        return result
    return _step


def drop_if(predicate: Callable[[Entry], bool]) -> TransformFn:
    """Return a step that drops entries matching *predicate*."""
    def _step(entry: Entry) -> Optional[Entry]:
        return None if predicate(entry) else entry
    return _step

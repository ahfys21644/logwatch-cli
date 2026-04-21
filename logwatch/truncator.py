"""Field and message truncation for log entries before display or storage."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

_DEFAULT_MAX_LENGTH = 200
_DEFAULT_FIELD_MAX = 120
_ELLIPSIS = "..."


@dataclass
class Truncator:
    """Truncates long string values in log entries to keep output readable."""

    max_message_length: int = _DEFAULT_MAX_LENGTH
    max_field_length: int = _DEFAULT_FIELD_MAX
    fields_to_skip: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.max_message_length < 1:
            raise ValueError("max_message_length must be >= 1")
        if self.max_field_length < 1:
            raise ValueError("max_field_length must be >= 1")

    def truncate_value(self, value: str, max_length: int) -> str:
        """Return *value* truncated to *max_length*, appending ellipsis if cut."""
        if len(value) <= max_length:
            return value
        cut = max(0, max_length - len(_ELLIPSIS))
        return value[:cut] + _ELLIPSIS

    def truncate_fields(self, entry: dict[str, Any]) -> dict[str, Any]:
        """Return a new entry dict with long string fields truncated."""
        result: dict[str, Any] = {}
        for key, val in entry.items():
            if key in self.fields_to_skip or not isinstance(val, str):
                result[key] = val
            elif key == "message":
                result[key] = self.truncate_value(val, self.max_message_length)
            else:
                result[key] = self.truncate_value(val, self.max_field_length)
        return result

    def truncate_entry(self, entry: dict[str, Any]) -> dict[str, Any]:
        """Return a truncated copy of *entry* without mutating the original."""
        return self.truncate_fields(dict(entry))


def build_truncator(
    max_message: int = _DEFAULT_MAX_LENGTH,
    max_field: int = _DEFAULT_FIELD_MAX,
    skip: list[str] | None = None,
) -> Truncator:
    """Convenience factory for constructing a :class:`Truncator`."""
    return Truncator(
        max_message_length=max_message,
        max_field_length=max_field,
        fields_to_skip=skip or [],
    )

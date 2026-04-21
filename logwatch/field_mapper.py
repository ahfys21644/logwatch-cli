"""Field mapper: rename or drop fields in log entries before output."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class FieldMapper:
    """Rename and/or drop fields on log entry dicts.

    Args:
        rename: mapping of {old_name: new_name}.  Applied before drops.
        drop:   list of field names to remove from the entry.
    """

    rename: Dict[str, str] = field(default_factory=dict)
    drop: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        # Normalise to lower-case keys so matching is case-insensitive
        self.rename = {k.lower(): v for k, v in self.rename.items()}
        self.drop = [d.lower() for d in self.drop]

    def apply(self, entry: dict) -> dict:
        """Return a new entry with renames applied then drops removed."""
        result = {}
        for k, v in entry.items():
            normalised = k.lower()
            if normalised in self.drop:
                continue
            new_key = self.rename.get(normalised, k)
            result[new_key] = v
        return result


def build_field_mapper(
    rename: Optional[Dict[str, str]] = None,
    drop: Optional[List[str]] = None,
) -> FieldMapper:
    """Convenience constructor with optional arguments."""
    return FieldMapper(
        rename=rename or {},
        drop=drop or [],
    )


def map_entry(entry: dict, mapper: FieldMapper) -> dict:
    """Apply *mapper* to *entry* and return the transformed copy."""
    return mapper.apply(entry)

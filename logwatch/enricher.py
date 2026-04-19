"""Entry enrichment: attach derived fields to parsed log entries."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class EnrichRule:
    """A single enrichment rule that adds or transforms a field."""
    target_field: str
    source_field: Optional[str] = None
    pattern: Optional[str] = None
    static_value: Optional[Any] = None
    transform: Optional[Callable[[Any], Any]] = None
    _compiled: Optional[re.Pattern] = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.pattern:
            self._compiled = re.compile(self.pattern)

    def apply(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        entry = dict(entry)
        if self.static_value is not None:
            entry[self.target_field] = self.static_value
            return entry

        source_val = entry.get(self.source_field) if self.source_field else None

        if self._compiled and source_val is not None:
            m = self._compiled.search(str(source_val))
            if m:
                groups = m.groupdict()
                entry[self.target_field] = groups if groups else m.group(0)
            return entry

        if self.transform and source_val is not None:
            entry[self.target_field] = self.transform(source_val)

        return entry


def enrich_entry(
    entry: Dict[str, Any],
    rules: List[EnrichRule],
) -> Dict[str, Any]:
    """Apply a sequence of EnrichRules to a single entry."""
    for rule in rules:
        entry = rule.apply(entry)
    return entry


def build_enricher(
    rules: List[EnrichRule],
) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """Return a callable that enriches an entry with all rules."""
    def _enrich(entry: Dict[str, Any]) -> Dict[str, Any]:
        return enrich_entry(entry, rules)
    return _enrich

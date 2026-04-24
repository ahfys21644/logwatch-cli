"""Field-value filter: include or exclude log entries based on field presence and value."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Optional

from logwatch.parser import parse_line


@dataclass
class FieldFilterRule:
    """A single include/exclude rule for a named field."""

    field: str
    values: List[str]  # empty list means "field must be present (any value)"
    exclude: bool = False  # True => block matching entries
    case_sensitive: bool = False

    def __post_init__(self) -> None:
        if not self.field:
            raise ValueError("field name must not be empty")
        if not self.case_sensitive:
            self.values = [v.lower() for v in self.values]

    def matches(self, entry: Dict[str, Any]) -> bool:
        """Return True when the entry satisfies this rule's field condition."""
        if self.field not in entry:
            return False
        if not self.values:
            return True  # only checking presence
        raw = str(entry[self.field])
        cmp = raw if self.case_sensitive else raw.lower()
        return cmp in self.values


@dataclass
class FieldFilter:
    """Applies an ordered list of FieldFilterRules to log entries."""

    rules: List[FieldFilterRule] = field(default_factory=list)

    def add_rule(self, rule: FieldFilterRule) -> None:
        self.rules.append(rule)

    def allows(self, entry: Dict[str, Any]) -> bool:
        """Return False if any exclude rule matches or any include rule fails to match."""
        for rule in self.rules:
            matched = rule.matches(entry)
            if rule.exclude and matched:
                return False
            if not rule.exclude and not matched:
                return False
        return True

    def filter(self, entries: Iterable[Dict[str, Any]]) -> Iterable[Dict[str, Any]]:
        return (e for e in entries if self.allows(e))


def build_field_filter(rules_cfg: List[Dict[str, Any]]) -> FieldFilter:
    """Build a FieldFilter from a list of rule dicts.

    Each dict may contain:
      field (str), values (list[str]), exclude (bool), case_sensitive (bool)
    """
    ff = FieldFilter()
    for cfg in rules_cfg:
        rule = FieldFilterRule(
            field=cfg["field"],
            values=list(cfg.get("values") or []),
            exclude=bool(cfg.get("exclude", False)),
            case_sensitive=bool(cfg.get("case_sensitive", False)),
        )
        ff.add_rule(rule)
    return ff


def field_filter_step(ff: FieldFilter) -> Callable[[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """Return a transformer-compatible step function."""
    def _step(entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return entry if ff.allows(entry) else None
    return _step

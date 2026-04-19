"""Redact sensitive fields from log entries before output."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, Any, List

DEFAULT_PATTERNS: List[str] = [
    r'(?i)password=[^\s&]+',
    r'(?i)token=[^\s&]+',
    r'(?i)secret=[^\s&]+',
    r'\b\d{4}-\d{4}-\d{4}-\d{4}\b',  # credit card-like
]

REDACT_PLACEHOLDER = "***"


@dataclass
class Redactor:
    """Redact sensitive values from log entry fields and messages."""

    sensitive_keys: List[str] = field(default_factory=lambda: ["password", "token", "secret", "api_key", "auth"])
    patterns: List[str] = field(default_factory=lambda: list(DEFAULT_PATTERNS))
    _compiled: List[re.Pattern] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._compiled = [re.compile(p) for p in self.patterns]

    def redact_value(self, value: str) -> str:
        result = value
        for pat in self._compiled:
            result = pat.sub(lambda m: m.group(0).split('=')[0] + '=' + REDACT_PLACEHOLDER
                             if '=' in m.group(0) else REDACT_PLACEHOLDER, result)
        return result

    def redact_fields(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        for k, v in fields.items():
            if k.lower() in self.sensitive_keys:
                out[k] = REDACT_PLACEHOLDER
            elif isinstance(v, str):
                out[k] = self.redact_value(v)
            else:
                out[k] = v
        return out

    def redact_entry(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        result = dict(entry)
        if "message" in result and isinstance(result["message"], str):
            result["message"] = self.redact_value(result["message"])
        if "fields" in result and isinstance(result["fields"], dict):
            result["fields"] = self.redact_fields(result["fields"])
        return result


def default_redactor() -> Redactor:
    return Redactor()

"""Schema validation for parsed log entries.

Allows asserting that required fields are present and that field values
match expected types or regex patterns before entries enter the pipeline.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class FieldSchema:
    """Validation rule for a single field."""

    name: str
    required: bool = False
    expected_type: Optional[type] = None
    pattern: Optional[str] = None
    _compiled: Optional[re.Pattern] = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.pattern:
            self._compiled = re.compile(self.pattern)

    def validate(self, entry: Dict[str, Any]) -> List[str]:
        """Return a list of validation error messages (empty means valid)."""
        errors: List[str] = []
        if self.name not in entry:
            if self.required:
                errors.append(f"missing required field '{self.name}'")
            return errors

        value = entry[self.name]

        if self.expected_type is not None and not isinstance(value, self.expected_type):
            errors.append(
                f"field '{self.name}' expected {self.expected_type.__name__}, "
                f"got {type(value).__name__}"
            )

        if self._compiled is not None:
            str_value = str(value)
            if not self._compiled.search(str_value):
                errors.append(
                    f"field '{self.name}' value {str_value!r} does not match "
                    f"pattern {self.pattern!r}"
                )

        return errors


@dataclass
class SchemaValidator:
    """Validates log entries against a collection of FieldSchema rules."""

    schemas: List[FieldSchema] = field(default_factory=list)
    on_invalid: str = "drop"  # "drop" | "tag" | "pass"
    tag_field: str = "_invalid"

    def validate(self, entry: Dict[str, Any]) -> List[str]:
        """Return all validation errors for *entry*."""
        errors: List[str] = []
        for schema in self.schemas:
            errors.extend(schema.validate(entry))
        return errors

    def apply(self, entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Apply validation policy. Returns entry (possibly modified) or None."""
        errors = self.validate(entry)
        if not errors:
            return entry
        if self.on_invalid == "drop":
            return None
        if self.on_invalid == "tag":
            result = dict(entry)
            result[self.tag_field] = errors
            return result
        # "pass" — return as-is
        return entry


def build_schema_validator(
    rules: List[Dict[str, Any]], on_invalid: str = "drop"
) -> SchemaValidator:
    """Build a SchemaValidator from a list of rule dicts."""
    schemas = [
        FieldSchema(
            name=r["name"],
            required=r.get("required", False),
            expected_type=__builtins__[r["type"]] if "type" in r else None,  # type: ignore[index]
            pattern=r.get("pattern"),
        )
        for r in rules
    ]
    return SchemaValidator(schemas=schemas, on_invalid=on_invalid)


def validation_step(
    validator: SchemaValidator,
) -> Callable[[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """Return a transformer-compatible step function."""
    return validator.apply

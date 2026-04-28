"""Load TagRouter configuration from dicts / YAML."""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore

from logwatch.tag_router import TagRule, TagRouter


def _predicate_from_dict(spec: Dict[str, Any]):
    """Build a predicate callable from a rule spec dict."""
    level = spec.get("level")
    pattern = spec.get("pattern")
    field_key = spec.get("field")
    field_value = spec.get("value")

    def predicate(entry):
        if level and str(entry.get("level", "")).upper() != level.upper():
            return False
        if pattern:
            msg = str(entry.get("message", ""))
            if not re.search(pattern, msg, re.IGNORECASE):
                return False
        if field_key and field_value is not None:
            if str(entry.get(field_key, "")).lower() != str(field_value).lower():
                return False
        return True

    return predicate


def load_tag_rules_from_list(items: List[Dict[str, Any]]) -> List[TagRule]:
    rules = []
    for item in items:
        tag = item.get("tag")
        if not tag:
            raise ValueError("Each tag rule must have a 'tag' key.")
        rules.append(TagRule(tag=tag, predicate=_predicate_from_dict(item)))
    return rules


def load_tag_rules_from_yaml(path: str) -> List[TagRule]:
    if yaml is None:  # pragma: no cover
        raise RuntimeError("PyYAML is required to load tag rules from YAML.")
    with open(path) as fh:
        data = yaml.safe_load(fh) or {}
    return load_tag_rules_from_list(data.get("tag_rules", []))


def default_tag_router() -> TagRouter:
    router = TagRouter()
    router.add_rule(TagRule("error", lambda e: str(e.get("level", "")).upper() == "ERROR"))
    router.add_rule(TagRule("warn", lambda e: str(e.get("level", "")).upper() in ("WARN", "WARNING")))
    router.add_rule(TagRule("info", lambda e: str(e.get("level", "")).upper() == "INFO"))
    return router

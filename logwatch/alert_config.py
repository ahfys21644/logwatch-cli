"""Load alert rules from a YAML or dict configuration."""

from typing import Any, Dict, List
from logwatch.alerts import AlertRule


DEFAULT_RULES: List[Dict[str, Any]] = [
    {"name": "high-severity", "level_threshold": "error"},
    {"name": "oom-detector", "pattern": "out of memory"},
]


def load_rules_from_list(raw: List[Dict[str, Any]]) -> List[AlertRule]:
    """Parse a list of rule dicts into AlertRule objects."""
    rules = []
    for item in raw:
        name = item.get("name")
        if not name:
            raise ValueError(f"Alert rule missing 'name': {item}")
        rules.append(
            AlertRule(
                name=name,
                pattern=item.get("pattern"),
                level_threshold=item.get("level_threshold"),
                field_match=item.get("field_match"),
            )
        )
    return rules


def load_rules_from_yaml(path: str) -> List[AlertRule]:
    """Load alert rules from a YAML file."""
    try:
        import yaml
    except ImportError:
        raise ImportError("PyYAML is required to load rules from YAML files.")

    with open(path, "r") as fh:
        data = yaml.safe_load(fh)

    if not isinstance(data, dict) or "alerts" not in data:
        raise ValueError("YAML file must contain a top-level 'alerts' key.")

    return load_rules_from_list(data["alerts"])


def default_rules() -> List[AlertRule]:
    """Return the built-in default alert rules."""
    return load_rules_from_list(DEFAULT_RULES)

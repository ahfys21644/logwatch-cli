"""Load router configuration from dicts or YAML."""
from __future__ import annotations

from typing import List


DEFAULT_ROUTER_CONFIG: List[dict] = [
    {
        "name": "errors_to_stderr",
        "level": "error",
        "sink": "stderr",
        "stop": False,
    },
    {
        "name": "default_stdout",
        "sink": "stdout",
        "stop": True,
    },
]


def load_router_config_from_list(raw: List[dict]) -> List[dict]:
    """Validate and return a list of route rule configs."""
    validated = []
    for item in raw:
        if "sink" not in item:
            raise ValueError(f"Route rule missing 'sink' key: {item}")
        validated.append({
            "name": item.get("name", "unnamed"),
            "sink": item["sink"],
            "stop": bool(item.get("stop", True)),
            **{k: item[k] for k in ("level", "pattern", "field", "value") if k in item},
        })
    return validated


def load_router_config_from_yaml(path: str) -> List[dict]:
    """Load router rule configs from a YAML file."""
    import yaml
    with open(path, "r") as fh:
        data = yaml.safe_load(fh) or {}
    raw = data.get("routes", [])
    return load_router_config_from_list(raw)


def default_router_config() -> List[dict]:
    return load_router_config_from_list(DEFAULT_ROUTER_CONFIG)

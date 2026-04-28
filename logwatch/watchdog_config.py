"""Load WatchdogConfig instances from dicts or YAML."""
from __future__ import annotations

from typing import Any, Dict, List

from logwatch.watchdog import WatchdogConfig


def load_watchdog_config_from_dict(data: Dict[str, Any]) -> WatchdogConfig:
    name = data.get("name", "unnamed")
    raw_window = data.get("silence_window")
    if raw_window is None:
        raise ValueError("watchdog config requires 'silence_window'")
    return WatchdogConfig(
        name=name,
        silence_window=float(raw_window),
        level_filter=data.get("level_filter"),
    )


def load_watchdog_configs_from_yaml(path: str) -> List[WatchdogConfig]:
    import yaml  # type: ignore

    with open(path, "r") as fh:
        raw = yaml.safe_load(fh)
    items = raw.get("watchdogs", []) if isinstance(raw, dict) else raw or []
    return [load_watchdog_config_from_dict(item) for item in items]


def default_watchdog_config() -> WatchdogConfig:
    return WatchdogConfig(name="default", silence_window=60.0)


def build_watchdogs(configs: List[Dict[str, Any]]) -> List["Watchdog"]:  # noqa: F821
    from logwatch.watchdog import Watchdog

    return [Watchdog(load_watchdog_config_from_dict(c)) for c in configs]

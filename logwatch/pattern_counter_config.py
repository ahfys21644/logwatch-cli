"""pattern_counter_config.py — load PatternCounterConfig from dicts or YAML."""
from __future__ import annotations

from typing import Any, Dict, List

from logwatch.pattern_counter import PatternCounter, PatternCounterConfig

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore


def load_pattern_counter_from_dict(data: Dict[str, Any]) -> PatternCounterConfig:
    """Build a PatternCounterConfig from a plain dictionary."""
    name = data.get("name", "unnamed")
    pattern = data["pattern"]
    window = float(data["window"])
    threshold = int(data["threshold"])
    level_filter = data.get("level_filter", None)
    return PatternCounterConfig(
        name=name,
        pattern=pattern,
        window=window,
        threshold=threshold,
        level_filter=level_filter,
    )


def load_pattern_counters_from_yaml(path: str) -> List[PatternCounterConfig]:
    """Load a list of PatternCounterConfig objects from a YAML file."""
    if yaml is None:  # pragma: no cover
        raise RuntimeError("PyYAML is required to load YAML config")
    with open(path) as fh:
        raw = yaml.safe_load(fh)
    items = raw if isinstance(raw, list) else raw.get("pattern_counters", [])
    return [load_pattern_counter_from_dict(item) for item in items]


def default_pattern_counter_config() -> PatternCounterConfig:
    """Return a sensible default config for demonstration purposes."""
    return PatternCounterConfig(
        name="error-burst",
        pattern=r"error|exception|fail",
        window=60.0,
        threshold=10,
        level_filter="warn",
    )


def build_counters(configs: List[PatternCounterConfig]) -> List[PatternCounter]:
    """Instantiate PatternCounter objects from a list of configs."""
    return [PatternCounter(config=cfg) for cfg in configs]

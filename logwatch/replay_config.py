"""Configuration helpers for the replay feature."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ReplayConfig:
    """Holds all settings needed to drive a replay session."""

    source: str
    """Path to a log file / JSONL file, or the name of a snapshot."""

    kind: str = "file"
    """One of ``'file'``, ``'jsonl'``, or ``'snapshot'``."""

    limit: Optional[int] = None
    """Maximum number of entries to replay.  ``None`` means unlimited."""

    min_level: str = "DEBUG"
    """Minimum log level to pass through the pipeline."""

    patterns: list[str] = field(default_factory=list)
    """Optional list of regex patterns to filter by message content."""

    def __post_init__(self) -> None:
        valid_kinds = {"file", "jsonl", "snapshot"}
        if self.kind not in valid_kinds:
            raise ValueError(f"kind must be one of {valid_kinds}, got {self.kind!r}")
        if self.limit is not None and self.limit < 1:
            raise ValueError(f"limit must be a positive integer, got {self.limit}")


def config_from_dict(data: dict) -> ReplayConfig:
    """Build a :class:`ReplayConfig` from a plain dictionary (e.g. parsed YAML)."""
    return ReplayConfig(
        source=data["source"],
        kind=data.get("kind", "file"),
        limit=data.get("limit"),
        min_level=data.get("min_level", "DEBUG"),
        patterns=data.get("patterns", []),
    )


def default_replay_config(source: str) -> ReplayConfig:
    """Return a sensible default :class:`ReplayConfig` for *source*."""
    return ReplayConfig(source=source)

"""Snapshot: persist and restore session stats to/from JSON."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from logwatch.stats import SessionStats

_DEFAULT_PATH = os.path.join(os.path.expanduser("~"), ".logwatch", "snapshot.json")


def save_snapshot(stats: "SessionStats", path: str = _DEFAULT_PATH) -> None:
    """Serialise *stats* to a JSON file at *path*."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    payload = {
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "total": stats.total,
        "by_level": dict(stats.by_level),
        "alerts_fired": stats.alerts_fired,
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)


def load_snapshot(path: str = _DEFAULT_PATH) -> dict:
    """Return the raw snapshot dict, or an empty dict if the file is absent."""
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def merge_snapshot(stats: "SessionStats", path: str = _DEFAULT_PATH) -> None:
    """Add counts from a previously saved snapshot into *stats*."""
    data = load_snapshot(path)
    if not data:
        return
    stats.total += data.get("total", 0)
    for level, count in data.get("by_level", {}).items():
        stats.by_level[level] = stats.by_level.get(level, 0) + count
    stats.alerts_fired += data.get("alerts_fired", 0)


def delete_snapshot(path: str = _DEFAULT_PATH) -> bool:
    """Remove the snapshot file. Returns True if a file was deleted."""
    if os.path.exists(path):
        os.remove(path)
        return True
    return False

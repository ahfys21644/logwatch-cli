"""Checkpoint module — persist and restore file read positions for resumable tailing."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, Optional

_DEFAULT_DIR = Path.home() / ".logwatch" / "checkpoints"


def _checkpoint_path(log_path: str, checkpoint_dir: Path) -> Path:
    safe_name = log_path.replace("/", "_").replace("\\", "_").lstrip("_")
    return checkpoint_dir / f"{safe_name}.json"


def save_checkpoint(log_path: str, offset: int, checkpoint_dir: Optional[Path] = None) -> Path:
    """Persist the byte offset for *log_path* to disk."""
    directory = Path(checkpoint_dir) if checkpoint_dir else _DEFAULT_DIR
    directory.mkdir(parents=True, exist_ok=True)
    dest = _checkpoint_path(log_path, directory)
    dest.write_text(json.dumps({"path": log_path, "offset": offset}), encoding="utf-8")
    return dest


def load_checkpoint(log_path: str, checkpoint_dir: Optional[Path] = None) -> int:
    """Return the saved byte offset for *log_path*, or 0 if none exists."""
    directory = Path(checkpoint_dir) if checkpoint_dir else _DEFAULT_DIR
    dest = _checkpoint_path(log_path, directory)
    if not dest.exists():
        return 0
    try:
        data = json.loads(dest.read_text(encoding="utf-8"))
        return int(data.get("offset", 0))
    except (json.JSONDecodeError, ValueError):
        return 0


def delete_checkpoint(log_path: str, checkpoint_dir: Optional[Path] = None) -> bool:
    """Remove the checkpoint file for *log_path*. Returns True if deleted."""
    directory = Path(checkpoint_dir) if checkpoint_dir else _DEFAULT_DIR
    dest = _checkpoint_path(log_path, directory)
    if dest.exists():
        dest.unlink()
        return True
    return False


def list_checkpoints(checkpoint_dir: Optional[Path] = None) -> Dict[str, int]:
    """Return a mapping of {log_path: offset} for all saved checkpoints."""
    directory = Path(checkpoint_dir) if checkpoint_dir else _DEFAULT_DIR
    if not directory.exists():
        return {}
    result: Dict[str, int] = {}
    for fp in directory.glob("*.json"):
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
            result[data["path"]] = int(data.get("offset", 0))
        except (json.JSONDecodeError, KeyError, ValueError):
            continue
    return result

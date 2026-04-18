"""Structured log parser supporting JSON and key=value formats."""

import json
import re
from typing import Optional


LOG_LEVELS = {"debug", "info", "warning", "warn", "error", "critical", "fatal"}

KV_PATTERN = re.compile(r'(\w+)=("[^"]*"|\S+)')


def parse_line(line: str) -> dict:
    """Parse a single log line into a structured dict.

    Supports:
    - JSON log lines
    - key=value formatted lines
    - Plain text (stored under 'message' key)
    """
    line = line.strip()
    if not line:
        return {}

    # Attempt JSON parse
    if line.startswith("{"):
        try:
            data = json.loads(line)
            _normalize(data)
            return data
        except json.JSONDecodeError:
            pass

    # Attempt key=value parse
    matches = KV_PATTERN.findall(line)
    if matches:
        data = {k: v.strip('"') for k, v in matches}
        _normalize(data)
        return data

    # Fallback: plain text
    return {"message": line, "level": "unknown"}


def parse_lines(lines) -> list[dict]:
    """Parse multiple log lines, skipping empty results.

    Args:
        lines: An iterable of log line strings.

    Returns:
        A list of non-empty parsed log entry dicts.
    """
    return [parsed for line in lines if (parsed := parse_line(line))]


def _normalize(data: dict) -> None:
    """Normalize common field aliases in-place."""
    # Normalize level field
    for key in ("level", "severity", "lvl"):
        if key in data:
            raw = str(data[key]).lower()
            data["level"] = "warning" if raw == "warn" else ("critical" if raw == "fatal" else raw)
            if key != "level":
                del data[key]
            break
    else:
        data.setdefault("level", "unknown")

    # Normalize message field
    for key in ("msg", "message", "text"):
        if key in data:
            data["message"] = data.pop(key) if key != "message" else data[key]
            break
    else:
        data.setdefault("message", "")


def extract_level(parsed: dict) -> Optional[str]:
    """Return the log level from a parsed log entry, or None."""
    level = parsed.get("level", "").lower()
    return level if level in LOG_LEVELS else None

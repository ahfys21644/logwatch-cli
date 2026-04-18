"""Terminal output formatting for parsed log entries."""

from typing import Dict, Any, Optional

LEVEL_COLORS = {
    "debug": "\033[36m",    # cyan
    "info": "\033[32m",     # green
    "warn": "\033[33m",     # yellow
    "warning": "\033[33m",  # yellow
    "error": "\033[31m",    # red
    "critical": "\033[35m", # magenta
    "fatal": "\033[35m",    # magenta
}

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"


def colorize_level(level: str) -> str:
    color = LEVEL_COLORS.get(level.lower(), "")
    return f"{color}{BOLD}{level.upper():<8}{RESET}"


def format_entry(entry: Dict[str, Any], color: bool = True, show_fields: bool = True) -> str:
    """Format a parsed log entry for terminal display."""
    parts = []

    timestamp = entry.get("timestamp") or entry.get("ts") or entry.get("time", "")
    if timestamp:
        ts_str = f"{DIM}{timestamp}{RESET}" if color else str(timestamp)
        parts.append(ts_str)

    level = entry.get("level", "info")
    if color:
        parts.append(colorize_level(level))
    else:
        parts.append(f"{level.upper():<8}")

    message = entry.get("message") or entry.get("msg", "")
    if message:
        parts.append(str(message))

    if show_fields:
        skip = {"timestamp", "ts", "time", "level", "severity", "message", "msg"}
        extras = {k: v for k, v in entry.items() if k not in skip}
        if extras:
            field_str = "  ".join(f"{k}={v}" for k, v in extras.items())
            if color:
                field_str = f"{DIM}{field_str}{RESET}"
            parts.append(field_str)

    return "  ".join(parts)


def format_alert(rule_name: str, entry: Dict[str, Any], color: bool = True) -> str:
    """Format an alert notification line."""
    label = f"[ALERT:{rule_name}]"
    if color:
        label = f"\033[41m{BOLD}{label}{RESET}"
    return f"{label}  {format_entry(entry, color=color, show_fields=False)}"

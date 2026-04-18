"""Collect and summarize log entry statistics during a session."""
from dataclasses import dataclass, field
from collections import Counter
from typing import Dict, List

LEVEL_ORDER = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


@dataclass
class SessionStats:
    total: int = 0
    by_level: Counter = field(default_factory=Counter)
    alerts_fired: int = 0
    alert_names: Counter = field(default_factory=Counter)

    def record_entry(self, entry: dict) -> None:
        self.total += 1
        level = entry.get("level", "UNKNOWN").upper()
        self.by_level[level] += 1

    def record_alert(self, rule_name: str) -> None:
        self.alerts_fired += 1
        self.alert_names[rule_name] += 1

    def summary(self) -> Dict:
        ordered = {lvl: self.by_level.get(lvl, 0) for lvl in LEVEL_ORDER}
        extra = {k: v for k, v in self.by_level.items() if k not in ordered}
        return {
            "total": self.total,
            "by_level": {**ordered, **extra},
            "alerts_fired": self.alerts_fired,
            "top_alerts": self.alert_names.most_common(5),
        }

    def format_summary(self) -> str:
        s = self.summary()
        lines = [
            "=== Session Summary ===",
            f"  Total entries : {s['total']}",
            "  By level:",
        ]
        for lvl, count in s["by_level"].items():
            if count:
                lines.append(f"    {lvl:<10} {count}")
        lines.append(f"  Alerts fired  : {s['alerts_fired']}")
        if s["top_alerts"]:
            lines.append("  Top alerts:")
            for name, count in s["top_alerts"]:
                lines.append(f"    {name:<20} {count}")
        return "\n".join(lines)

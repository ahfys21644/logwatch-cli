"""Term highlighter – marks pattern matches inside formatted log lines."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

ANSI_RESET = "\033[0m"
ANSI_BOLD_YELLOW = "\033[1;33m"
ANSI_BOLD_RED = "\033[1;31m"
ANSI_BOLD_CYAN = "\033[1;36m"

COLOR_CYCLE = [ANSI_BOLD_YELLOW, ANSI_BOLD_CYAN, ANSI_BOLD_RED]


@dataclass
class Highlighter:
    patterns: List[str] = field(default_factory=list)
    case_sensitive: bool = False
    _compiled: List[re.Pattern] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        flags = 0 if self.case_sensitive else re.IGNORECASE
        self._compiled = [re.compile(p, flags) for p in self.patterns]

    def highlight(self, text: str) -> str:
        """Return *text* with each pattern match wrapped in ANSI colour codes."""
        if not self._compiled:
            return text
        for idx, regex in enumerate(self._compiled):
            color = COLOR_CYCLE[idx % len(COLOR_CYCLE)]
            text = regex.sub(lambda m, c=color: f"{c}{m.group(0)}{ANSI_RESET}", text)
        return text

    def highlight_field(self, value: object) -> str:
        """Convenience wrapper that stringifies *value* before highlighting."""
        return self.highlight(str(value))

    def any_match(self, text: str) -> bool:
        """Return True if *any* pattern matches *text*."""
        return any(rx.search(text) for rx in self._compiled)


def build_highlighter(
    patterns: Optional[List[str]] = None,
    case_sensitive: bool = False,
) -> Highlighter:
    """Factory used by the CLI to construct a Highlighter from raw strings."""
    return Highlighter(patterns=patterns or [], case_sensitive=case_sensitive)

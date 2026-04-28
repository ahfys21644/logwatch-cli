"""Tag-based routing: attach tags to log entries and route by tag set."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Optional, Set

LogEntry = Dict[str, object]
Sink = Callable[[LogEntry], None]


@dataclass
class TagRule:
    """Associate a tag with a predicate; entries that match get the tag."""
    tag: str
    predicate: Callable[[LogEntry], bool]


@dataclass
class TagRouter:
    """Attach tags to entries and dispatch to per-tag sinks."""
    rules: List[TagRule] = field(default_factory=list)
    sinks: Dict[str, Sink] = field(default_factory=dict)
    default_sink: Optional[Sink] = None

    def add_rule(self, rule: TagRule) -> None:
        self.rules.append(rule)

    def register_sink(self, tag: str, sink: Sink) -> None:
        self.sinks[tag] = sink

    def tag_entry(self, entry: LogEntry) -> Set[str]:
        """Return the set of tags that apply to *entry*."""
        return {r.tag for r in self.rules if r.predicate(entry)}

    def route(self, entry: LogEntry) -> None:
        """Tag *entry* and dispatch to every matching sink."""
        tags = self.tag_entry(entry)
        enriched = {**entry, "tags": sorted(tags)}
        dispatched = False
        for tag in tags:
            sink = self.sinks.get(tag)
            if sink is not None:
                sink(enriched)
                dispatched = True
        if not dispatched and self.default_sink is not None:
            self.default_sink(enriched)

    def route_all(self, entries: Iterable[LogEntry]) -> None:
        for entry in entries:
            self.route(entry)


def make_level_tag_router(
    error_sink: Sink,
    warn_sink: Sink,
    default_sink: Optional[Sink] = None,
) -> TagRouter:
    """Convenience factory: routes ERROR entries and WARN entries."""
    router = TagRouter(default_sink=default_sink)
    router.add_rule(TagRule("error", lambda e: str(e.get("level", "")).upper() == "ERROR"))
    router.add_rule(TagRule("warn", lambda e: str(e.get("level", "")).upper() in ("WARN", "WARNING")))
    router.register_sink("error", error_sink)
    router.register_sink("warn", warn_sink)
    return router

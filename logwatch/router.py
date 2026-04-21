"""Route log entries to different output sinks based on rules."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional

from logwatch.output import OutputSink


@dataclass
class RouteRule:
    """A single routing rule: if predicate matches, send entry to sink."""
    name: str
    predicate: Callable[[dict], bool]
    sink: OutputSink
    stop: bool = True  # if True, do not evaluate further rules


@dataclass
class Router:
    """Evaluate a list of RouteRules and dispatch entries accordingly."""
    rules: List[RouteRule] = field(default_factory=list)
    default_sink: Optional[OutputSink] = None

    def add_rule(self, rule: RouteRule) -> None:
        self.rules.append(rule)

    def route(self, entry: dict) -> Optional[str]:
        """Send entry to matching sink(s). Returns name of first matched rule or None."""
        matched: Optional[str] = None
        for rule in self.rules:
            if rule.predicate(entry):
                rule.sink.write_entry(entry)
                matched = rule.name
                if rule.stop:
                    return matched
        if matched is None and self.default_sink is not None:
            self.default_sink.write_entry(entry)
        return matched

    def route_all(self, entries) -> None:
        for entry in entries:
            self.route(entry)


def build_router(rules_cfg: List[dict], sinks: dict[str, OutputSink],
                 default_sink: Optional[OutputSink] = None) -> Router:
    """Build a Router from a list of config dicts and a named sink map."""
    from logwatch.filter import filter_by_level, filter_by_pattern, filter_by_field

    router = Router(default_sink=default_sink)
    for cfg in rules_cfg:
        name = cfg.get("name", "unnamed")
        sink_name = cfg["sink"]
        sink = sinks[sink_name]
        stop = cfg.get("stop", True)

        predicates: List[Callable[[dict], bool]] = []
        if "level" in cfg:
            predicates.append(filter_by_level(cfg["level"]))
        if "pattern" in cfg:
            predicates.append(filter_by_pattern(cfg["pattern"]))
        if "field" in cfg:
            predicates.append(filter_by_field(cfg["field"], cfg["value"]))

        def make_predicate(preds):
            def predicate(entry):
                return all(p(entry) for p in preds)
            return predicate

        router.add_rule(RouteRule(
            name=name,
            predicate=make_predicate(predicates),
            sink=sink,
            stop=stop,
        ))
    return router

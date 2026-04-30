"""topology_builder.py — Fluent builder for constructing Topology pipelines from config.

Provides a high-level API for wiring together parsers, filters, transformers,
routers, sinks, and middleware into a Topology instance without manually
managing node references.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from logwatch.topology import Topology, TopologyNode
from logwatch.filter import build_filter, combined
from logwatch.transformer import build_transformer
from logwatch.output import OutputSink
from logwatch.alerts import AlertRule, check_alerts
from logwatch.alert_config import load_rules_from_list
from logwatch.enricher import build_enricher
from logwatch.redactor import Redactor
from logwatch.truncator import Truncator
from logwatch.dedup import DedupFilter
from logwatch.sampler import Sampler
from logwatch.label_filter import build_label_filter


class TopologyBuilder:
    """Fluent builder that assembles a :class:`~logwatch.topology.Topology`.

    Example usage::

        topology = (
            TopologyBuilder()
            .with_level_filter("warning")
            .with_dedup(ttl=60)
            .with_enricher([{"field": "env", "value": "prod"}])
            .with_stdout_sink()
            .build()
        )
    """

    def __init__(self) -> None:
        self._topology: Topology = Topology()
        self._steps: List[Callable[[Dict[str, Any]], Optional[Dict[str, Any]]]] = []
        self._sinks: List[OutputSink] = []
        self._alert_rules: List[AlertRule] = []
        self._on_alert: Optional[Callable] = None

    # ------------------------------------------------------------------
    # Filtering
    # ------------------------------------------------------------------

    def with_level_filter(self, min_level: str) -> "TopologyBuilder":
        """Drop entries below *min_level* (e.g. ``'warning'``)."""
        f = build_filter(min_level=min_level)
        self._steps.append(lambda entry: entry if f(entry) else None)
        self._topology.add_step(f"level_filter:{min_level}")
        return self

    def with_pattern_filter(self, pattern: str) -> "TopologyBuilder":
        """Keep only entries whose message matches *pattern* (regex)."""
        from logwatch.filter import filter_by_pattern
        f = filter_by_pattern(pattern)
        self._steps.append(lambda entry: entry if f(entry) else None)
        self._topology.add_step(f"pattern_filter:{pattern}")
        return self

    def with_label_filter(
        self,
        include: Optional[Dict[str, List[str]]] = None,
        exclude: Optional[Dict[str, List[str]]] = None,
    ) -> "TopologyBuilder":
        """Filter entries by field label inclusion/exclusion rules."""
        lf = build_label_filter(include=include or {}, exclude=exclude or {})
        self._steps.append(lambda entry: entry if lf.allows(entry) else None)
        self._topology.add_step("label_filter")
        return self

    # ------------------------------------------------------------------
    # Transformation
    # ------------------------------------------------------------------

    def with_enricher(self, rules: List[Dict[str, Any]]) -> "TopologyBuilder":
        """Enrich each entry with static values or regex-extracted fields."""
        enricher = build_enricher(rules)
        self._steps.append(enricher)
        self._topology.add_step("enricher")
        return self

    def with_redactor(self, patterns: Optional[List[str]] = None) -> "TopologyBuilder":
        """Redact sensitive values matching *patterns* from every entry."""
        redactor = Redactor(patterns=patterns or [])
        self._steps.append(redactor.redact_entry)
        self._topology.add_step("redactor")
        return self

    def with_truncator(self, max_length: int = 200) -> "TopologyBuilder":
        """Truncate long field values to *max_length* characters."""
        truncator = Truncator(max_length=max_length)
        self._steps.append(truncator.truncate_entry)
        self._topology.add_step(f"truncator:{max_length}")
        return self

    def with_dedup(self, ttl: float = 30.0) -> "TopologyBuilder":
        """Suppress duplicate entries seen within the last *ttl* seconds."""
        dedup = DedupFilter(ttl=ttl)
        self._steps.append(lambda entry: None if dedup.is_duplicate(entry) else entry)
        self._topology.add_step(f"dedup:ttl={ttl}")
        return self

    def with_sampler(self, rate: int = 1) -> "TopologyBuilder":
        """Keep only every *rate*-th entry (1 = keep all)."""
        sampler = Sampler(rate=rate)
        self._steps.append(lambda entry: entry if sampler.should_keep(entry) else None)
        self._topology.add_step(f"sampler:rate={rate}")
        return self

    # ------------------------------------------------------------------
    # Alerting
    # ------------------------------------------------------------------

    def with_alerts(
        self,
        rules: List[Dict[str, Any]],
        on_alert: Optional[Callable] = None,
    ) -> "TopologyBuilder":
        """Register alert rules loaded from a list of dicts.

        *on_alert* is called with each fired :class:`~logwatch.alerts.AlertRule`
        and the triggering entry.  Defaults to printing to stdout.
        """
        self._alert_rules = load_rules_from_list(rules)
        self._on_alert = on_alert
        self._topology.add_step("alerts")
        return self

    # ------------------------------------------------------------------
    # Sinks
    # ------------------------------------------------------------------

    def with_stdout_sink(self, color: bool = True) -> "TopologyBuilder":
        """Add a sink that writes formatted entries to *stdout*."""
        sink = OutputSink(color=color)
        self._sinks.append(sink)
        self._topology.add_sink("stdout")
        return self

    def with_file_sink(self, path: str, color: bool = False) -> "TopologyBuilder":
        """Add a sink that writes formatted entries to *path*."""
        sink = OutputSink(path=path, color=color)
        self._sinks.append(sink)
        self._topology.add_sink(f"file:{path}")
        return self

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def build(self) -> Topology:
        """Finalise and return the assembled :class:`~logwatch.topology.Topology`."""
        return self._topology

    def build_processor(
        self,
    ) -> Callable[[Dict[str, Any]], None]:
        """Return a callable that runs an entry through all configured steps and sinks.

        The returned function applies each transformation step in order,
        fires any matching alert rules, then forwards the (possibly modified)
        entry to every registered sink.
        """
        steps = list(self._steps)
        rules = list(self._alert_rules)
        on_alert = self._on_alert
        sinks = list(self._sinks)

        def _default_on_alert(rule: AlertRule, entry: Dict[str, Any]) -> None:
            print(f"[ALERT] {rule.name}: {entry.get('message', '')}")

        _fire = on_alert or _default_on_alert

        def process(entry: Dict[str, Any]) -> None:
            current: Optional[Dict[str, Any]] = entry
            for step in steps:
                if current is None:
                    return
                current = step(current)
            if current is None:
                return
            # Alert checking
            for fired_rule in check_alerts(rules, current):
                _fire(fired_rule, current)
            # Fan-out to sinks
            for sink in sinks:
                sink.write_entry(current)

        return process

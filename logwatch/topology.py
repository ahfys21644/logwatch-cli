"""Pipeline topology builder for logwatch-cli.

Provides a high-level API for wiring together sources, transformers,
routers, sinks, and side-effect components (alerts, aggregators, etc.)
into a named, inspectable processing graph.
"""

from __future__ import annotations

import dataclasses
from typing import Any, Callable, Dict, Iterable, List, Optional

# A processing node is any callable that accepts a log entry dict and
# returns either a (possibly mutated) dict or None to drop the entry.
StepFn = Callable[[Dict[str, Any]], Optional[Dict[str, Any]]]

# A sink is any callable that accepts a log entry dict for final output.
SinkFn = Callable[[Dict[str, Any]], None]


@dataclasses.dataclass
class TopologyNode:
    """A single named node in the processing topology."""

    name: str
    step: StepFn
    description: str = ""

    def __repr__(self) -> str:  # pragma: no cover
        return f"TopologyNode(name={self.name!r})"


@dataclasses.dataclass
class Topology:
    """Ordered pipeline graph with named nodes and one or more sinks.

    Nodes are applied in insertion order.  Any node that returns ``None``
    short-circuits the remaining pipeline for that entry.
    """

    name: str
    _nodes: List[TopologyNode] = dataclasses.field(default_factory=list, init=False)
    _sinks: List[SinkFn] = dataclasses.field(default_factory=list, init=False)

    # ------------------------------------------------------------------
    # Builder helpers
    # ------------------------------------------------------------------

    def add_step(self, name: str, step: StepFn, description: str = "") -> "Topology":
        """Append a processing step and return *self* for chaining."""
        self._nodes.append(TopologyNode(name=name, step=step, description=description))
        return self

    def add_sink(self, sink: SinkFn) -> "Topology":
        """Register a terminal sink and return *self* for chaining."""
        self._sinks.append(sink)
        return self

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    @property
    def node_names(self) -> List[str]:
        """Ordered list of step names in this topology."""
        return [n.name for n in self._nodes]

    @property
    def sink_count(self) -> int:
        """Number of registered sinks."""
        return len(self._sinks)

    def describe(self) -> str:
        """Return a human-readable summary of the topology."""
        lines = [f"Topology: {self.name}"]
        lines.append(f"  Steps ({len(self._nodes)}):")
        for node in self._nodes:
            desc = f" — {node.description}" if node.description else ""
            lines.append(f"    [{node.name}]{desc}")
        lines.append(f"  Sinks: {self.sink_count}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def process_entry(self, entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Run *entry* through every step, returning the final entry or None."""
        current: Optional[Dict[str, Any]] = entry
        for node in self._nodes:
            if current is None:
                return None
            current = node.step(current)
        return current

    def run(self, entries: Iterable[Dict[str, Any]]) -> int:
        """Process an iterable of entries, forwarding survivors to all sinks.

        Returns the number of entries that reached the sinks.
        """
        if not self._sinks:
            raise RuntimeError(f"Topology '{self.name}' has no registered sinks.")

        delivered = 0
        for entry in entries:
            result = self.process_entry(entry)
            if result is not None:
                for sink in self._sinks:
                    sink(result)
                delivered += 1
        return delivered


# ---------------------------------------------------------------------------
# Convenience factory
# ---------------------------------------------------------------------------

def build_topology(name: str) -> Topology:
    """Create and return an empty :class:`Topology` with the given name."""
    return Topology(name=name)

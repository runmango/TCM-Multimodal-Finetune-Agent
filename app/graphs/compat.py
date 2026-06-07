from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional


try:
    from langgraph.graph import END, StateGraph  # type: ignore

    USING_LANGGRAPH = True
except Exception:
    END = "__end__"
    USING_LANGGRAPH = False

    class _CompiledGraph:
        def __init__(
            self,
            nodes: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]],
            edges: Dict[str, List[str]],
            entry_point: str,
        ) -> None:
            self.nodes = nodes
            self.edges = edges
            self.entry_point = entry_point

        def invoke(self, state: Dict[str, Any]) -> Dict[str, Any]:
            current_state = dict(state)
            current_node: Optional[str] = self.entry_point
            steps = 0

            while current_node and current_node != END:
                if current_node not in self.nodes:
                    raise ValueError("Unknown graph node: %s" % current_node)
                result = self.nodes[current_node](current_state)
                if result is not None:
                    current_state = result
                next_nodes = self.edges.get(current_node, [END])
                current_node = next_nodes[0] if next_nodes else END
                steps += 1
                if steps > 100:
                    raise RuntimeError("Graph execution exceeded 100 steps")

            return current_state

    class StateGraph:
        def __init__(self, state_schema: Any = None) -> None:
            self.state_schema = state_schema
            self.nodes: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {}
            self.edges: Dict[str, List[str]] = {}
            self.entry_point: Optional[str] = None

        def add_node(self, name: str, func: Callable[[Dict[str, Any]], Dict[str, Any]]) -> None:
            self.nodes[name] = func

        def add_edge(self, start: str, end: str) -> None:
            self.edges.setdefault(start, []).append(end)

        def set_entry_point(self, name: str) -> None:
            self.entry_point = name

        def compile(self) -> _CompiledGraph:
            if self.entry_point is None:
                raise ValueError("Graph entry point is not set")
            return _CompiledGraph(self.nodes, self.edges, self.entry_point)


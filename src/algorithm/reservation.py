"""Tracks which nodes and edges are occupied at each turn."""

from typing import Dict, List, Tuple


class ReservationTable:
    """Stores how many drones are at each node/edge per time step."""

    def __init__(self) -> None:
        # node_name -> {time -> count}
        self._nodes: Dict[str, Dict[int, int]] = {}
        # (from, to) -> {time -> count}
        self._edges: Dict[Tuple[str, str], Dict[int, int]] = {}

    def node_count(self, node: str, t: int) -> int:
        """Return how many drones are reserved at *node* at time *t*."""
        if node not in self._nodes:
            return 0
        return self._nodes[node].get(t, 0)

    def edge_count(self, src: str, dst: str, t: int) -> int:
        """Return how many drones are on edge (src→dst) at time *t*."""
        edge = (src, dst)
        if edge not in self._edges:
            return 0
        return self._edges[edge].get(t, 0)

    def reserve_node(self, node: str, t: int) -> None:
        """Mark one drone at *node* at time *t*."""
        if node not in self._nodes:
            self._nodes[node] = {}
        self._nodes[node][t] = self._nodes[node].get(t, 0) + 1

    def reserve_edge(self, src: str, dst: str, t: int) -> None:
        """Mark one drone on edge (src→dst) at time *t*."""
        edge = (src, dst)
        if edge not in self._edges:
            self._edges[edge] = {}
        self._edges[edge][t] = self._edges[edge].get(t, 0) + 1

    def commit_path(self, path: List[Tuple[int, str]]) -> None:
        """Reserve all nodes and edges along a drone's path.

        Args:
            path: Ordered (time, node_name) list for one drone.
        """
        for i, (t, node) in enumerate(path):
            self.reserve_node(node, t)
            if i == 0:
                continue
            prev_t, prev_node = path[i - 1]
            if prev_node == node:
                continue  # drone waited — no edge traversal
            # reserve each transit step through the edge
            for dt in range(t - prev_t):
                self.reserve_edge(prev_node, node, prev_t + dt)

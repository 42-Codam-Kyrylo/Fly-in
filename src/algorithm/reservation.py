"""Node and edge occupancy tracking per time step."""

from collections import defaultdict
from typing import Dict, List, Tuple


class ReservationTable:
    """Tracks drone occupancy on nodes and edges per turn."""

    def __init__(self) -> None:
        self._nodes: Dict[str, Dict[int, int]] = defaultdict(
            lambda: defaultdict(int)
        )
        self._edges: Dict[Tuple[str, str], Dict[int, int]] = defaultdict(
            lambda: defaultdict(int)
        )

    def node_count(self, node: str, t: int) -> int:
        """Return reserved drone count at *node* at time *t*."""
        return self._nodes[node].get(t, 0)

    def edge_count(self, src: str, dst: str, t: int) -> int:
        """Return reserved drone count on edge (src→dst) at time *t*."""
        return self._edges.get((src, dst), {}).get(t, 0)

    def commit_path(self, path: List[Tuple[int, str]]) -> None:
        """Reserve all nodes and edges for a planned drone path.

        Args:
            path: Ordered (time, node_name) tuples for one drone.
        """
        for i, (t, node) in enumerate(path):
            self._nodes[node][t] += 1
            if i == 0:
                continue
            prev_t, prev_node = path[i - 1]
            if prev_node == node:
                continue  # wait — no edge traversal
            for dt in range(t - prev_t):
                self._edges[(prev_node, node)][prev_t + dt] += 1

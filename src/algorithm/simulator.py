"""Priority Planning: routes all drones one by one."""

from collections import defaultdict
from typing import Dict, List, Tuple

from graph.graph import Graph
from algorithm.reservation import ReservationTable
from algorithm.pathfinder import find_path


class SimulationResult:
    """Holds planned drone paths and renders the simulation output."""

    def __init__(
        self,
        paths: Dict[int, List[Tuple[int, str]]],
        graph: Graph,
    ) -> None:
        self.paths = paths
        self.graph = graph
        self.total_turns: int = (
            max(p[-1][0] for p in paths.values()) if paths else 0
        )
        self._events: Dict[int, List[str]] = self._build_events()

    def _build_events(self) -> Dict[int, List[str]]:
        """Build per-turn movement strings from all drone paths."""
        events: Dict[int, List[str]] = defaultdict(list)

        for drone_id, path in sorted(self.paths.items()):
            for i in range(1, len(path)):
                prev_t, prev_node = path[i - 1]
                curr_t, curr_node = path[i]

                if prev_node == curr_node:
                    continue

                if curr_t - prev_t == 1:
                    events[curr_t].append(f"D{drone_id}-{curr_node}")
                else:
                    mid_label = f"{prev_node}-{curr_node}"
                    events[prev_t + 1].append(f"D{drone_id}-{mid_label}")
                    events[curr_t].append(f"D{drone_id}-{curr_node}")

        return events

    def render(self) -> str:
        """Return the full simulation output as a multi-line string."""
        lines: List[str] = []
        for t in range(1, self.total_turns + 1):
            moves = self._events.get(t, [])
            lines.append(" ".join(moves))
        return "\n".join(lines)


class Simulator:
    """Routes all drones using Priority Planning + Space-Time Dijkstra.

    Each drone is planned in order (D1 first, highest priority).
    Later drones route around earlier drones' reservations.
    """

    def __init__(self, graph: Graph) -> None:
        self.graph = graph

    def run(self) -> SimulationResult:
        """Route all drones from start_hub to end_hub.

        Returns:
            SimulationResult with all paths.

        Raises:
            RuntimeError: If any drone has no valid path.
        """
        max_time = (len(self.graph.nodes) + self.graph.nb_drones) * 4
        table = ReservationTable()
        paths: Dict[int, List[Tuple[int, str]]] = {}

        for drone_id in range(1, self.graph.nb_drones + 1):
            path = find_path(
                graph=self.graph,
                start=self.graph.start_hub,
                goal=self.graph.end_hub,
                table=table,
                max_time=max_time,
            )
            if path is None:
                raise RuntimeError(
                    f"No path found for drone {drone_id}. "
                    "Map may be unsolvable within the time limit."
                )
            table.commit_path(path)
            paths[drone_id] = path

        return SimulationResult(paths, self.graph)

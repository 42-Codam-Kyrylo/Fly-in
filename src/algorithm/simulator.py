"""Priority Planning orchestrator: routes all drones, produces output."""

from collections import defaultdict
from typing import Dict, List, Tuple

from graph.graph import Graph
from algorithm.reservation import ReservationTable
from algorithm.pathfinder import find_path


class SimulationResult:
    """Holds planned drone paths and renders the simulation output.

    Attributes:
        paths: Drone ID → ordered (time, node_name) path.
        graph: The routing graph (exposed for the visualiser).
        total_turns: Simulation length — turn on which the last drone
            arrives at end_hub.
    """

    def __init__(
        self,
        paths: Dict[int, List[Tuple[int, str]]],
        graph: Graph,
    ) -> None:
        """Initialize with planned paths.

        Args:
            paths: Drone ID → (time, node) list.
            graph: Routing graph.
        """
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
                    continue  # wait — no output
                if curr_t - prev_t == 1:
                    # Normal or priority move
                    events[curr_t].append(f"D{drone_id}-{curr_node}")
                else:
                    # Restricted zone: 2-turn transit
                    conn = f"{prev_node}-{curr_node}"
                    events[prev_t + 1].append(f"D{drone_id}-{conn}")
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
    """Plans all drones with Priority Planning + Space-Time Dijkstra.

    Each drone is planned in order (D1 first, highest priority).
    Later drones route around earlier drones' reservations.
    All drones start at start_hub at t=0.
    """

    def __init__(self, graph: Graph) -> None:
        """Initialize with a built graph.

        Args:
            graph: Routing graph.
        """
        self.graph = graph

    def run(self) -> SimulationResult:
        """Route all drones from start_hub to end_hub.

        Returns:
            SimulationResult containing paths and rendered output.

        Raises:
            RuntimeError: If any drone cannot reach the goal.
        """
        max_time = (len(self.graph.nodes) + self.graph.nb_drones) * 4
        table = ReservationTable()
        paths: Dict[int, List[Tuple[int, str]]] = {}

        for drone_id in range(1, self.graph.nb_drones + 1):
            path = find_path(
                self.graph,
                self.graph.start_hub,
                self.graph.end_hub,
                start_time=0,
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

"""Terminal-based visualiser providing colored output of the simulation."""

from typing import Dict, List, Optional, Tuple
from graph.graph import Graph
from algorithm.simulator import SimulationResult


class TerminalRenderer:
    """Renders the simulation state turn-by-turn to the terminal."""

    # ANSI color mapping for common colors
    COLORS: Dict[str, str] = {
        "red": "\033[91m",
        "orange": "\033[38;5;208m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "gray": "\033[90m",
        "black": "\033[30m",
        "purple": "\033[95m",
        "gold": "\033[38;5;220m",
        "maroon": "\033[38;5;88m",
        "darkred": "\033[31m",
        "brown": "\033[38;5;94m",
        "cyan": "\033[96m",
        "crimson": "\033[38;5;161m",
        "lime": "\033[38;5;118m",
        "magenta": "\033[35m",
        "rainbow": "\033[38;5;51m",
        "violet": "\033[38;5;129m",
    }
    RESET = "\033[0m"

    def __init__(self, graph: Graph, result: SimulationResult) -> None:
        self.graph = graph
        self.result = result

    def _get_ansi(self, color_name: Optional[str]) -> str:
        if not color_name:
            return ""
        return self.COLORS.get(color_name.lower(), "")

    def _get_drone_node(
        self, path: List[Tuple[int, str]], time: int
    ) -> str:
        """Find the node a drone is at (or heading to) at a given time."""
        if time <= path[0][0]:
            return path[0][1]
        if time >= path[-1][0]:
            return path[-1][1]

        for i in range(1, len(path)):
            if path[i - 1][0] <= time <= path[i][0]:
                # If it's in transit, it occupies the destination node in logic
                return path[i][1]

        return path[-1][1]

    def run(self) -> None:
        """Print the simulation turn-by-turn."""
        print("\n" + "=" * 40)
        print(" TERMINAL VISUALISATION ".center(40, "="))
        print("=" * 40)

        for t in range(self.result.total_turns + 1):
            print(f"\n--- Turn {t} ---")

            node_drones: Dict[str, List[int]] = {}
            for did, path in self.result.paths.items():
                current_node = self._get_drone_node(path, t)
                if current_node not in node_drones:
                    node_drones[current_node] = []
                node_drones[current_node].append(did)

            for node_name in sorted(self.graph.nodes.keys()):
                node = self.graph.nodes[node_name]
                drones = node_drones.get(node_name, [])

                # Only print nodes that have drones, or if it's a hub
                is_start = node_name == self.graph.start_hub
                is_end = node_name == self.graph.end_hub
                if not drones and not (is_start or is_end):
                    continue

                color_str = self.graph.zone_color(node_name)
                ansi = self._get_ansi(color_str)
                reset = self.RESET if ansi else ""

                drone_str = ", ".join(f"D{d}" for d in sorted(drones))
                z_type = node.zone.metadata.zone_type.name

                if drones:
                    print(
                        f"  {ansi}[{node_name}]{reset} "
                        f"({z_type}): {drone_str}"
                    )
                else:
                    print(f"  {ansi}[{node_name}]{reset} ({z_type}): (empty)")

        print("\n" + "=" * 40 + "\n")

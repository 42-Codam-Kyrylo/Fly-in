# flake8: noqa
"""Integration tests: run every map and verify correctness of results."""

import os
import sys
import pytest

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from packages.parsing import ConfigParser
from graph.graph import Graph
from algorithm.simulator import Simulator, SimulationResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MAPS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "maps", "intra")
)


def _run(relative_path: str) -> tuple[Graph, SimulationResult]:
    """Parse map, build graph, run simulation, return both."""
    full_path = os.path.join(MAPS_DIR, relative_path)
    config = ConfigParser(full_path).parse()
    graph = Graph(config)
    result = Simulator(graph).run()
    return graph, result


def _check_correctness(graph: Graph, result: SimulationResult) -> None:
    """Assert that the simulation result obeys all rules.

    Checks:
    - Every drone path starts at start_hub and ends at end_hub.
    - No two drones share a node that exceeds its capacity at any turn.
    - No BLOCKED zone is ever visited.
    - No edge exceeds its max_link_capacity at any time step.
    - No RESTRICTED zone is visited as a quick (1-turn) hop — must take 2 turns.
    """
    from packages.parsing.config_models import ZoneType

    # --- 1. Start and end hubs ---
    for drone_id, path in result.paths.items():
        assert path[0][1] == graph.start_hub, (
            f"D{drone_id} does not start at start_hub"
        )
        assert path[-1][1] == graph.end_hub, (
            f"D{drone_id} does not end at end_hub"
        )

    # --- 2. BLOCKED zones never visited ---
    for drone_id, path in result.paths.items():
        for t, node in path:
            node_obj = graph.get_node(node)
            zone_type = node_obj.zone.metadata.zone_type
            assert zone_type != ZoneType.BLOCKED, (
                f"D{drone_id} visited BLOCKED zone '{node}' at t={t}"
            )

    # --- 3. Node capacity never exceeded ---
    # Count how many drones are at each node at each time step
    node_occupancy: dict[tuple[str, int], int] = {}
    for drone_id, path in result.paths.items():
        for t, node in path:
            key = (node, t)
            node_occupancy[key] = node_occupancy.get(key, 0) + 1

    for (node, t), count in node_occupancy.items():
        cap = graph.get_node(node).capacity
        assert count <= cap, (
            f"Node '{node}' has {count} drones at t={t}, capacity={cap}"
        )

    # --- 4. Edge capacity never exceeded ---
    # Count drones on each directed edge at each transit step
    edge_occupancy: dict[tuple[str, str, int], int] = {}
    for drone_id, path in result.paths.items():
        for i in range(1, len(path)):
            prev_t, prev_node = path[i - 1]
            curr_t, curr_node = path[i]
            if prev_node == curr_node:
                continue  # wait — no edge
            for dt in range(curr_t - prev_t):
                key = (prev_node, curr_node, prev_t + dt)
                edge_occupancy[key] = edge_occupancy.get(key, 0) + 1

    for (src, dst, t), count in edge_occupancy.items():
        # Find edge capacity from graph
        cap = None
        for edge in graph.get_neighbors(src):
            if edge.to_zone == dst:
                cap = edge.max_link_capacity
                break
        if cap is not None:
            assert count <= cap, (
                f"Edge '{src}→{dst}' has {count} drones at t={t}, "
                f"max_link_capacity={cap}"
            )

    # --- 5. RESTRICTED zones take exactly 2 turns to traverse ---
    from packages.parsing.config_models import ZoneType
    for drone_id, path in result.paths.items():
        for i in range(1, len(path)):
            prev_t, prev_node = path[i - 1]
            curr_t, curr_node = path[i]
            if prev_node == curr_node:
                continue  # wait step
            dest_node = graph.get_node(curr_node)
            travel = curr_t - prev_t
            if dest_node.zone.metadata.zone_type == ZoneType.RESTRICTED:
                assert travel == 2, (
                    f"D{drone_id} reached RESTRICTED zone '{curr_node}' "
                    f"in {travel} turns (expected 2)"
                )
            else:
                assert travel == 1, (
                    f"D{drone_id} moved to '{curr_node}' in {travel} turns "
                    f"(expected 1)"
                )


# ---------------------------------------------------------------------------
# Easy maps
# ---------------------------------------------------------------------------

class TestEasyMaps:
    def test_01_linear_path(self):
        graph, result = _run("easy/01_linear_path.txt")
        _check_correctness(graph, result)
        assert result.total_turns <= 10, (
            f"Expected ≤10 turns, got {result.total_turns}"
        )

    def test_02_simple_fork(self):
        graph, result = _run("easy/02_simple_fork.txt")
        _check_correctness(graph, result)
        assert result.total_turns <= 10, (
            f"Expected ≤10 turns, got {result.total_turns}"
        )

    def test_03_basic_capacity(self):
        graph, result = _run("easy/03_basic_capacity.txt")
        _check_correctness(graph, result)
        assert result.total_turns <= 10, (
            f"Expected ≤10 turns, got {result.total_turns}"
        )


# ---------------------------------------------------------------------------
# Medium maps
# ---------------------------------------------------------------------------

class TestMediumMaps:
    def test_01_dead_end_trap(self):
        graph, result = _run("medium/01_dead_end_trap.txt")
        _check_correctness(graph, result)
        assert result.total_turns <= 30, (
            f"Expected ≤30 turns, got {result.total_turns}"
        )

    def test_02_circular_loop(self):
        graph, result = _run("medium/02_circular_loop.txt")
        _check_correctness(graph, result)
        assert result.total_turns <= 30, (
            f"Expected ≤30 turns, got {result.total_turns}"
        )

    def test_03_priority_puzzle(self):
        graph, result = _run("medium/03_priority_puzzle.txt")
        _check_correctness(graph, result)
        assert result.total_turns <= 30, (
            f"Expected ≤30 turns, got {result.total_turns}"
        )


# ---------------------------------------------------------------------------
# Hard maps
# ---------------------------------------------------------------------------

class TestHardMaps:
    def test_01_maze_nightmare(self):
        graph, result = _run("hard/01_maze_nightmare.txt")
        _check_correctness(graph, result)
        # No strict turn limit — just must complete

    def test_02_capacity_hell(self):
        graph, result = _run("hard/02_capacity_hell.txt")
        _check_correctness(graph, result)

    def test_03_ultimate_challenge(self):
        graph, result = _run("hard/03_ultimate_challenge.txt")
        _check_correctness(graph, result)


# ---------------------------------------------------------------------------
# Challenger map
# ---------------------------------------------------------------------------

class TestChallengerMaps:
    def test_01_the_impossible_dream(self):
        """Benchmark: reference implementation = 41 turns. We aim for ≤45."""
        graph, result = _run("challenger/01_the_impossible_dream.txt")
        _check_correctness(graph, result)
        assert result.total_turns <= 45, (
            f"Expected ≤45 turns (benchmark=41), got {result.total_turns}"
        )

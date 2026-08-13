# flake8: noqa
"""Tests for PRIORITY zone behaviour using custom maps."""

import os
import sys
import pytest

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from packages.parsing import ConfigParser
from packages.parsing.config_models import ZoneType
from graph.graph import Graph
from algorithm.simulator import Simulator, SimulationResult


PRIORITY_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "maps", "intra", "priority")
)


def _run(filename: str) -> tuple[Graph, SimulationResult]:
    path = os.path.join(PRIORITY_DIR, filename)
    config = ConfigParser(path).parse()
    graph = Graph(config)
    result = Simulator(graph).run()
    return graph, result


def _visited_nodes(result: SimulationResult, drone_id: int) -> set[str]:
    """Return the set of node names visited by a drone."""
    return {node for _, node in result.paths[drone_id]}


# ---------------------------------------------------------------------------
# Map 1: only route goes through priority zones
# start -> prio1 -> prio2 -> goal  (3 turns, no alternative)
# ---------------------------------------------------------------------------

class TestPriorityOnlyPath:
    """Drone must pass through priority zones when there is no other route."""

    def test_arrives_in_3_turns(self):
        _, result = _run("01_priority_only_path.txt")
        assert result.total_turns == 3

    def test_drone_visits_prio1(self):
        _, result = _run("01_priority_only_path.txt")
        assert "prio1" in _visited_nodes(result, 1), (
            "D1 should pass through prio1 (priority zone)"
        )

    def test_drone_visits_prio2(self):
        _, result = _run("01_priority_only_path.txt")
        assert "prio2" in _visited_nodes(result, 1), (
            "D1 should pass through prio2 (priority zone)"
        )

    def test_both_visited_nodes_are_priority(self):
        """Every intermediate node on the path is a PRIORITY zone."""
        graph, result = _run("01_priority_only_path.txt")
        for _, node in result.paths[1]:
            if node in (graph.start_hub, graph.end_hub):
                continue
            zone_type = graph.get_node(node).zone.metadata.zone_type
            assert zone_type == ZoneType.PRIORITY, (
                f"Node '{node}' is {zone_type}, expected PRIORITY"
            )


# ---------------------------------------------------------------------------
# Map 2: priority path (2 turns) vs restricted path (3 turns)
# Dijkstra always picks the earliest arrival — must choose priority route.
# ---------------------------------------------------------------------------

class TestPriorityBeatsRestricted:
    """Drone prefers 2-turn priority path over 3-turn restricted path."""

    def test_arrives_in_2_turns_not_3(self):
        _, result = _run("02_priority_beats_restricted.txt")
        assert result.total_turns == 2, (
            f"Expected 2 turns (via priority), got {result.total_turns} "
            f"(drone may have taken the slower restricted path)"
        )

    def test_drone_chose_priority_zone(self):
        _, result = _run("02_priority_beats_restricted.txt")
        visited = _visited_nodes(result, 1)
        assert "via_priority" in visited, (
            "D1 should travel via the priority zone (faster path)"
        )

    def test_drone_did_not_use_restricted_zone(self):
        _, result = _run("02_priority_beats_restricted.txt")
        visited = _visited_nodes(result, 1)
        assert "via_restricted" not in visited, (
            "D1 should NOT use the restricted zone — it is slower"
        )


# ---------------------------------------------------------------------------
# Map 3: priority shortcut (2 turns) vs longer normal detour (3 turns)
# ---------------------------------------------------------------------------

class TestPriorityShortcut:
    """Drone takes 2-hop priority shortcut instead of 3-hop normal detour."""

    def test_arrives_in_2_turns_not_3(self):
        _, result = _run("03_priority_shortcut.txt")
        assert result.total_turns == 2, (
            f"Expected 2 turns (via shortcut), got {result.total_turns}"
        )

    def test_drone_chose_shortcut(self):
        _, result = _run("03_priority_shortcut.txt")
        assert "shortcut" in _visited_nodes(result, 1), (
            "D1 should pass through 'shortcut' (priority zone, 2 hops)"
        )

    def test_drone_did_not_take_detour(self):
        _, result = _run("03_priority_shortcut.txt")
        visited = _visited_nodes(result, 1)
        assert "normal1" not in visited and "normal2" not in visited, (
            "D1 should NOT use the 3-hop normal detour"
        )


# ---------------------------------------------------------------------------
# Map 4: priority zone capacity=1 — D1 or D2 takes priority, other takes normal
# Both must arrive in 2 turns. Node capacity must never be exceeded.
# ---------------------------------------------------------------------------

class TestPriorityCapacity:
    """When priority zone capacity=1, only one drone can use it at a time."""

    def test_both_drones_arrive(self):
        _, result = _run("04_priority_capacity.txt")
        assert 1 in result.paths and 2 in result.paths

    def test_both_arrive_in_2_turns(self):
        _, result = _run("04_priority_capacity.txt")
        assert result.total_turns == 2, (
            f"Expected 2 turns, got {result.total_turns}"
        )

    def test_priority_zone_used_by_exactly_one_drone(self):
        """Exactly one drone passes through the capacity-1 priority zone."""
        _, result = _run("04_priority_capacity.txt")
        d1_visits = "priority" in _visited_nodes(result, 1)
        d2_visits = "priority" in _visited_nodes(result, 2)
        users = int(d1_visits) + int(d2_visits)
        assert users == 1, (
            f"Expected exactly 1 drone to use 'priority' zone, got {users}"
        )

    def test_priority_zone_never_over_capacity(self):
        """At no turn do two drones occupy the priority node simultaneously."""
        _, result = _run("04_priority_capacity.txt")
        # Count drones at priority zone per turn
        occupancy: dict[int, int] = {}
        for drone_id in (1, 2):
            for t, node in result.paths[drone_id]:
                if node == "priority":
                    occupancy[t] = occupancy.get(t, 0) + 1
        for t, count in occupancy.items():
            assert count <= 1, (
                f"Priority zone (cap=1) has {count} drones at t={t}"
            )

    def test_other_drone_uses_normal_zone(self):
        """The drone that cannot use priority must go through normal zone."""
        _, result = _run("04_priority_capacity.txt")
        d1_visits = _visited_nodes(result, 1)
        d2_visits = _visited_nodes(result, 2)
        # One of the two must have visited 'normal'
        assert "normal" in d1_visits or "normal" in d2_visits, (
            "One drone should have been rerouted through 'normal' zone"
        )


# ---------------------------------------------------------------------------
# Map 5: Tiebreaker — equal-cost fork: priority vs normal (both 2 turns)
# This is the key test: when arrival time is identical, drone must pick
# the route that passes through a PRIORITY zone.
# ---------------------------------------------------------------------------

class TestTiebreakerPriorityVsNormal:
    """When two paths have equal travel time, drone must prefer priority."""

    def test_arrives_in_2_turns(self):
        _, result = _run("05_tiebreaker_priority_vs_normal.txt")
        assert result.total_turns == 2

    def test_drone_chose_priority_not_normal(self):
        """Core tiebreaker assertion: priority zone chosen over normal."""
        _, result = _run("05_tiebreaker_priority_vs_normal.txt")
        visited = _visited_nodes(result, 1)
        assert "priority_zone" in visited, (
            "D1 should choose the PRIORITY path when cost is equal"
        )
        assert "normal_zone" not in visited, (
            "D1 should NOT go through normal_zone when priority_zone costs the same"
        )


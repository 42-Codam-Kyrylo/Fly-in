"""Space-Time Dijkstra: finds shortest path for one drone."""

import heapq
from typing import Dict, List, Optional, Tuple

from graph.graph import Graph
from algorithm.reservation import ReservationTable


def find_path(
    graph: Graph,
    start: str,
    goal: str,
    table: ReservationTable,
    max_time: int,
) -> Optional[List[Tuple[int, str]]]:
    """Find the fastest path from *start* to *goal* for one drone.

    Args:
        graph: Routing graph.
        start: Start zone name.
        goal: Goal zone name.
        table: Occupancy reserved by higher-priority drones.
        max_time: Hard time-step cap.

    Returns:
        Ordered (time, node) list, or None if unreachable.
    """
    # heap entry: (time, node)
    # We use plain Dijkstra — earliest arrival wins.
    heap: List[Tuple[int, str]] = [(0, start)]

    # best time we've seen to reach each (time, node) state
    visited: Dict[Tuple[int, str], int] = {}

    # how we got to each (time, node): stores the previous (time, node)
    came_from: Dict[Tuple[int, str], Optional[Tuple[int, str]]] = {}
    came_from[(0, start)] = None

    while heap:
        t, node = heapq.heappop(heap)
        state = (t, node)

        # Skip if we already processed this state with a better (lower) time
        if state in visited:
            continue
        visited[state] = t

        # Goal reached — rebuild and return path
        if node == goal:
            return _rebuild_path(came_from, state)

        # Hard cutoff to prevent infinite search
        if t >= max_time:
            continue

        node_obj = graph.get_node(node)

        # Option 1: Wait at the current node for one turn
        if table.node_count(node, t + 1) < node_obj.capacity:
            next_state = (t + 1, node)
            if next_state not in visited:
                if next_state not in came_from:
                    came_from[next_state] = state
                heapq.heappush(heap, (t + 1, node))

        # Option 2: Move to each neighbouring zone
        for edge in graph.get_neighbors(node):
            dest = edge.to_zone
            travel_time = int(edge.cost)
            arrival = t + travel_time

            if arrival > max_time:
                continue

            dest_node = graph.get_node(dest)

            # Check node capacity at arrival
            if table.node_count(dest, arrival) >= dest_node.capacity:
                continue

            # Check edge capacity for every step of the transit
            edge_free = True
            for dt in range(travel_time):
                count = table.edge_count(node, dest, t + dt)
                if count >= edge.max_link_capacity:
                    edge_free = False
                    break
            if not edge_free:
                continue

            next_state = (arrival, dest)
            if next_state not in visited:
                if next_state not in came_from:
                    came_from[next_state] = state
                heapq.heappush(heap, (arrival, dest))

    return None  # no path found


def _rebuild_path(
    came_from: Dict[Tuple[int, str], Optional[Tuple[int, str]]],
    end: Tuple[int, str],
) -> List[Tuple[int, str]]:
    """Walk back through came_from to reconstruct the path."""
    path: List[Tuple[int, str]] = []
    current: Optional[Tuple[int, str]] = end
    while current is not None:
        path.append(current)
        current = came_from[current]
    path.reverse()
    return path

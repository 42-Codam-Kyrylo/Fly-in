"""Space-Time Dijkstra for single-drone pathfinding."""

import heapq
from typing import Dict, List, Optional, Tuple

from graph.graph import Graph
from algorithm.reservation import ReservationTable

# (time, node_name)
type _Key = Tuple[int, str]
# heap entry: (time, priority_penalty, node_name)
type _State = Tuple[int, int, str]


def find_path(
    graph: Graph,
    start: str,
    goal: str,
    start_time: int,
    table: ReservationTable,
    max_time: int,
) -> Optional[List[Tuple[int, str]]]:
    """Find the lowest-time path for one drone, respecting reservations.

    Priority zones break ties when arrival times are equal.

    Args:
        graph: Routing graph.
        start: Start zone name.
        goal: Goal zone name.
        start_time: Departure time step.
        table: Read-only reservations from higher-priority drones.
        max_time: Hard time-step cap.

    Returns:
        Ordered (time, node_name) list, or None if goal is unreachable.
    """
    heap: List[_State] = [(start_time, 0, start)]
    # best priority-penalty seen for each (time, node) state
    best_pp: Dict[_Key, int] = {(start_time, start): 0}
    came_from: Dict[_Key, Optional[_Key]] = {(start_time, start): None}

    while heap:
        t, pp, node = heapq.heappop(heap)
        key: _Key = (t, node)

        if best_pp.get(key, pp + 1) < pp:
            continue  # stale heap entry

        if node == goal:
            return _reconstruct(came_from, key)

        if t >= max_time:
            continue

        node_obj = graph.get_node(node)

        # --- Wait at current node ---
        if table.node_count(node, t + 1) < node_obj.capacity:
            wait_pp = pp + (0 if node_obj.is_priority else 1)
            _relax(
                heap, best_pp, came_from,
                prev=key, nxt=(t + 1, node), pp=wait_pp,
            )

        # --- Move to each routable neighbour ---
        for edge in graph.get_neighbors(node):
            dest = edge.to_zone
            arr_t = t + int(edge.cost)
            if arr_t > max_time:
                continue
            dest_node = graph.get_node(dest)
            if table.node_count(dest, arr_t) >= dest_node.capacity:
                continue
            if not _edge_clear(
                table, node, dest, t, int(edge.cost), edge.max_link_capacity
            ):
                continue
            move_pp = pp + (0 if dest_node.is_priority else 1)
            _relax(
                heap, best_pp, came_from,
                prev=key, nxt=(arr_t, dest), pp=move_pp,
            )

    return None


def _edge_clear(
    table: ReservationTable,
    src: str,
    dst: str,
    t: int,
    cost: int,
    cap: int,
) -> bool:
    """Return True when edge (src→dst) has free capacity for all transit."""
    for dt in range(cost):
        if table.edge_count(src, dst, t + dt) >= cap:
            return False
    return True


def _relax(
    heap: List[_State],
    best_pp: Dict[_Key, int],
    came_from: Dict[_Key, Optional[_Key]],
    prev: _Key,
    nxt: _Key,
    pp: int,
) -> None:
    """Update best path to *nxt* if *pp* improves the known best."""
    if best_pp.get(nxt, pp + 1) > pp:
        best_pp[nxt] = pp
        came_from[nxt] = prev
        t, node = nxt
        heapq.heappush(heap, (t, pp, node))


def _reconstruct(
    came_from: Dict[_Key, Optional[_Key]],
    end: _Key,
) -> List[Tuple[int, str]]:
    path: List[Tuple[int, str]] = []
    cur: Optional[_Key] = end
    while cur is not None:
        path.append(cur)
        cur = came_from[cur]
    path.reverse()
    return path

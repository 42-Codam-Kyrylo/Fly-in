"""Graph structures for routing drones between zones."""

from typing import Dict, List, Optional, Set, Tuple
from packages.parsing.config_models import Zone, Config, ZoneType


class Edge:
    """Directed connection between two zones."""

    def __init__(
        self,
        to_zone: str,
        max_link_capacity: int,
        cost: int | float,
        is_two_turn: bool,
    ) -> None:
        """Initialize an edge.

        Args:
            to_zone: Destination zone name.
            max_link_capacity: Max simultaneous drones on this link.
            cost: Movement cost derived from the destination zone type.
            is_two_turn: True when the destination is a RESTRICTED zone.
        """
        self.to_zone: str = to_zone
        self.max_link_capacity: int = max_link_capacity
        self.cost: int | float = cost
        self.is_two_turn: bool = is_two_turn


class Node:
    """Zone in the routing graph."""

    def __init__(self, zone: Zone, capacity: int) -> None:
        """Initialize a node.

        Args:
            zone: Zone configuration data.
            capacity: Max drones this node can hold.
        """
        self.zone: Zone = zone
        self.capacity: int = capacity
        self.neighbors: List[Edge] = []
        self.is_routable: bool = (
            zone.metadata.zone_type != ZoneType.BLOCKED
        )

    @property
    def name(self) -> str:
        """Return the zone name."""
        return self.zone.name

    @property
    def cost(self) -> int | float:
        """Return the movement cost for entering this zone."""
        return self.zone.metadata.zone_type.cost

    @property
    def is_priority(self) -> bool:
        """Return True when zone_type is PRIORITY."""
        return self.zone.metadata.zone_type == ZoneType.PRIORITY

    @property
    def is_restricted(self) -> bool:
        """Return True when zone_type is RESTRICTED (2-turn)."""
        return self.zone.metadata.zone_type == ZoneType.RESTRICTED

    @property
    def is_blocked(self) -> bool:
        """Return True when zone_type is BLOCKED."""
        return self.zone.metadata.zone_type == ZoneType.BLOCKED


class Graph:
    """Routing graph built from the parsed configuration.

    BLOCKED nodes are kept for visualisation but excluded from routing
    edges so the algorithm never visits them.
    """

    def __init__(self, config: Config) -> None:
        """Initialize the graph from a configuration.

        Args:
            config: Parsed configuration containing zones and connections.
        """
        self.nodes: Dict[str, Node] = {}
        self.start_hub: str = config.start_hub.name
        self.end_hub: str = config.end_hub.name
        self.nb_drones: int = config.nb_drones
        # All edges including BLOCKED destinations — for visualisation.
        self.all_edges: List[Tuple[str, str, int]] = []
        self._init_graph(config)

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def _init_graph(self, config: Config) -> None:
        """Populate nodes and bidirectional edges from config.

        Args:
            config: Parsed configuration containing zones and connections.
        """
        self._add_node(config.start_hub, config.nb_drones)
        self._add_node(config.end_hub, config.nb_drones)

        for hub in config.hubs.values():
            self._add_node(hub, hub.metadata.max_drones)

        for conn in config.connections:
            endpoints: List[str] = conn.connection.split("-")
            if len(endpoints) != 2:
                continue
            z1, z2 = endpoints[0], endpoints[1]

            self.all_edges.append((z1, z2, conn.max_link_capacity))
            self.all_edges.append((z2, z1, conn.max_link_capacity))

            if self._is_routable(z1) and self._is_routable(z2):
                self._add_edge(z1, z2, conn.max_link_capacity)
                self._add_edge(z2, z1, conn.max_link_capacity)

    def _add_node(self, zone: Zone, capacity: int) -> None:
        """Add a node if not already present.

        Args:
            zone: Zone to add.
            capacity: Capacity assigned to the node.
        """
        if zone.name not in self.nodes:
            self.nodes[zone.name] = Node(zone, capacity)

    def _add_edge(self, from_zone: str, to_zone: str, capacity: int) -> None:
        """Add a directed edge between two existing routable nodes.

        Args:
            from_zone: Source zone name.
            to_zone: Destination zone name.
            capacity: Link capacity.
        """
        if from_zone not in self.nodes or to_zone not in self.nodes:
            return
        dest = self.nodes[to_zone]
        edge = Edge(
            to_zone=to_zone,
            max_link_capacity=capacity,
            cost=dest.cost,
            is_two_turn=dest.is_restricted,
        )
        self.nodes[from_zone].neighbors.append(edge)

    # ------------------------------------------------------------------
    # Algorithm helpers
    # ------------------------------------------------------------------

    def get_node(self, zone_name: str) -> Node:
        """Return the node for a zone name.

        Args:
            zone_name: Zone to look up.

        Returns:
            The corresponding Node.

        Raises:
            KeyError: If the zone name is not in the graph.
        """
        return self.nodes[zone_name]

    def get_neighbors(self, zone_name: str) -> List[Edge]:
        """Return routable outgoing edges for a zone.

        Args:
            zone_name: Source zone name.

        Returns:
            List of outgoing Edge objects (empty if zone unknown).
        """
        node = self.nodes.get(zone_name)
        return node.neighbors if node else []

    def routable_nodes(self) -> List[Node]:
        """Return all non-BLOCKED nodes.

        Returns:
            List of routable Node objects.
        """
        return [n for n in self.nodes.values() if n.is_routable]

    def is_routable(self, zone_name: str) -> bool:
        """Return True when the zone exists and is not BLOCKED.

        Args:
            zone_name: Zone name to check.

        Returns:
            True if present and routable.
        """
        return self._is_routable(zone_name)

    def _is_routable(self, zone_name: str) -> bool:
        node = self.nodes.get(zone_name)
        return node is not None and node.is_routable

    # ------------------------------------------------------------------
    # Visualisation helpers
    # ------------------------------------------------------------------

    def zone_position(self, zone_name: str) -> Tuple[int, int]:
        """Return (x, y) coordinates of a zone.

        Args:
            zone_name: Zone to look up.

        Returns:
            Tuple (x, y).

        Raises:
            KeyError: If the zone name is not in the graph.
        """
        zone = self.nodes[zone_name].zone
        return zone.x, zone.y

    def zone_color(self, zone_name: str) -> Optional[str]:
        """Return the configured display color of a zone, or None.

        Args:
            zone_name: Zone to look up.

        Returns:
            Color string or None.
        """
        color = self.nodes[zone_name].zone.metadata.color
        return str(color) if color is not None else None

    def zone_type(self, zone_name: str) -> ZoneType:
        """Return the ZoneType of a zone.

        Args:
            zone_name: Zone to look up.

        Returns:
            ZoneType enum value.
        """
        return self.nodes[zone_name].zone.metadata.zone_type

    def all_zone_names(self) -> Set[str]:
        """Return all zone names including BLOCKED ones.

        Returns:
            Set of every zone name in the graph.
        """
        return set(self.nodes.keys())

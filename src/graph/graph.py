"""Graph structures for routing drones between zones."""

from typing import Dict, List, Union
from packages.parsing.config_models import Zone, Config

default_cost: Union[int, float] = 1.0


class Edge:
    """Represent a directed connection between two zones."""

    def __init__(self, to_zone: str, max_link_capacity: int) -> None:
        """Initialize an edge.

        Args:
            to_zone: Destination zone name.
            max_link_capacity: Maximum number of drones that can traverse it.
        """
        self.to_zone: str = to_zone
        self.max_link_capacity: int = max_link_capacity


class Node:
    """Represent a zone in the graph."""

    def __init__(self, zone: Zone, capacity: int) -> None:
        """Initialize a node.

        Args:
            zone: Zone configuration data.
            capacity: Maximum number of drones this node can hold.
        """
        self.zone: Zone = zone
        self.capacity: int = capacity
        self.neighbors: List[Edge] = []

    @property
    def cost(self) -> Union[int, float]:
        """Return the movement cost for entering this zone.

        Returns:
            The configured turn cost, or 1.0 when no numeric cost is set.
        """
        cost = self.zone.metadata.zone_type.cost
        if isinstance(cost, (int, float)):
            return cost
        return default_cost


class Graph:
    """Represent the routing graph built from the configuration."""

    def __init__(self, config: Config) -> None:
        """Initialize the graph from a configuration.

        Args:
            config: Parsed configuration containing zones and connections.
        """
        self.nodes: Dict[str, Node] = {}
        self._init_graph(config)

    def _init_graph(self, config: Config) -> None:
        """Populate the graph with nodes and bidirectional edges.

        Args:
            config: Parsed configuration containing zones and connections.
        """
        self._add_node(config.start_hub, config.nb_drones)
        self._add_node(config.end_hub, config.nb_drones)

        for hub in config.hubs.values():
            self._add_node(hub, hub.metadata.max_drones)

        for conn in config.connections:
            endpoints: List[str] = conn.connection.split("-")
            if len(endpoints) == 2:
                z1: str = endpoints[0]
                z2: str = endpoints[1]
                self._add_edge(z1, z2, conn.max_link_capacity)
                self._add_edge(z2, z1, conn.max_link_capacity)

    def _add_node(self, zone: Zone, capacity: int) -> None:
        """Add a node if it is not already present.

        Args:
            zone: Zone to add.
            capacity: Capacity assigned to the node.
        """
        if zone.name not in self.nodes:
            self.nodes[zone.name] = Node(zone, capacity)

    def _add_edge(self, from_zone: str, to_zone: str, capacity: int) -> None:
        """Add a directed edge between two existing nodes.

        Args:
            from_zone: Source zone name.
            to_zone: Destination zone name.
            capacity: Link capacity.
        """
        if from_zone in self.nodes and to_zone in self.nodes:
            edge: Edge = Edge(to_zone, capacity)
            self.nodes[from_zone].neighbors.append(edge)

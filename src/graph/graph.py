"""Module for graph representation of the drone routing network."""

from typing import Dict, List, Union
from packages.parsing.config_models import Zone, Config


class Edge:
    """Represents a connection between two zones in the graph.

    Attributes:
        to_zone (str): The name of the destination zone.
        max_link_capacity (int): Maximum number of drones that can traverse
            simultaneously.
    """

    def __init__(self, to_zone: str, max_link_capacity: int) -> None:
        """Initialize an edge.

        Args:
            to_zone: The name of the destination zone.
            max_link_capacity: The maximum link capacity.
        """
        self.to_zone: str = to_zone
        self.max_link_capacity: int = max_link_capacity


class Node:
    """Represents a zone (hub) in the graph.

    Attributes:
        zone (Zone): The zone configuration data including metadata.
        neighbors (List[Edge]): List of outgoing connections from this zone.
        capacity (int): Maximum number of drones the zone can hold.
    """

    def __init__(self, zone: Zone, capacity: int) -> None:
        """Initialize a node.

        Args:
            zone: The zone configuration data.
            capacity: The capacity of the zone.
        """
        self.zone: Zone = zone
        self.capacity: int = capacity
        self.neighbors: List[Edge] = []

    @property
    def cost(self) -> Union[int, float]:
        """Get the movement cost for this zone.

        Returns:
            The turn cost to enter this zone.
        """
        cost = self.zone.metadata.zone_type.cost
        if isinstance(cost, (int, float)):
            return cost
        return 1.0


class Graph:
    """Graph implementation using an Adjacency List for drone routing.

    Attributes:
        nodes (Dict[str, Node]): Mapping of zone names to their corresponding
            Node objects.
    """

    def __init__(self, config: Config) -> None:
        """Initialize the graph from a Config object.

        Args:
            config: The configuration containing zones and connections.
        """
        self.nodes: Dict[str, Node] = {}
        self._init_graph(config)

    def _init_graph(self, config: Config) -> None:
        """Populate the graph with zones and connections from the config.

        Args:
            config: The configuration data.
        """
        # Add start and end hubs with infinite capacity
        # (represented by nb_drones)
        self._add_node(config.start_hub, config.nb_drones)
        self._add_node(config.end_hub, config.nb_drones)

        # Add other hubs with their defined capacity
        for hub in config.hubs.values():
            self._add_node(hub, hub.metadata.max_drones)

        # Add all connections as bidirectional edges
        for conn in config.connections:
            endpoints: List[str] = conn.connection.split("-")
            if len(endpoints) == 2:
                z1: str = endpoints[0]
                z2: str = endpoints[1]
                self._add_edge(z1, z2, conn.max_link_capacity)
                self._add_edge(z2, z1, conn.max_link_capacity)

    def _add_node(self, zone: Zone, capacity: int) -> None:
        """Add a zone as a node to the graph if it doesn't already exist.

        Args:
            zone: The zone to add.
            capacity: The capacity of the zone.
        """
        if zone.name not in self.nodes:
            self.nodes[zone.name] = Node(zone, capacity)

    def _add_edge(self, from_zone: str, to_zone: str, capacity: int) -> None:
        """Add a connection as an edge between two existing nodes.

        Args:
            from_zone: The starting zone name.
            to_zone: The destination zone name.
            capacity: The link capacity.
        """
        if from_zone in self.nodes and to_zone in self.nodes:
            edge: Edge = Edge(to_zone, capacity)
            self.nodes[from_zone].neighbors.append(edge)

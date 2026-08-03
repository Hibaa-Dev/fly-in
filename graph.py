from typing import List, Dict, Any, Tuple
from conn import Connection
from hub import Hub


class Graph:
    """Manages the entire map network for the drone simulation.

    It holds the collections of all hubs (zones) and connections, remembers
    the starting and ending hubs, tracks the number of drones, and provides
    a fast network layout for pathfinding algorithms.
    """

    def __init__(self) -> None:
        """Sets up an empty graph with all storage systems initialized."""
        self.zones: List[Hub] = []
        self.conn: List[Connection] = []
        self.start_hub_name: str = ""
        self.end_hub_name: str = ""
        self.nb_drones: int = 0
        self.zone_lookup: Dict[str, Hub] = {}
        self.adjacency: Dict[str, List[Tuple[str, Connection]]] = {}

    def create_zone(self, map: Dict[str, Any]) -> None:
        """Converts raw hub data from the parsed map dictionary into Hub
            objects.

        This method extracts the total number of drones, identifies which hubs
        are the start and end points, creates live Hub objects, and prepares
        empty slots in the adjacency list for neighbors.

        Args:
            map: The complete dictionary of parsed map data from the map file.
        """
        self.nb_drones = map['nb_drones']
        for hub_row in map["hubs"]:
            if hub_row.get("type") == "start_hub":
                self.start_hub_name = hub_row.get("zone_name")
            elif hub_row.get("type") == "end_hub":
                self.end_hub_name = hub_row.get("zone_name")

            zone_obj = Hub(
                kind=hub_row.get("type"),
                name=hub_row.get("zone_name"),
                x=hub_row.get("x"),
                y=hub_row.get("y"),
                zone_type=hub_row["metadata"]["zone"],
                max_drones=hub_row["metadata"]["max_drones"],
                color=hub_row["metadata"]["color"],
            )
            self.zones.append(zone_obj)
            self.zone_lookup[hub_row.get("zone_name")] = zone_obj
            self.adjacency[hub_row.get("zone_name")] = []

    def create_conn(self, map: Dict[str, Any]) -> None:
        """Converts raw connection data into Connection objects and links hubs.

        This method builds live Connection instances and links them
        bidirectionally into the adjacency list so that any hub can instantly`
        find its connected neighbor paths.

        Args:
            map: The complete dictionary of parsed map data from the map file.
        """
        for conn_row in map["connections"]:

            src: str = conn_row.get("source")
            trg: str = conn_row.get("target")
            metadata = conn_row["metadata"]

            conn_obj: Connection = Connection(
                name=src + "-" + trg,
                source=src,
                target=trg,
                max_link_capacity=metadata["max_link_capacity"],
            )
            self.conn.append(conn_obj)

            if src in self.adjacency and trg in self.adjacency:
                self.adjacency[trg].append((src, conn_obj))
                self.adjacency[src].append((trg, conn_obj))

    def get_conn(self, src: str, target: str) -> Connection | None:
        """Finds the connection object linking two adjacent hubs.

        Looks through the source hub's adjacency list for an entry whose
        neighbor matches the target hub.

        Args:
            src: The name of the hub to search from.
            target: The name of the neighboring hub to find a link to.

        Returns:
            The Connection object linking src and target, or None if the
            two hubs aren't directly connected.
        """
        for trg in self.adjacency[src]:
            if trg[0] == target:
                return trg[1]
        return None

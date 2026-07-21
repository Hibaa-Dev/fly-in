from typing import List
from graph import Graph
from algorithm import Dijkstra
import copy


class Yen:
    """
    Implements Yen's K-Shortest Paths algorithm tailored for a custom zone
        graph.

    This algorithm discovers alternative top-tier routing paths across
        the network
    by systematically identifying detour intersections ('spur nodes') along
    previously discovered shortest paths. It dynamically isolates
        historical routes and applies a cost-threshold limit to filter out
        excessively inefficient options.
    """
    def __init__(self, graph: Graph):
        """
        Initializes the Yen algorithm engine with a target network graph.

        Attributes:
            graph (Graph): The central graph network architecture containing
                the global nodes, zones, configurations, and adjacency listings
            djikstra (Dijkstra): The internal pathfinding engine instance used
                to compute shortest paths on modified slices of
                    the adjacency map.
        Args:
            graph (Graph): The central graph network containing nodes,
                           zones, and adjacency listings.
        """
        self.graph: Graph = graph
        self.djikstra = Dijkstra(self.graph)

    def find_shortets_paths(
        self,
        max_path: float = 2.0,
        max_paths: int | None = None
    ) -> List[List[str]]:
        """
        Executes Yen's algorithm to find and rank valid alternative paths.

        Args:
            max_path (float): The maximum allowed cost multiplier relative to
                              the optimal path (e.g., 2.0 allows paths up to
                              twice the cost of the absolute shortest path).
            max_paths: Maximum number of paths to return. Defaults to a
                       bounded value based on map size.

        Returns:
            List[List[str]]: A list of unique paths (each path being a list of
                node names) sorted from shortest to longest cost that fall
                within the threshold constraint.

        Raises:
            ValueError: If the initial Dijkstra run cannot find a valid path
                        between the start and destination hubs.
        """
        self.djikstra.assign()
        first_path = self.djikstra.algo()

        if not first_path:
            return []

        if max_paths is None:
            max_paths = min(self.graph.nb_drones, max(1, len(self.graph.zones)))

        best_distance = self.djikstra.distances[self.graph.end_hub_name]
        max_allowed_cost = best_distance * max_path

        A: List[List[str]] = [first_path]
        B: List[tuple[int | float, List[str]]] = []

        while len(A) < max_paths:
            previous_path = A[-1]
            # find the spur node:
            for i in range(len(previous_path) - 1):
                spur_node = previous_path[i]
                root_path = previous_path[:i + 1]
                adjacent_copy = copy.deepcopy(self.graph.adjacency)
                
                for locked_path in A:
                    if (len(locked_path) > i + 1 and
                            locked_path[:i + 1] == root_path):
                        next_conn = locked_path[i + 1]
                    # -----delete conn between spur node and next node
                        adjacent_copy[spur_node] = [
                            edge for edge in adjacent_copy[spur_node]
                            if edge[0] != next_conn
                        ]
                        
                # Remove the visited node:
                for node in root_path[:-1]:
                    adjacent_copy[node] = []

                # Start Djikstra
                self.djikstra.adjacency = adjacent_copy
                self.djikstra.assign(spur_node)
                spur_path = self.djikstra.algo()

                # get the paths:
                if spur_path:
                    total_path = root_path[:-1] + spur_path

                    total_cost: float = sum(
                        self.graph.zone_lookup[hub].cost or 0.0
                        for hub in total_path)

                    extart_B = [items[1] for items in B]
                    if (total_cost <= max_allowed_cost
                            and total_path not in A
                            and total_path not in extart_B):
                        B.append((total_cost, total_path))

            if not B:
                break
            B.sort()
            best_cost, zone = B.pop(0)
            A.append(zone)
        return A

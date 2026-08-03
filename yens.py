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

    K: int = 20

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

    def path_cost(self, path: List[str]) -> float:
        """
        Computes the total zone-based cost of a path, summing each hub's
        movement cost along the route.

        Args:
            path: A list of hub names describing the route.

        Returns:
            The total cost of traversing every hub in the path.
        """
        return sum(self.graph.zone_lookup[hub].cost or 0.0
                   for hub in path)

    def find_shortets_paths(
        self,
        max_path: float = 2.0,
    ) -> List[List[str]]:
        """
        Executes Yen's algorithm to find up to K candidate paths, then
        returns them ranked from closest to farthest from the shortest
        path's cost.

        Args:
            max_path (float): The maximum allowed cost multiplier relative to
                              the optimal path (e.g., 2.0 allows paths up to
                              twice the cost of the absolute shortest path).
                              Acts purely as a safety cutoff to avoid wasting
                              time exploring wildly inefficient detours.

        Returns:
            List[List[str]]: Up to K unique paths (each path being a list of
                node names), sorted so the path whose cost is closest to the
                shortest path's cost comes first.

        Raises:
            ValueError: If the initial Dijkstra run cannot find a valid path
                        between the start and destination hubs.
        """
        self.djikstra.assign()
        first_path = self.djikstra.algo()

        if not first_path:
            return []

        max_paths = self.K

        # get the code of the shortest path
        best_distance = self.djikstra.distances[self.graph.end_hub_name]
        max_allowed_cost = best_distance * max_path

        A: List[List[str]] = [first_path]
        A_costs: List[float] = [self.path_cost(first_path)]
        B: List[tuple[int | float, List[str]]] = []

        while len(A) < max_paths:
            previous_path = A[-1]
            # find the spur node:
            for i in range(len(previous_path) - 1):
                spur_node = previous_path[i]
                root_path = previous_path[: i + 1]
                adjacent_copy = copy.deepcopy(self.graph.adjacency)

                for lp in A:
                    if len(lp) > i + 1 and lp[: i + 1] == root_path:
                        next_conn = lp[i + 1]
                        # delete conn between spur node and next node
                        adjacent_copy[spur_node] = [
                            edge
                            for edge in adjacent_copy[spur_node]
                            if edge[0] != next_conn
                        ]

                # Remove the visited node conn:
                for node in root_path[:-1]:
                    adjacent_copy[node] = []

                # Start Djikstra
                self.djikstra.adjacency = adjacent_copy
                self.djikstra.assign(spur_node)
                spur_path = self.djikstra.algo()

                # get the paths:
                if spur_path:
                    total_path = root_path[:-1] + spur_path
                    total_cost: float = self.path_cost(total_path)

                    # extart_B = [["A","B","D"], ["A","C","D"]]
                    extart_B = [items[1] for items in B]
                    if (
                        total_cost <= max_allowed_cost
                        and total_path not in A
                        and total_path not in extart_B
                    ):
                        B.append((total_cost, total_path))

            if not B:
                break

            B.sort(key=lambda item: abs(item[0] - best_distance))
            best_cost, zone = B.pop(0)
            A.append(zone)
            A_costs.append(best_cost)

        ranked = sorted(
            # zip: combine the path with the cost
            zip(A, A_costs),
            key=lambda pair: abs(pair[1] - best_distance),
        )
        return [path for path, cost in ranked]

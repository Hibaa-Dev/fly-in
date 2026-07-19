from typing import Dict, List, Tuple
from graph import Graph
from hub import Hub
import heapq


class Dijkstra:
    """
    The pathfinding controller that calculates the absolute fastest route
    for a drone from the start hub to the destination hub, taking into
    account turn-based zone movement costs.
    """
    def __init__(self, graph: Graph) -> None:
        """
        Sets up the pathfinder's tracking systems before starting.

        Attributes:
            self.zones: A master list containing every single zone on the map.
            self.adjacency: A connection guide. Give it a hub name, and it
                tells you its directly connected neighbors.
            self.graph: A reference link back to the global map data
                (used to easily check the names of the start and end hubs).
            self.previous: A footprint diary. Maps a hub name to the hub
                we stood on just before it.
            self.distances: A leaderboard scoreboard. Tracks the lowest
                number of turns discovered so far to reach any hub from
                the start.
        """
        self.zones: List[Hub] = graph.zones
        self.adjacency: Dict[str, List[Tuple[str, object]]] = graph.adjacency
        self.graph: Graph = graph
        self.previous: Dict[str, str | None] = {}
        self.distances: Dict[str, int | float] = {}

    def assign(self, start_node: str | None = None) -> None:
        """
        Prepares the map ledgers right before pathfinding.
        Sets the starting hub's distance to 0 (since we are already there)
        and sets all other hubs to infinity (meaning 'unreachable for now').
        """
        if start_node is None:
            start_node = self.graph.start_hub_name
        for z in self.zones:
            if z.name == start_node:
                self.distances[z.name] = 0
            else:
                self.distances[z.name] = float('inf')
            self.previous[z.name] = None

    def min_heap(self) -> List[Tuple[int | float, str]]:
        """
        Gathers our current distance ledger and formats it into a
        prioritized To-Do list (a min-heap). This ensures that Python
        always hands us the hub with the lowest distance value first.

        Returns:
            A sorted-priority list of (distance, hub_name) tuples.
        """
        heap: List[Tuple[int | float, str]] = []
        for key, value in self.distances.items():
            heap.append((value, key))
        heapq.heapify(heap)
        return heap

    def algo(self) -> List[str]:
        """
        Runs the core routing loops. It evaluates zones one by one,
        calculates arrival times based on zone rules (normal, priority,
        restricted), updates shorter paths, and returns the final chronological
        list of zone names from start to finish.

        Returns:
            A list of zone name strings representing the chosen route.
        """
        heap = self.min_heap()
        while heap:
            node = heapq.heappop(heap)
            if node[0] > self.distances[node[1]]:
                continue
            if node[1] == self.graph.end_hub_name:
                break

            for e in self.adjacency[node[1]]:
                neighbor = self.graph.zone_lookup[e[0]]
                if neighbor.zone_type == 'normal':
                    cost = 1
                elif neighbor.zone_type == 'priority':
                    cost = 0.9
                elif neighbor.zone_type == 'restricted':
                    cost = 2
                elif neighbor.zone_type == 'blocked':
                    continue

                new_distance = node[0] + cost
                if new_distance < self.distances[neighbor.name]:
                    self.distances[neighbor.name] = new_distance
                    self.previous[neighbor.name] = node[1]
                    heapq.heappush(heap, (new_distance, neighbor.name))
        if self.distances[self.graph.end_hub_name] == float('inf'):
            return []
        path: List[str] = []
        current: str | None = self.graph.end_hub_name
        while current:
            path.append(current)
            current = self.previous[current]
        return path[::-1]

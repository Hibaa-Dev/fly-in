from typing import Dict


class Connection:
    """Represents a spatial link connecting two distinct zones
        in the map graph.

    Tracks real-time routing capacity and handles turn-based token limits to
    prevent simultaneous traversal overlaps beyond defined constraints.
    """

    def __init__(self, name: str, source: str, target: str,
                 max_link_capacity: int) -> None:
        """Initializes the connection profile with systemic flow attributes.

        Args:
            name: Unique identifying label for the connection pathway.
            source: Name tag of the origin hub.
            target: Name tag of the destination hub.
            max_link_capacity: The maximum total of concurrent drone traversals
                permitted on this link during a single simulation turn step.
            move_by_turn: The maximum number of drones that can move
            simultaneously.
        """
        self.name: str = name
        self.source: str = source
        self.target: str = target
        self.max_link_capacity: int = max_link_capacity

        self.move_by_turn: Dict[int, int] = {}

    def move_at_turn(self, turn: int) -> None:
        """Increments the scheduled traversal token tally for a specific turn.

        Registers a drone's commitment to cross this connection matrix during
        the transition at the specified simulation interval.

        Args:
            turn: The target simulation step index to register.
        """
        self.move_by_turn[turn] = self.move_by_turn.get(turn, 0) + 1

    def can_move(self, turn: int) -> bool:
        """Evaluates if the connection has remaining bandwidth at a
        specific turn.

        Args:
            turn: The targeted simulation chronological turn index.

        Returns:
            True if the current scheduled volume is strictly below the max
            link capacity boundary, False otherwise.
        """
        return self.move_by_turn.get(turn, 0) < self.max_link_capacity

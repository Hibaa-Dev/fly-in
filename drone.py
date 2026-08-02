from typing import List, Optional
from conn import Connection


class Drone:
    """Represents an individual drone moving through the map network.

    It tracks its own identity, its current location, its assigned route,
    and whether it has safely reached the destination hub.
    """

    def __init__(self, id: str, path: List[str], start_zone: str) -> None:
        """Sets up a new drone with its unique ID and planned route.

        Args:
            id: The unique name identifying this drone.
            path: The list of hub names this drone must follow.
            start_zone: the zone from what the drone strat flying
        """
        self.id: str = id
        self.current_zone: str | None = start_zone
        self.path: List[str] = path
        self.is_delivred: bool = False
        self.path_index: int = 0
        self.turns_remaining: int = 0
        self.transit_target: str | None = None
        self.transit_conn: Optional[Connection] = None
        self.is_in_transit: bool = False

    def get_next_zone(self) -> str | None:
        """Looks ahead to the next hub the drone should head towards.

        Returns:
            The name of the next zone on the path, or None if the drone
            is currently in transit or already at the final hub.
        """
        if self.is_in_transit:
            return None
        if self.path_index + 1 < len(self.path):
            return self.path[self.path_index + 1]
        return None

    def move_forward(self) -> None:
        """Moves the drone forward to its next scheduled hub on the path.

        It advances the path tracker index, updates its current location,
        and flags the drone as delivered if it reaches the final finish line.
        """
        next_zone = self.get_next_zone()
        if next_zone:
            self.path_index += 1
            self.current_zone = next_zone
        if self.path_index == len(self.path) - 1:
            self.is_delivred = True

    def strat_transit(
        self, target_zone: str, connection: Connection, travel_time: int
    ) -> None:
        """Starts the drone's journey across a connection to a target zone.

        Puts the drone into an in-transit state, meaning it no longer has
        a current zone until the transit finishes.

        Args:
            target_zone: The hub the drone will arrive at once transit ends.
            connection: The connection/edge object the drone is travelling on.
            travel_time: The number of ticks required to complete the transit.
        """
        self.is_in_transit = True
        self.turns_remaining = travel_time
        self.transit_target = target_zone
        self.transit_conn = connection
        self.current_zone = None

    def tick_transit(self) -> bool:
        """Advances the drone's transit by one turn, if it's in transit.

        Decrements the remaining travel time. When it hits zero, the drone
        arrives at its transit target, its path index advances, and it is
        flagged as delivered if that target is the final hub.

        Returns:
            True if the drone was in transit (and so this tick applied to
            it), False if the drone wasn't in transit at all.
        """
        if self.is_in_transit:
            self.turns_remaining -= 1
            if self.turns_remaining == 0:
                self.is_in_transit = False
                self.current_zone = self.transit_target
                self.path_index += 1
                if self.current_zone == self.path[-1]:
                    self.is_delivred = True
                self.transit_target = None
                self.transit_conn = None
            return True
        return False

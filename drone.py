from typing import List, Optional


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
        self.transit_conn: Optional[object] = None
        self.is_in_transit: bool = False

    def get_next_zone(self) -> str | None:
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
        if self.path_index + 1 == len(self.path) - 1:
            self.is_delivred = True

    def strat_transit(self, target_zone: str, connection: object, travel_time: int) -> None:
        self.is_in_transit = True
        self.turns_remaining = travel_time
        self.transit_target = target_zone
        self.transit_conn = connection
        self.current_zone = None

    def tick_transit(self) -> bool: 
        if self.is_in_transit:
            self.turns_remaining -= 1
            if self.turns_remaining == 0:
                self.is_in_transit = False
                self.current_zone = self.transit_target
                self.path_index += 1
                if self.current_zone == self.path[len(self.path) - 1]:
                    self.is_delivred = True
                self.transit_target = None
                self.transit_conn = None
            return True
        return False


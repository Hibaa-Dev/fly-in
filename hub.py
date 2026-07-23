class Hub:
    """Represents a landing place (hub) on the map.

    It tracks the hub's location, how much it costs to move through it
    based on its zone type, and how many drones are inside it at any moment.
    """

    def __init__(
        self,
        kind: str,
        name: str,
        x: int,
        y: int,
        zone_type: str,
        max_drones: int,
        color: str | None,
    ) -> None:
        """Sets up a new hub with its options and limits.

        Args:
            kind: The role of the hub (like 'hub', 'start_hub', or 'end_hub').
            name: The unique name of this hub.
            x: The horizontal position on the map.
            y: The vertical position on the map.
            zone_type: The type of zone ('normal', 'blocked', 'restricted',
                'priority').
            max_drones: The maximum number of drones allowed here at the same
                time.
            color: An optional color name or code for drawing the map.
            occupy_by_turn: how many drones can occupy a zone simultaneously.
        """
        self.kind: str = kind
        self.name: str = name
        self.x: int | float = x
        self.y: int | float = y
        self.zone_type: str = zone_type
        self.max_drones: int = max_drones
        self.color: str | None = color
        self.cost: int | float | None = self.get_cost()

    def get_cost(self) -> int | float | None:
        """Finds the travel cost based on the zone type.

        Higher numbers mean it takes longer or is harder to cross.
        'blocked' zones cannot be crossed at all.

        Returns:
            The number cost to cross, or infinity if blocked.
        """
        zones = {
            "normal": 1,
            "blocked": float("inf"),
            "restricted": 2,
            "priority": 0.9,
        }
        return zones.get(self.zone_type)

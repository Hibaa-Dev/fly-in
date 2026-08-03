from typing import Dict, List
from graph import Graph
from drone import Drone


class Simulation:
    def __init__(
        self, graph: Graph, paths: List[List[str]],
    ) -> None:
        self.graph: Graph = graph
        self.nb_drones: int = graph.nb_drones
        self.drones: List[Drone] = []
        self.paths: List[List[str]] = paths
        self.output: List[str] = []
        self.frames: List[Dict[str, str | None]] = []
        self.total_turns: int = 0

        self.TERMINAL_COLORS: Dict[str, str] = {
            # Standard ANSI
            "black": "\033[30m",
            "red": "\033[31m",
            "green": "\033[32m",
            "yellow": "\033[33m",
            "blue": "\033[34m",
            "magenta": "\033[35m",
            "cyan": "\033[36m",
            "white": "\033[37m",

            # Bright ANSI
            "gray": "\033[90m",
            "light_red": "\033[91m",
            "light_green": "\033[92m",
            "light_yellow": "\033[93m",
            "light_blue": "\033[94m",
            "light_magenta": "\033[95m",
            "light_cyan": "\033[96m",

            # Colors seen in your maps
            "orange": "\033[38;5;214m",
            "purple": "\033[38;5;129m",
            "brown": "\033[38;5;94m",
            "maroon": "\033[38;5;52m",
            "gold": "\033[38;5;220m",
            "darkred": "\033[38;5;88m",
            "crimson": "\033[38;5;160m",
            "violet": "\033[38;5;177m",

            # Common extras
            "pink": "\033[38;5;213m",
            "navy": "\033[38;5;18m",
            "teal": "\033[38;5;30m",
            "lime": "\033[38;5;118m",
            "olive": "\033[38;5;100m",
            "turquoise": "\033[38;5;44m",
            "indigo": "\033[38;5;54m",
            "coral": "\033[38;5;209m",
            "salmon": "\033[38;5;216m",
            "beige": "\033[38;5;230m",
            "silver": "\033[38;5;250m",
            "aqua": "\033[38;5;51m",

            "rainbow": "\033[38;5;51m",
        }

        self.default_color: str = '\033[37m'
        self.Drone_color: str = '\033[38;5;51m'

    # ------------------get the color of the zone-------------------------
    def get_color(self, color_name: str | None) -> str:
        if color_name is None:
            return self.default_color
        else:
            name = color_name.lower()
            return self.TERMINAL_COLORS.get(name, self.default_color)

    # ---------------------------Format moove-------------------------------
    def format_move(
        self,
        dron_id: str,
        destination: str,
        is_connection: bool = False,
    ) -> str:
        reset = '\033[37m'
        drone_color = f"{self.Drone_color}{dron_id}{reset}"
        if is_connection:
            connection_color = self.get_color('gray')
            target_color = f"{connection_color}{destination}{reset}"

        else:
            if destination in self.graph.zone_lookup:
                hub = self.graph.zone_lookup[destination]
                zone_color: str = self.get_color(hub.color)
            else:
                zone_color = self.get_color('teal')
            target_color = f"{zone_color}{destination}{reset}"

        return f"{drone_color}-{target_color}"

    # -------------------------create Drone objects---------------------------
    def create_drones(self) -> None:
        for i in range(0, self.nb_drones):
            self.drones.append(
                Drone(
                    id=f"D{i + 1}",
                    path=[],
                    start_zone=self.graph.start_hub_name,
                )
            )

    # ----------------------Asign paath to each dron--------------------------
    def assign_path(self) -> None:
        if not self.paths:
            raise ValueError('Can not find path')
        nb_path = min(len(self.drones), len(self.paths))
        for i, drone in enumerate(self.drones):
            index = i % nb_path
            drone.path = self.paths[index]

    # ------------how many drones are occuping a zone--------------------------
    def get_occupy_map(self) -> Dict[str, int]:
        occupied: Dict[str, int] = {}
        for hub in self.graph.zones:
            occupied[hub.name] = 0
        for drone in self.drones:
            if drone.current_zone:
                occupied[drone.current_zone] += 1
        return occupied

    # -------------check if the zone can accept another drone------------------
    def can_move_to_zone(
        self,
        target_zone: str,
        occupied: Dict[str, int],
    ) -> bool:
        # the end_hub can accept any number of drones
        if target_zone == self.graph.end_hub_name:
            return True
        hub = self.graph.zone_lookup[target_zone]
        max_drone = hub.max_drones
        current_count = occupied.get(target_zone, 0)
        return current_count < max_drone

    def run(self, max_turns: int | None = None) -> None:
        self.output = []
        self.frames = []
        turn: int = 0
        initial_frame: Dict[str, str | None] = {
            drone.id: drone.current_zone
            for drone in self.drones
            if drone.current_zone is not None
        }
        self.frames.append(initial_frame)

        while not all(drone.is_delivred for drone in self.drones):
            if max_turns is not None and turn >= max_turns:
                raise RuntimeError("Simulation exceeded test turn limit")

            frame: Dict[str, str | None] = {}
            turn_moves: List[str] = []
            landed_this_turn: set[str] = set()

            # Phase 1: Land mid-flight drones
            for drone in self.drones:
                transit_target = drone.transit_target

                if drone.tick_transit():
                    if not drone.is_in_transit and transit_target:
                        landed_this_turn.add(drone.id)
                        turn_moves.append(
                            f"{drone.id}-{drone.current_zone}"
                        )

            # Phase 2: Recomputes how many drones currently sit
            # in each hub, after Phase 1
            occupied = self.get_occupy_map()

            # Phase 3:
            # gives priority to drones closest to finishing
            drones_by_progress = sorted(
                self.drones,
                key=lambda item: item.path_index,
                reverse=True,
            )
            for drone in drones_by_progress:
                if (
                    drone.is_delivred
                    or drone.is_in_transit
                    or drone.current_zone is None
                    or drone.id in landed_this_turn
                ):
                    continue

                next_zone = drone.get_next_zone()
                if not next_zone:
                    continue
                # get the conn onj of the next zone
                connection = None
                neighbors = self.graph.adjacency.get(
                    drone.current_zone, []
                )
                for neighbor, conn_obj in neighbors:
                    if neighbor == next_zone:
                        connection = conn_obj
                        break

                if (
                    connection
                    and connection.can_move(turn)
                    and self.can_move_to_zone(next_zone, occupied)
                ):

                    target_hub = self.graph.zone_lookup[next_zone]
                    travel_time = (
                        1 if target_hub.zone_type == 'restricted' else 0
                    )
                    current_zone = drone.current_zone

                    if travel_time == 0:
                        drone.move_forward()
                        turn_moves.append(f"{drone.id}-{next_zone}")
                    else:
                        drone.strat_transit(
                            next_zone, connection, travel_time
                        )
                        turn_moves.append(
                            f"{drone.id}-{connection.name}"
                        )

                    connection.move_at_turn(turn)
                    if current_zone:
                        occupied[current_zone] -= 1
                    occupied[next_zone] = (
                        occupied.get(next_zone, 0) + 1
                    )

            for drone in self.drones:
                if drone.is_in_transit and drone.transit_conn is not None:
                    frame[drone.id] = drone.transit_conn.name
                else:
                    frame[drone.id] = drone.current_zone
            self.frames.append(frame)

            if turn_moves:
                turn_moves.sort(key=lambda x: int(x.split("-")[0][1:]))
                colored_moves: List[str] = []
                for move in turn_moves:
                    d_id, dest = move.split('-', 1)
                    is_conn = '-' in dest
                    colored_moves.append(
                        self.format_move(d_id, dest, is_conn)
                    )
                self.output.append(" ".join(colored_moves))
            else:
                self.output.append("")

            turn += 1

        self.total_turns = turn

    def print_output(self) -> None:
        for line in self.output:
            if line.strip():
                print(line)

    def simulation(self) -> None:
        self.create_drones()
        self.assign_path()
        self.run()
        self.print_output()

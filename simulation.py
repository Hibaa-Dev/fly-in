from typing import Dict, List, Union
from hub import Hub
from conn import Connection
from graph import Graph
from drone import Drone


class Simulation:
    def __init__(self, nb_drones: int, graph: Graph, paths: List[List[str]]):
        self.nb_drones: int = nb_drones
        self.graph: Graph = graph
        self.drones: List[Drone] = []
        self.paths: List[List[str]] = paths
        self.output: List[str] = []
        self.frames: List[Dict[str, str]] = []

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

            "rainbow": "\033[38;5;51m"}

        self.default_color: str = '\033[37m'
        self.Drone_color: str = '\033[38;5;51m'

# ------------------------get the color of the zone---------------------------------------
    def get_color(self, color_name: str) -> str:
        if color_name is None:
            return self.default_color
        else:
            name = color_name.lower()
            return self.TERMINAL_COLORS.get(name, self.default_color)
# ---------------------------------Format moove-------------------------------------------

    def format_move(self, dron_id, destication, is_connection: bool = False):
        reset = '\033[37m'
        drone_color = f"{self.Drone_color}{dron_id}{reset}"
        if is_connection:
            connection_color = self.get_color('gray')
            target_color = f"{connection_color}{destication}{reset}"

        else:
            hub = self.graph.zone_lookup[destication]
            zone_color: str = self.get_color(hub.color)
            target_color = f"{zone_color}{destication}{reset}"

        return f"{drone_color}-{target_color}"
        
# ---------------------------create Drone objects--------------------------------------------
    def create_drones(self) -> None:
        for i in range(0, self.nb_drones):
            self.drones.append(
                Drone(id=f"D{i + 1}", path=[], start_zone=self.graph.start_hub_name)
            )

# -------------------------Asign paath to each dron--------------------------------------------

    def assign_path(self) -> None:
        if not self.paths:
            raise ValueError('Can not find path')
        nb_path = min(len(self.drones), len(self.paths))
        for i, drone in enumerate(self.drones):
            index = i % nb_path
            drone.path = self.paths[index]

# ----------------how many drones are occuping a zone----------------------------------
    def get_occupy_map(self) -> Dict[str, int]:
        occupied: Dict[str, int] = {}
        for hub in self.graph.zones:
            occupied[hub.name] = 0
        for drone in self.drones:
            if drone.current_zone:
                occupied[drone.current_zone] += 1
        return occupied

# ---------------------check if the zone can accept another drone------------------------------
    def can_move_to_zone(self, target_zone: str, occupied: Dict[str, int]) -> bool:
        # the end_hub can accept any number of drones
        if target_zone == self.graph.end_hub_name:
            return True
        hub = self.graph.zone_lookup[target_zone]
        max_drone = hub.max_drones
        current_count = occupied.get(target_zone, 0)
        return current_count < max_drone

    def run(self) -> None:
        self.output = []
        turn: int = 0
        
        while not all(drone.is_delivred for drone in self.drones):
            frame = {}
            turn_moves: List[str] = []

            # Phase 1: Land mid-flight drones
            for drone in self.drones:
                # We track if it was a 2-turn restricted flight before ticking
                was_restricted = (
                    drone.is_in_transit and 
                    getattr(self.graph.zone_lookup.get(drone.get_next_zone()), 'zone_type', '') == 'restricted'
                )
                
                if drone.tick_transit():
                    # ONLY log the landing here if it spent consecutive turns in the air!
                    if was_restricted:
                        turn_moves.append(f"{drone.id}-{drone.current_zone}")
            
            # Phase 2: Compute scoreboard & simulate departures
            occupied = self.get_occupy_map()
            for drone in self.drones:
                if drone.current_zone and drone.get_next_zone():
                    occupied[drone.current_zone] -= 1
                
            # Phase 3: Move resting drones
            for drone in self.drones:
                if drone.is_delivred or drone.is_in_transit or drone.current_zone is None:
                    continue

                next_zone = drone.get_next_zone()
                if not next_zone:
                    continue

                # Find connection inline lookup
                connection = None
                for neighbor, conn_obj in self.graph.adjacency.get(drone.current_zone, []):
                    if neighbor == next_zone:
                        connection = conn_obj
                        break

                    if (connection and connection.can_move(turn)
                        and self.can_move_to_zone(next_zone, occupied)):
                    
                        target_hub = self.graph.zone_lookup[next_zone]
                        travel_time = 2 if target_hub.zone_type == 'restricted' else 1
    
                        if travel_time == 1:
                            # Normal move: resolves instantly, drone lands this same turn
                            drone.move_forward()
                            connection.move_at_turn(turn)
                            occupied[next_zone] = occupied.get(next_zone, 0) + 1
                            turn_moves.append(f"{drone.id}-{next_zone}")
                        else:
                            # Restricted move: genuinely spans 2 turns, use transit tracking
                            drone.strat_transit(next_zone, connection, travel_time)
                            connection.move_at_turn(turn)
                            occupied[next_zone] = occupied.get(next_zone, 0) + 1
                        turn_moves.append(f"{drone.id}-{connection.name}")

            for drone in self.drones:
                if drone.is_in_transit:
                    frame[drone.id] = drone.transit_conn.name
                else:
                    frame[drone.id] = drone.current_zone

            self.frames.append(frame)

            # Phase 4: Finalize turn tracking (Always append to keep turn counts synchronized!)
            if turn_moves:
                turn_moves.sort(key=lambda x: int(x.split("-")[0][1:]))
                colored_moves: List[str] = []
                for move in turn_moves:
                    d_id, dest = move.split('-')
                    is_conn = '-' in dest
                    colored_moves.append(self.format_move(d_id, dest, is_conn))
                self.output.append(" ".join(colored_moves))
            else:
                # If no drones moved, we still record a blank line or empty state entry 
                # so that turn indexing aligns perfectly with connection tracking!
                self.output.append("")
            
            turn += 1

    def print_output(self) -> None:
        # Only print lines that actually contain movements, omitting stationary turns
        for line in self.output:
            if line.strip():
                print(line)

    def simulation(self) -> None:
        self.create_drones()
        self.assign_path()
        self.run()
        self.print_output()


from typing import Tuple, List, Dict
from hub import Hub
from conn import Connection
from graph import Graph
import math
import pygame
import sys


class Display:

    def __init__(self, graph: Graph, frames):
        pygame.init()
        pygame.display.set_caption("FLY-IN")
        self.font = pygame.font.Font(None, 15)
        self.frames = frames
        self.zones: List[Hub] = graph.zones
        self.conn: List[Connection] = graph.conn
        self.graph: Graph = graph
        self.running: bool = True
        self.WIDTH = 1800
        self.HEIFHT = 900
        self.end_delay = 1000
        self.scale = 0
        self.offset_x = 0
        self.offset_y = 0
        self.compute_layout()
        self.compute_visual_style()
        self.font = pygame.font.Font(None, self.font_size)
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIFHT))

        self.COLOR_MAP: Dict[str, Tuple[int, int, int]] = {

            # Standard ANSI equivalents
            "black": (0, 0, 0),
            "red": (205, 0, 0),
            "green": (0, 205, 0),
            "yellow": (205, 205, 0),
            "blue": (0, 0, 238),
            "magenta": (205, 0, 205),
            "cyan": (0, 205, 205),
            "white": (229, 229, 229),

            # Bright ANSI equivalents
            "gray": (127, 127, 127),
            "light_red": (255, 0, 0),
            "light_green": (0, 255, 0),
            "light_yellow": (255, 255, 0),
            "light_blue": (92, 92, 255),
            "light_magenta": (255, 0, 255),
            "light_cyan": (0, 255, 255),

            "orange": (255, 135, 0),
            "purple": (175, 0, 255),
            "brown": (135, 95, 0),
            "maroon": (95, 0, 0),
            "gold": (255, 215, 0),
            "darkred": (135, 0, 0),
            "crimson": (215, 0, 0),
            "violet": (215, 135, 255),

            # Common extras
            "pink": (255, 135, 255),
            "navy": (0, 0, 135),
            "teal": (0, 135, 135),
            "lime": (95, 255, 0),
            "olive": (135, 135, 0),
            "turquoise": (0, 215, 215),
            "indigo": (95, 0, 175),
            "coral": (255, 135, 95),
            "salmon": (255, 175, 135),
            "beige": (255, 255, 215),
            "silver": (188, 188, 188),
            "aqua": (0, 255, 255),

            "rainbow": (0, 255, 255)}

        self.default_color = (255, 255, 255)  # White

    def compute_layout(self) -> None:
        # create bounding box
        xs = [zone.x for zone in self.zones]
        ys = [zone.y for zone in self.zones]

        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        # the width and height of bounding box
        span_x = max(max_x - min_x, 1)
        span_y = max(max_y - min_y, 1)

        # pixels per graph-unit
        padding = 100
        scale_x = (self.WIDTH - 2 * padding) / span_x
        scale_y = (self.HEIFHT - 2 * padding) / span_y
        self.scale = min(scale_x, scale_y)

        # Center of the bounding box in graph-space
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2

        # Center of the window in screen-space
        window_center_x = self.WIDTH / 2
        window_center_y = self.HEIFHT / 2

        self.offset_x = window_center_x - (center_x * self.scale)
        self.offset_y = window_center_y + (center_y * self.scale)

    def compute_visual_style(self) -> None:
        self.zone_radius = max(10, min(40, int(self.scale * 0.28)))
        self.drone_radius = max(6, min(20, int(self.zone_radius * 0.55)))
        self.line_width = max(1, min(5, int(self.zone_radius * 0.16)))
        self.font_size = max(10, min(18, int(self.zone_radius * 0.75)))
        self.show_zone_labels = (len(self.zones) <= 25 and
                                 self.zone_radius >= 14)

    def screen_position(self, x: float, y: float) -> Tuple[int, int]:
        screen_x = self.offset_x + (x * self.scale)
        screen_y = self.offset_y - (y * self.scale)
        return (int(screen_x), int(screen_y))

    def draw_connection(self):
        for connection in self.conn:
            source = connection.source
            target = connection.target

            src_hub = self.graph.zone_lookup[source]
            trg_hub = self.graph.zone_lookup[target]

            start = self.screen_position(src_hub.x, src_hub.y)
            end = self.screen_position(trg_hub.x, trg_hub.y)

            color = self.COLOR_MAP['teal']

            pygame.draw.line(self.screen, color, start, end,
                             width=self.line_width)

    def draw_zones(self):
        for zone in self.zones:
            name = zone.name
            pos = self.screen_position(zone.x, zone.y)
            color_key = (zone.color.lower()
                         if zone.color is not None else 'white')
            color = self.COLOR_MAP.get(color_key, self.default_color)
            pygame.draw.circle(self.screen, color, pos, self.zone_radius)
            pygame.draw.circle(self.screen, (0, 0, 0), pos,
                               self.zone_radius, 1)
            if self.show_zone_labels:
                label = self.font.render(name, True, (0, 0, 0))
                rect = label.get_rect(center=pos)
                self.screen.blit(label, rect)

    def draw_drones(self, frame) -> None:
        occupied_positions: Dict[Tuple[int, int], int] = {}
        for drone_id, zone in frame.items():
            if zone in self.graph.zone_lookup:
                hub = self.graph.zone_lookup[zone]
                x, y = hub.x, hub.y
                pos = self.screen_position(x, y)
            else:
                loc = [(conn.source, conn.target)
                       for conn in self.conn if conn.name == zone]
                src, trg = loc[0]

                x1, y1 = (self.graph.zone_lookup[src].x,
                          self.graph.zone_lookup[src].y)
                x2, y2 = (self.graph.zone_lookup[trg].x,
                          self.graph.zone_lookup[trg].y)

                x = (x1 + x2) / 2
                y = (y1 + y2) / 2

                pos = self.screen_position(x, y)

            stack_index = occupied_positions.get(pos, 0)
            occupied_positions[pos] = stack_index + 1
            if stack_index > 0:
                angle = stack_index * 2 * math.pi / 8
                spread = self.drone_radius * 1.2
                pos = (
                    int(pos[0] + math.cos(angle) * spread),
                    int(pos[1] + math.sin(angle) * spread)
                )

            pygame.draw.circle(self.screen, (255, 255, 215), pos,
                               self.drone_radius)
            pygame.draw.circle(self.screen, (0, 0, 0), pos,
                               self.drone_radius, 2)

            label = self.font.render(drone_id, True, (0, 0, 0))
            rect = label.get_rect(center=pos)
            self.screen.blit(label, rect)

    def _draw(self) -> None:
        try:
            background = pygame.image.load('map.webp')
            background = pygame.transform.scale(background,
                                                (self.WIDTH, self.HEIFHT))

            # Create time obj to control FPS
            clock = pygame.time.Clock()

            # get the time in ms from the pygame.init()
            last_update: int = pygame.time.get_ticks()

            fram_index: int = 0
            finished_at: int | None = None

            while self.running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False

                now = pygame.time.get_ticks()
                if (now - last_update >= self.end_delay and
                        fram_index < len(self.frames) - 1):
                    fram_index += 1
                    last_update = now
                    if fram_index == len(self.frames) - 1:
                        finished_at = now

                if (finished_at is not None and
                        now - finished_at >= self.end_delay):
                    self.running = False
                    continue

                self.screen.blit(background, (0, 0))

                self.draw_connection()
                self.draw_zones()

                if self.frames:
                    self.draw_drones(self.frames[fram_index])

                pygame.display.flip()
                clock.tick(60)

            pygame.quit()
        except KeyboardInterrupt:
            sys.exit()

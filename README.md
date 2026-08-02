*This project has been created as part of the 42 curriculum by hmezrari.*

# fly-in

## Description

**fly-in** is a drone delivery simulation engine. Given a map made up of
**hubs** (zones) connected by **links**, the goal is to route a fleet of
drones from a start hub to an end hub as efficiently as possible, while
respecting real-world-style constraints:

- Each hub has a maximum drone capacity (`max_drones`) — it can only hold
  so many drones at once.
- Each connection between two hubs has its own throughput limit
  (`max_link_capacity`).
- Some hubs are marked as `restricted` zones, which take longer to enter
  (an extra turn of "transit" time instead of an instant move).

The project is split into three main concerns:

1. **Modeling the map** — parsing the input map into a `Graph` of `Hub`
   and `Connection` objects, with an adjacency list for fast lookups.
2. **Pathfinding** — computing not just *the* shortest path from start to
   end, but several good alternative paths, so traffic can be spread
   across the network instead of bottlenecking a single route.
3. **Simulating traffic** — running a turn-by-turn simulation where every
   drone advances along its assigned path, one hop at a time, respecting
   hub capacity and connection limits, until every drone has reached the
   destination.

The end goal is to answer: *given this map and this many drones, how many
turns does it take to deliver all of them, and what does that traffic
flow look like?*

## Instructions

### Requirements

- Python 3
- Dependencies listed in `requirements.txt`

### Installation

```bash
make install
```

This installs all required Python dependencies via `pip`.

### Running the project

```bash
make run
```

This runs the simulation using the default map defined in the
`Makefile` (`MAP = maps/medium/01_dead_end_trap.txt`). To run a
different map, override the `MAP` variable on the command line:

```bash
make run MAP=maps/easy/some_other_map.txt
```

### Other available commands

- `make debug` — runs the project under the Python debugger.
- `make lint` — runs `flake8` and `mypy` (with a relaxed, permissive
  configuration) over the codebase.
- `make lint-strict` — runs `flake8` and `mypy --strict` for a fully
  strict type-checking pass.
- `make clean` — removes `__pycache__` and `.mypy_cache` directories.

### Input format

Maps are plain text files under `maps/`, organized by difficulty
(`easy`, `medium`, `hard`, ...). Each map is a simple line-based format,
for example:

```
# Medium Level 1: Dead end trap - drones might get stuck
nb_drones: 5

start_hub: start 0 0 [color=green]
hub: junction 1 0 [color=yellow max_drones=2]
hub: dead_end 1 1 [color=red]
hub: correct_path 2 0 [color=blue]
hub: intermediate 3 0 [color=blue]
end_hub: goal 4 0 [color=green]

connection: start-junction [max_link_capacity=2]
connection: junction-dead_end
connection: junction-correct_path
connection: correct_path-intermediate
connection: intermediate-goal
```

- Lines starting with `#` are comments and are ignored.
- `nb_drones: <n>` sets how many drones will be simulated.
- Hubs are declared one per line as `<type>: <name> <x> <y> [options]`:
  - `<type>` is one of `hub`, `start_hub`, or `end_hub` — there must be
    exactly one `start_hub` and one `end_hub` per map.
  - `<name>` is the hub's unique identifier.
  - `<x> <y>` are its coordinates (used for layout/positioning).
  - Bracketed options configure the hub's metadata: `color=<name>` sets
    its display color, and `max_drones=<n>` sets its capacity (if
    omitted, a default capacity is used). A hub can also be marked
    `restricted`, which adds an extra turn of transit time for drones
    entering it.
- Connections are declared as `connection: <hub1>-<hub2> [options]`,
  linking two hubs bidirectionally. `max_link_capacity=<n>` optionally
  limits how many drones can use that connection per turn (if omitted,
  a default is used).

### Output

While running, the simulation prints one line per turn listing every
drone move that occurred that turn, using colored labels for readability
(see **Visual Representation** below). At the end, it reports the total
number of turns needed to deliver every drone.

## Algorithm Choices & Implementation Strategy

### Graph modeling

The map is parsed into a `Graph`, holding:
- A list of `Hub` objects (`zones`) and a `zone_lookup` dict for O(1)
  access by name.
- A list of `Connection` objects (`conn`), each linking two hubs and
  carrying its own throughput/capacity limits.
- An `adjacency` dict mapping each hub name to a list of
  `(neighbor_name, Connection)` tuples, built bidirectionally so both
  ends of a connection can find each other. This adjacency list is the
  structure every pathfinding and simulation step relies on.

### Pathfinding: Dijkstra + Yen's K-Shortest Paths

Rather than sending every drone down a single "best" route (which would
quickly bottleneck at hub capacity limits), the project computes **several**
good alternative routes and distributes drones across them:

- A **Dijkstra** implementation finds the single cheapest path between
  the start and end hub, using each hub's own movement cost.
- **Yen's algorithm** is then layered on top of Dijkstra to generate up
  to `K` alternative paths. It works by, for each already-found path,
  trying every possible "spur node" along it: temporarily removing the
  edges/nodes already explored from that point, then re-running Dijkstra
  from the spur node onward. This produces genuinely different candidate
  routes rather than trivial variations of the same path.
- Candidates are filtered by a cost ceiling (a multiple of the true
  shortest path's cost) so wildly inefficient detours are discarded, and
  ranked by how close their cost is to the optimal path's cost, so the
  most efficient alternatives are preferred first.

This gives a ranked list of `K` distinct, reasonably efficient paths,
which are then handed off to the simulation and distributed cyclically
across all drones — spreading traffic instead of funneling every drone
through one congested corridor.

### Turn-based simulation

The `Simulation` class drives the actual delivery process, one discrete
turn at a time, until every drone reports as delivered. Each turn is
broken into ordered phases:

1. **Land mid-flight drones** — any drone currently in transit (crossing
   into a `restricted` zone, which takes an extra turn) has its transit
   timer ticked down; drones whose timer reaches zero land this turn.
2. **Snapshot occupancy** — a fresh count of how many drones currently
   occupy each hub is computed, used to enforce capacity limits for the
   rest of the turn.
3. **Move resting drones** — drones not already mid-flight are processed
   in order of how far along their path they already are (furthest
   first), so drones closer to completion get priority over hub capacity
   and connection availability. A move is only allowed if: a connection
   exists between the drone's current and next hub, that connection
   still allows movement this turn, and the destination hub has room.
   Entering a normal hub resolves instantly; entering a `restricted` hub
   instead starts a one-turn transit period.
4. **Advance the turn counter** and repeat until every drone is
   delivered.

This turn/phase structure keeps drone movement deterministic and fair:
drones are never allowed to overfill a hub, and priority is always given
to whichever drones are closest to finishing, to keep the overall
delivery time as short as possible.

## Visual Representation

To make the simulation's behavior easy to follow at a glance, each
printed turn is rendered as a line of colored `drone-destination` pairs
in the terminal, using ANSI escape codes:

- Each **drone ID** is shown in a consistent accent color, so the same
  drone is easy to track visually across turns.
- Each **destination hub** is colored according to that hub's own color,
  as defined in the map data — so hubs belonging to the same zone/area
  are visually grouped, and it's immediately obvious which region of the
  map a drone is moving through without cross-referencing the raw map
  file.

This turns a wall of turn-by-turn text into something that's much faster
to scan: you can follow a specific drone's journey by color, spot which
hubs are busiest by how often their color appears, and see at a glance
whether traffic is well spread across the network or bottlenecked in one
area — all without needing a separate graphical tool.

## Resources

### Classic references

- [Dijkstra's algorithm — Wikipedia](https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm)
    (https://www.geeksforgeeks.org/dsa/dijkstras-shortest-path-algorithm-greedy-algo-7/)
- [Yen's algorithm — Wikipedia](https://en.wikipedia.org/wiki/Yen%27s_algorithm)
    (https://dev.to/whoakarsh/finding-the-k-shortest-paths-using-yens-algorithm-in-python-1gka)
- [pygane] (https://pypi.org/project/pygame/)

### AI usage

- Understanding the algorithms:
    explaining how Dijkstra's algorithm and Yen's K-Shortest Paths algorithm work, to fully understand their logic before implementing them.
- Test maps:
    generating different sample maps used to test the program against a variety of scenarios (e.g. capacity bottlenecks, restricted zones, dead ends).
import sys
from parsing import Parser
from graph import Graph
from yens import Yen
from simulation import Simulation
from display import Display


def build_graph(mape_file: dict) -> Graph:
    graph = Graph()
    graph.create_zone(mape_file)
    graph.create_conn(mape_file)
    return graph


def select_working_paths(mape_file, graph_builder, paths):
    """Try increasing numbers of candidate paths; keep the subset that
    completes in the fewest turns without deadlocking.

    Each candidate is tested using a lightweight simulation run (no
    frame recording, no colored output string building) so that testing
    all K candidates stays cheap even with a large number of drones —
    only the real, final simulation records full frames/output.
    """
    if not paths:
        return paths

    def count_turns(candidate_paths):
        test_graph = graph_builder()
        test_sim = Simulation(test_graph, candidate_paths, lightweight=True)
        test_sim.create_drones()
        test_sim.assign_path()
        try:
            test_sim.run()
        except RuntimeError:
            return float('inf')
        return test_sim.total_turns

    best_paths = paths[:1]
    best_turns = count_turns(best_paths)

    for path_count in range(2, len(paths) + 1):
        candidate_paths = paths[:path_count]
        candidate_turns = count_turns(candidate_paths)
        if candidate_turns == float('inf'):
            continue
        if candidate_turns <= best_turns:
            best_paths = candidate_paths
            best_turns = candidate_turns

    return best_paths


def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <map_file.txt>")
        return

    # 1. Parsing
    parser = Parser(sys.argv[1])
    mape_file = parser.check_input_file()

    # 2. Build Graph
    graph = build_graph(mape_file)

    # 3. Yen's K-Shortest Paths (runs Dijkstra internally)
    yen = Yen(graph)
    paths = yen.find_shortets_paths()
    paths = select_working_paths(mape_file, lambda: build_graph(mape_file), paths)

    # 4. Run Simulation (always records frames, for any number of drones)
    sim = Simulation(graph, paths)
    sim.simulation()

    # 5. Render Pygame Display
    disp = Display(graph, sim.frames)
    disp._draw()


if __name__ == "__main__":
    main()
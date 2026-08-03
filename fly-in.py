import sys
from typing import Callable, List
from parsing import Parser
from graph import Graph
from yens import Yen
from simulation import Simulation
from display import Display


class Main:

    def __init__(self) -> None:
        parser = Parser(sys.argv[1])
        self.map_file = parser.check_input_file()

    def build_graph(self) -> Graph:
        graph = Graph()
        graph.create_zone(self.map_file)
        graph.create_conn(self.map_file)
        return graph

    def select_working_paths(
        self,
        graph_builder: Callable[[], Graph],
        paths: List[List[str]],
    ) -> List[List[str]]:
        """Picks the subset of candidate paths (from Yen's algorithm)
        that delivers all drones fastest.

        Tries using just the best path, then the best two, then three,
        and so on, running a throwaway simulation for each candidate
        set. Candidates are tested with a small turn cap so an
        obviously bad combination (e.g. every drone squeezed onto one
        path) is rejected quickly instead of running to completion.
        """
        if not paths:
            return paths

        def count_turns(candidate_paths: List[List[str]]) -> float:
            test_graph = graph_builder()
            test_sim = Simulation(test_graph, candidate_paths)
            test_sim.create_drones()
            test_sim.assign_path()
            try:
                test_sim.run(max_turns=200)
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

    def main(self) -> None:
        if len(sys.argv) > 2:
            raise OSError("Error: Usage: python main.py <map_file.txt>")
            return

        # 2. Build Graph
        graph = self.build_graph()

        # 3. Yen's K-Shortest Paths
        yen = Yen(graph)
        paths = yen.find_shortets_paths()
        paths = self.select_working_paths(lambda: self.build_graph(), paths)

        # 4. Run Simulation (real run: no cap, runs to true completion)
        sim = Simulation(graph, paths)
        sim.simulation()

        # 5. Pygame Display
        disp = Display(graph, sim.frames)
        disp._draw()


if __name__ == "__main__":
    try:
        main = Main()
        main.main()
    except Exception as e:
        print(e)

from typing import Dict, Any
import sys
from parsing import Parser
from graph import Graph
from yens import Yen
from simulation import Simulation
from display import Display


class Main:

    def __init__(self):
        parser = Parser(sys.argv[1])
        self.map_file = parser.check_input_file()

    def build_graph(self) -> Graph:
        graph = Graph()
        graph.create_zone(self.map_file)
        graph.create_conn(self.map_file)
        return graph


    def select_working_paths(self, graph_builder, paths):
        if not paths:
            return paths

        def count_turns(candidate_paths):
            test_graph = graph_builder()
            test_sim = Simulation(test_graph, candidate_paths)
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


    def main(self):
        if len(sys.argv) < 2:
            print("Usage: python main.py <map_file.txt>")
            return

        # 2. Build Graph
        graph = self.build_graph()
    
        # 3. Yen's K-Shortest Paths 
        yen = Yen(graph)
        paths = yen.find_shortets_paths()
        paths = self.select_working_paths(lambda: self.build_graph(), paths)
    
        # 4. Run Simulation
        sim = Simulation(graph, paths)
        sim.simulation()
    
        # 5. Pygame Display
        disp = Display(graph, sim.frames)
        disp._draw()


if __name__ == "__main__":
    main = Main()
    main.main()
from parsing import Parser
from yens import Yen
from graph import Graph
from simulation import Simulation
from display import Display
import sys


def build_graph(mape_file):
    graph = Graph()
    graph.create_zone(mape_file)
    graph.create_conn(mape_file)
    return graph


def count_turns(mape_file, paths):
    graph = build_graph(mape_file)
    simulation = Simulation(mape_file['nb_drones'], graph, paths)
    simulation.create_drones()
    simulation.assign_path()
    try:
        simulation.run()
    except RuntimeError:
        return float('inf')
    return len([line for line in simulation.output if line.strip()])


def select_fastest_paths(mape_file, paths):
    if not paths:
        return paths

    best_paths = paths[:1]
    best_turns = count_turns(mape_file, best_paths)

    for path_count in range(2, len(paths) + 1):
        candidate_paths = paths[:path_count]
        candidate_turns = count_turns(mape_file, candidate_paths)
        if candidate_turns < best_turns:
            best_paths = candidate_paths
            best_turns = candidate_turns

    return best_paths


# try:
    #    --------check mape file--------------
parser = Parser(sys.argv[1])
mape_file = parser.check_input_file()
# ----------------Validate--------------------
graph = build_graph(mape_file)
# -----------------Algo----------------------
yen = Yen(graph)
paths = yen.find_shortets_paths()
paths = select_fastest_paths(mape_file, paths)
#----------------simulation-------------------
simulation = Simulation(mape_file['nb_drones'], graph, paths)
simulation.simulation()
#print(simulation.frames)
# ________________________________Display__________________________________
disp = Display(graph, simulation.frames)
disp._draw()

# except Exception as e:
#     print(e)

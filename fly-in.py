from parsing import Parser
from yens import Yen
from graph import Graph
from simulation import Simulation
from display import Display
import sys


# try:
#    --------check mape file--------------
parser = Parser(sys.argv[1])
mape_file = parser.check_input_file()

# ----------------Validate--------------------
graph = Graph()
graph.create_zone(mape_file)
graph.create_conn(mape_file)

# -----------------Algo----------------------
yen = Yen(graph)
paths = yen.find_shortets_paths()
print(paths)

#----------------simulation-------------------
simulation = Simulation(mape_file['nb_drones'], graph, paths)
simulation.simulation()

#print(simulation.frames)
# ________________________________Display__________________________________
disp = Display(graph, simulation.frames)
disp._draw()

# except Exception as e:
#     print(e)

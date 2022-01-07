from amplpy import AMPL, Environment
import sys

file_name, ampl_path, input_file_path = sys.argv

if len(sys.argv) < 3:
    sys.exit()

# Create an AMPL instance
ampl = AMPL(Environment(ampl_path))

# Interpret the two files
ampl.read('minimart_sol.mod')
ampl.read_data(input_file_path)

# Save parameters from the input file
n = int(ampl.get_parameter('n').value())  # number of villages
coordX = ampl.get_parameter('Cx').get_values().toDict()  # village coord x
coordY = ampl.get_parameter('Cy').get_values().toDict()  # village coord y
usable = ampl.get_parameter('usable').get_values().toDict()  # village i can be used to build a store
dc = ampl.get_parameter('Dc').get_values().toDict()  # cost to build a store in village i
rng = int(ampl.get_parameter('range').value())  # max range
distances = ampl.get_parameter('distance').get_values().to_dict()  # distances from i to j
vc = ampl.get_parameter('Vc').value()  # driving cost per kilometer
fc = ampl.get_parameter('Fc').value()  # fixed fee for each driver
capacity = int(ampl.get_parameter('capacity').value())  # capacity of each truck

# Solve the store locations installation problem
ampl.set_option('solver', ampl_path + "/cplex")
ampl.solve()

building_costs = ampl.get_objective('cost').value()

y = ampl.get_variable('y').get_values().toDict()
ampl.close()

# Installed stores coordinates
storesCoords = dict()

for i in range(1, len(y) + 1):
    if y.get(i) == 1:
        storesCoords.update({i: (coordX.get(i), coordY.get(i))})


# Plot the region: see the print.txt file

# Refurbishing Routes Problem
def compute_savings():
    stores_indxs = storesCoords.keys()
    savings = [(distances.get((1, i)) + distances.get((1, j)) - distances.get((i, j)), i, j) for i in stores_indxs for j
               in stores_indxs if i != j and i > j]
    savings.sort(reverse=True)
    return savings


savings = compute_savings()

routes = [[1, i, 1] for i in storesCoords.keys() if i > 1]


def find_routes_passing_through(s1, s2):
    r1 = None
    r2 = None
    for route in routes:
        if r1 is not None and r2 is not None:
            break
        if route[1] == s1:
            route.reverse()
            r1 = route
            continue
        elif route[-2] == s1:
            r1 = route
            continue
        if route[1] == s2:
            r2 = route
            continue
        elif route[-2] == s2:
            route.reverse()
            r2 = route
            continue
    return r1, r2


def merge_routes(r1, s1, r2):
    r1_c = list(r1)
    r2_c = list(r2)
    del r1_c[-2:]
    del r2_c[:2]
    return r1_c + s1 + r2_c


def clarke_wright():
    while len(savings) > 0:
        curr_saving = savings.pop(0)
        r1, r2 = find_routes_passing_through(curr_saving[1], curr_saving[2])
        if r1 is not None and r2 is not None:
            new_route = merge_routes(r1, [curr_saving[1], curr_saving[2]], r2)
            if len(new_route) - 2 <= capacity:  # excluding the store at location 1 (depot)
                routes.remove(r1)
                routes.remove(r2)
                routes.insert(0, new_route)


clarke_wright()

# Plot the routes: see the print.txt file

# Final cost
total_km = 0
for route in routes:
    for i, j in zip(route, route[1:]):
        total_km = total_km + distances.get((i, j))

driving_costs = total_km * vc
driving_fees = len(routes) * fc

total_refurbishing_costs = driving_costs + driving_fees
total_costs = total_refurbishing_costs + building_costs

print(total_costs)
print(building_costs)
print(total_refurbishing_costs)
print(*storesCoords, sep=",")
for route in routes:
    print(*route, sep=",")

from amplpy import AMPL, Environment
import sys, os

file_name, ampl_path, input_file_path = sys.argv
ampl_model_filename = 'minimart_sol.mod'
output_separator = "-----"

# Disable printing
def blockPrint():
    sys.stdout = open(os.devnull, 'w')

# Restore printing
def enablePrint():
    sys.stdout = sys.__stdout__


def solve_stores_installation_problem():
    # Create an AMPL instance
    ampl = AMPL(Environment(ampl_path))

    # Interpret the two files
    ampl.read(ampl_model_filename)
    ampl.read_data(input_file_path)

    # Save parameters from the input file
    n = int(ampl.get_parameter('n').value())  # number of villages
    coordX = ampl.get_parameter('Cx').get_values().toDict()  # village coord x
    coordY = ampl.get_parameter('Cy').get_values().toDict()  # village coord y
    usable = ampl.get_parameter('usable').get_values().toDict()  # village i can be used to build a store
    dc = ampl.get_parameter('Dc').get_values().toDict()  # cost to build a store in village i
    rng = int(ampl.get_parameter('range').value())  # max range
    global distances
    distances = ampl.get_parameter('distance').get_values().to_dict()  # distances from i to j

    global vc, fc
    vc = ampl.get_parameter('Vc').value()  # driving cost per kilometer
    fc = ampl.get_parameter('Fc').value()  # fixed fee for each driver

    global capacity
    capacity = int(ampl.get_parameter('capacity').value())  # capacity of each truck

    # Solve the store locations installation problem
    ampl.set_option('solver', ampl_path + "/cplex")

    blockPrint()
    ampl.solve()
    enablePrint()

    building_costs = ampl.get_objective('cost').value()

    y = ampl.get_variable('y').get_values().toDict()
    ampl.close()

    # Installed stores coordinates
    stores_coords = dict()
    for i in range(1, len(y) + 1):
        if y.get(i) == 1:
            stores_coords.update({i: (coordX.get(i), coordY.get(i))})

    return stores_coords, building_costs


# Refurbishing Routes Problem
def compute_savings(stores_coords):
    # computing the cost for driving from i to j
    driving_cost = dict()
    for d in distances.keys():
        driving_cost.update({d: distances.get(d) * vc})  # dist * vc
        if d[0] == 1:  # if is an arch starting from the depot, a new route is created and a driver fee is applied
            driving_cost.update({d: distances.get(d) + fc})

    # compute saving(i,j) = d_cost(1,j) + d_cost(1,j) - d_cost(i,j) for each i,j in stores
    stores_indxs = stores_coords.keys()
    savings = [(driving_cost.get((1, i)) + driving_cost.get((1, j)) - driving_cost.get((i, j)), i, j)
               for i in stores_indxs
               for j in stores_indxs
               if i != j and i > j]

    savings.sort(reverse=True)  # first step of Best() function
    return driving_cost, savings


def find_routes_passing_through(s1, s2, routes):
    # if there exists, return two routes that pass from s1 and s2, that needs to be adjacent to the depot
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


def Best(savings):
    return savings.pop(0)


def Ind(routes, curr_saving):
    r1, r2 = find_routes_passing_through(curr_saving[1], curr_saving[2], routes)
    if r1 is not None and r2 is not None:
        new_route = merge_routes(r1, [curr_saving[1], curr_saving[2]], r2)
        if len(new_route) - 2 <= capacity:  # excluding the store at location 1 (depot)
            return True, r1, r2, new_route
    return False, None, None, None


def savings_algorithm(savings, routes):
    while len(savings) > 0:
        curr_saving = Best(savings)
        can_be_merged, r1, r2, new_route = Ind(routes, curr_saving)
        if can_be_merged:
            routes.remove(r1)
            routes.remove(r2)
            routes.insert(0, new_route)


def solve_refurbishing_routing_problem(store_coords):
    driving_cost, savings = compute_savings(store_coords)
    routes = [[1, i, 1] for i in store_coords.keys() if i > 1]
    savings_algorithm(savings, routes)
    return routes, driving_cost


def print_results(stores_coords, routes, driving_cost):
    # computing total costs
    driving_costs = 0
    for route in routes:
        for i, j in zip(route, route[1:]):
            driving_costs = driving_costs + driving_cost.get((i, j))

    total_costs = building_costs + driving_costs

    print(total_costs)
    print(building_costs)
    print(driving_costs)
    print(*stores_coords, sep=",")
    for route in routes:
        print(*route, sep=",")


stores_coords, building_costs = solve_stores_installation_problem()
routes, driving_cost = solve_refurbishing_routing_problem(stores_coords)
print_results(stores_coords, routes, driving_cost)

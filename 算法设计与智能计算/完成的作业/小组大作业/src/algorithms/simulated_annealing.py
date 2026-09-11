import math
import random

from route_common import evaluate_route, nearest_neighbor_route, nearest_neighbor_route_with_delay, route_cost


DEFAULT_PARAMS = {
    "initial_temp": 10.0,
    "final_temp": 1e-4,
    "alpha": 0.95,
    "inner_iter": 100,
    "seed": 42,
}


def neighbor(route, rng):
    if len(route) <= 3:
        return route[:]

    candidate = route[:]
    i, j = sorted(rng.sample(range(1, len(candidate)), 2))
    if rng.choice(["swap", "reverse"]) == "swap":
        candidate[i], candidate[j] = candidate[j], candidate[i]
    else:
        candidate[i:j + 1] = reversed(candidate[i:j + 1])
    return candidate


def objective(route, cost_matrix, return_to_start, path_matrix=None, node_delay=None, nodes=None):
    if path_matrix is not None and node_delay is not None and nodes is not None:
        return evaluate_route(route, cost_matrix, path_matrix, node_delay, nodes, return_to_start)["total_time"]
    return route_cost(route, cost_matrix, return_to_start)


def solve(start, points, cost_matrix, return_to_start=False, **kwargs):
    params = {**DEFAULT_PARAMS, **{key: value for key, value in kwargs.items() if key in DEFAULT_PARAMS}}
    rng = random.Random(params["seed"])
    path_matrix = kwargs.get("path_matrix")
    node_delay = kwargs.get("node_delay")
    nodes = kwargs.get("nodes")

    if not points:
        return {
            "algorithm": "simulated_annealing",
            "route": [start],
            "drive_time": 0.0,
            "history": [],
        }

    if path_matrix is not None and node_delay is not None:
        current_route = nearest_neighbor_route_with_delay(start, points, cost_matrix, path_matrix, node_delay)
    else:
        current_route = nearest_neighbor_route(start, points, cost_matrix)
    current_cost = objective(current_route, cost_matrix, return_to_start, path_matrix, node_delay, nodes)
    best_route = current_route[:]
    best_cost = current_cost
    history = []

    iteration = 0
    temperature = params["initial_temp"]
    while temperature > params["final_temp"]:
        for _ in range(params["inner_iter"]):
            iteration += 1
            candidate_route = neighbor(current_route, rng)
            candidate_cost = objective(candidate_route, cost_matrix, return_to_start, path_matrix, node_delay, nodes)
            delta = candidate_cost - current_cost
            if delta < 0 or rng.random() < math.exp(-delta / temperature):
                current_route = candidate_route
                current_cost = candidate_cost
            if current_cost < best_cost:
                best_route = current_route[:]
                best_cost = current_cost
            history.append({
                "iteration": iteration,
                "current_cost": current_cost,
                "best_cost": best_cost,
                "temperature": temperature,
            })
        temperature *= params["alpha"]

    return {
        "algorithm": "simulated_annealing",
        "route": best_route,
        "drive_time": route_cost(best_route, cost_matrix, return_to_start),
        "history": history,
    }

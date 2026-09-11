import random

from route_common import (
    add_delay_nodes_from_segment,
    evaluate_route,
    route_cost,
    route_with_return,
    segment_total_cost,
)


DEFAULT_PARAMS = {
    "num_ants": 30,
    "num_iterations": 100,
    "alpha": 1.0,
    "beta": 3.0,
    "rho": 0.3,
    "q": 1.0,
    "seed": 42,
}


def initialize_pheromone(nodes):
    return {
        (from_id, to_id): 1.0
        for from_id in nodes
        for to_id in nodes
        if from_id != to_id
    }


def select_next(
    current,
    candidates,
    pheromone,
    cost_matrix,
    params,
    rng,
    path_matrix=None,
    node_delay=None,
    seen_delay_nodes=None,
):
    weights = []
    for candidate in candidates:
        cost = segment_total_cost(
            current,
            candidate,
            cost_matrix,
            path_matrix=path_matrix,
            node_delay=node_delay,
            seen_delay_nodes=seen_delay_nodes,
        )
        if cost == float("inf"):
            raise ValueError(f"{current}->{candidate} 不可达，无法构造蚁群路线。")
        eta = 1e6 if cost <= 0 else 1 / cost
        tau = pheromone[(current, candidate)]
        weights.append((candidate, (tau ** params["alpha"]) * (eta ** params["beta"])))

    total = sum(weight for _candidate, weight in weights)
    if total <= 0:
        return rng.choice(list(candidates))

    pick = rng.random() * total
    cumulative = 0.0
    for candidate, weight in weights:
        cumulative += weight
        if cumulative >= pick:
            return candidate
    return weights[-1][0]


def construct_route(start, points, pheromone, cost_matrix, params, rng, path_matrix=None, node_delay=None):
    route = [start]
    current = start
    unvisited = set(points)
    seen_delay_nodes = set()
    if node_delay is not None:
        add_delay_nodes_from_segment([start], node_delay, seen_delay_nodes)

    while unvisited:
        next_point = select_next(
            current,
            unvisited,
            pheromone,
            cost_matrix,
            params,
            rng,
            path_matrix=path_matrix,
            node_delay=node_delay,
            seen_delay_nodes=seen_delay_nodes,
        )
        if path_matrix is not None and node_delay is not None:
            segment = path_matrix.get((current, next_point))
            if segment is None:
                raise KeyError(f"path matrix 缺少 {current}->{next_point} 的路径。")
            add_delay_nodes_from_segment(segment, node_delay, seen_delay_nodes)
        route.append(next_point)
        unvisited.remove(next_point)
        current = next_point
    return route


def objective(route, cost_matrix, return_to_start, path_matrix=None, node_delay=None, nodes=None):
    if path_matrix is not None and node_delay is not None and nodes is not None:
        return evaluate_route(route, cost_matrix, path_matrix, node_delay, nodes, return_to_start)["total_time"]
    return route_cost(route, cost_matrix, return_to_start)


def update_pheromone(pheromone, routes, return_to_start, params):
    for key in pheromone:
        pheromone[key] *= 1 - params["rho"]
    for route, score in routes:
        if score <= 0:
            continue
        amount = params["q"] / score
        actual_route = route_with_return(route, return_to_start)
        for from_id, to_id in zip(actual_route, actual_route[1:]):
            pheromone[(from_id, to_id)] += amount


def solve(start, points, cost_matrix, return_to_start=False, **kwargs):
    params = {**DEFAULT_PARAMS, **{key: value for key, value in kwargs.items() if key in DEFAULT_PARAMS}}
    rng = random.Random(params["seed"])
    path_matrix = kwargs.get("path_matrix")
    node_delay = kwargs.get("node_delay")
    nodes = kwargs.get("nodes")

    if not points:
        return {
            "algorithm": "ant_colony",
            "route": [start],
            "drive_time": 0.0,
            "history": [],
        }

    relevant_nodes = [start] + [point for point in points if point != start]
    pheromone = initialize_pheromone(relevant_nodes)
    best_route = None
    best_cost = float("inf")
    history = []

    for iteration in range(1, params["num_iterations"] + 1):
        ant_routes = []
        iteration_best = float("inf")
        for _ant in range(params["num_ants"]):
            route = construct_route(start, points, pheromone, cost_matrix, params, rng, path_matrix, node_delay)
            score = objective(route, cost_matrix, return_to_start, path_matrix, node_delay, nodes)
            ant_routes.append((route, score))
            iteration_best = min(iteration_best, score)
            if score < best_cost:
                best_route = route[:]
                best_cost = score
        update_pheromone(pheromone, ant_routes, return_to_start, params)
        history.append({
            "iteration": iteration,
            "iteration_best_cost": iteration_best,
            "best_cost": best_cost,
        })

    return {
        "algorithm": "ant_colony",
        "route": best_route,
        "drive_time": route_cost(best_route, cost_matrix, return_to_start),
        "history": history,
    }

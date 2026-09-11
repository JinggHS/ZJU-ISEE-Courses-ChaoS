from route_common import nearest_neighbor_route, nearest_neighbor_route_with_delay, route_cost


def solve(start, points, cost_matrix, return_to_start=False, **kwargs):
    path_matrix = kwargs.get("path_matrix")
    node_delay = kwargs.get("node_delay")
    if path_matrix is not None and node_delay is not None:
        route = nearest_neighbor_route_with_delay(start, points, cost_matrix, path_matrix, node_delay)
    else:
        route = nearest_neighbor_route(start, points, cost_matrix)
    return {
        "algorithm": "greedy",
        "route": route,
        "drive_time": route_cost(route, cost_matrix, return_to_start),
        "history": [],
    }

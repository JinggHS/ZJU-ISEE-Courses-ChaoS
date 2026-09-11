import math

from route_common import lookup_cost, route_cost


DEFAULT_MAX_POINTS = 12


def solve(start, points, cost_matrix, return_to_start=False, **kwargs):
    path_matrix = kwargs.get("path_matrix")
    node_delay = kwargs.get("node_delay") or {}
    max_points = int(kwargs.get("max_points", DEFAULT_MAX_POINTS))

    points = unique_points(start, points)
    if len(points) > max_points:
        raise ValueError(
            f"exact_dp 只用于小规模最优解对照，当前配送点数量 {len(points)} "
            f"超过限制 {max_points}。"
        )

    if not points:
        return {
            "algorithm": "exact_dp",
            "route": [start],
            "drive_time": 0.0,
            "history": [],
            "checked_routes": 1,
            "checked_states": 1,
            "checked_transitions": 0,
        }

    special_nodes, special_index, delay_values = build_delay_index(node_delay)
    initial_delay_mask = node_delay_mask([start], special_index)
    initial_delay_cost = delay_cost(initial_delay_mask, delay_values)

    dp = {(0, -1, initial_delay_mask): initial_delay_cost}
    parent = {}
    transition_count = 0
    full_visit_mask = (1 << len(points)) - 1

    for _depth in range(len(points)):
        next_dp = {}
        for state, current_cost in dp.items():
            visited_mask, last_index, delay_mask = state
            current_node = start if last_index == -1 else points[last_index]
            for point_index, point in enumerate(points):
                if visited_mask & (1 << point_index):
                    continue
                transition_count += 1
                segment_mask = segment_delay_mask(current_node, point, path_matrix, special_index)
                new_delay_mask = delay_mask | segment_mask
                extra_delay = delay_cost(segment_mask & ~delay_mask, delay_values)
                new_state = (
                    visited_mask | (1 << point_index),
                    point_index,
                    new_delay_mask,
                )
                new_cost = current_cost + lookup_cost(cost_matrix, current_node, point) + extra_delay
                if new_cost < next_dp.get(new_state, math.inf):
                    next_dp[new_state] = new_cost
                    parent[new_state] = state
        dp = next_dp

    best_state = None
    best_cost = math.inf
    for state, current_cost in dp.items():
        visited_mask, last_index, delay_mask = state
        if visited_mask != full_visit_mask:
            continue
        total_cost = current_cost
        if return_to_start:
            current_node = points[last_index]
            segment_mask = segment_delay_mask(current_node, start, path_matrix, special_index)
            total_cost += lookup_cost(cost_matrix, current_node, start)
            total_cost += delay_cost(segment_mask & ~delay_mask, delay_values)
        if total_cost < best_cost:
            best_cost = total_cost
            best_state = state

    route = reconstruct_route(start, points, best_state, parent)
    return {
        "algorithm": "exact_dp",
        "route": route,
        "drive_time": route_cost(route, cost_matrix, return_to_start),
        "history": [],
        "checked_routes": math.factorial(len(points)),
        "checked_states": len(parent) + 1,
        "checked_transitions": transition_count,
    }


def unique_points(start, points):
    result = []
    seen = set()
    for point in points:
        if point == start or point in seen:
            continue
        seen.add(point)
        result.append(point)
    return result


def build_delay_index(node_delay):
    special_nodes = sorted(node_delay)
    special_index = {node_id: index for index, node_id in enumerate(special_nodes)}
    delay_values = [float(node_delay[node_id].get("delay_min", 0.0)) for node_id in special_nodes]
    return special_nodes, special_index, delay_values


def node_delay_mask(nodes, special_index):
    mask = 0
    for node_id in nodes:
        if node_id in special_index:
            mask |= 1 << special_index[node_id]
    return mask


def segment_delay_mask(from_id, to_id, path_matrix, special_index):
    if path_matrix is None:
        return 0
    segment = path_matrix.get((from_id, to_id))
    if segment is None:
        raise KeyError(f"path matrix 缺少 {from_id}->{to_id} 的路径。")
    return node_delay_mask(segment, special_index)


def delay_cost(mask, delay_values):
    total = 0.0
    index = 0
    while mask:
        if mask & 1:
            total += delay_values[index]
        mask >>= 1
        index += 1
    return total


def reconstruct_route(start, points, state, parent):
    if state is None:
        raise RuntimeError("exact_dp 未找到可行路线。")
    order = []
    current = state
    while current[1] != -1:
        order.append(points[current[1]])
        current = parent[current]
    order.reverse()
    return [start, *order]


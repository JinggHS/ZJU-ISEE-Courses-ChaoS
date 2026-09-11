import csv
import json
import math
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
RESULTS_DIR = ROOT_DIR / "results"

NODES_PATH = DATA_DIR / "nodes.csv"
DELIVERY_TASK_PATH = DATA_DIR / "delivery_task.json"
NODE_DELAY_PATH = DATA_DIR / "node_delay.json"
CONTEXT_CONFIG_PATH = DATA_DIR / "context_config.json"
CONTEXT_COST_MATRIX_PATH = DATA_DIR / "context_cost_matrix.csv"
CONTEXT_PATH_MATRIX_PATH = DATA_DIR / "context_path_matrix.json"


def read_csv(path):
    with open(path, "r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def write_csv(path, fieldnames, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def load_nodes(path=NODES_PATH):
    nodes = {}
    for row in read_csv(path):
        node_id = parse_node_id(row.get("node_id"), "nodes.csv")
        nodes[node_id] = row
    return nodes


def load_cost_matrix(path=CONTEXT_COST_MATRIX_PATH):
    if not Path(path).exists():
        raise FileNotFoundError(f"找不到 {path}，请先生成对应的 cost matrix。")
    costs = {}
    for row in read_csv(path):
        from_id = parse_node_id(row.get("from_id"), str(path))
        to_id = parse_node_id(row.get("to_id"), str(path))
        raw_cost = str(row.get("cost", "")).strip()
        if raw_cost.lower() == "inf":
            cost = math.inf
        else:
            try:
                cost = float(raw_cost)
            except ValueError as exc:
                raise ValueError(f"{path} 中 {from_id}->{to_id} 的 cost 不是数字: {raw_cost}") from exc
        costs[(from_id, to_id)] = cost
    return costs


def load_path_matrix(path=CONTEXT_PATH_MATRIX_PATH):
    if not Path(path).exists():
        raise FileNotFoundError(f"找不到 {path}，请先生成对应的 path matrix。")
    with open(path, "r", encoding="utf-8") as file:
        raw = json.load(file)
    matrix = {}
    for key, value in raw.items():
        try:
            from_id, to_id = key.split("->", 1)
            matrix[(int(from_id), int(to_id))] = [int(node) for node in value]
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{path} 中存在非法路径项: {key!r}") from exc
    return matrix


def load_delivery_task(path=DELIVERY_TASK_PATH):
    with open(path, "r", encoding="utf-8-sig") as file:
        task = json.load(file)

    start = parse_node_id(task.get("start"), "delivery_task.json")
    raw_points = task.get("points", [])
    if raw_points is None:
        raw_points = []
    if not isinstance(raw_points, list):
        raise ValueError("delivery_task.json 中 points 必须是数组。")

    points = []
    seen = set()
    for value in raw_points:
        point = parse_node_id(value, "delivery_task.json")
        if point == start or point in seen:
            continue
        seen.add(point)
        points.append(point)

    return {
        "start": start,
        "points": points,
        "return_to_start": bool(task.get("return_to_start", False)),
        "description": str(task.get("description", "")).strip(),
    }


def load_node_delay(path=NODE_DELAY_PATH):
    with open(path, "r", encoding="utf-8-sig") as file:
        raw = json.load(file)
    delays = {}
    for node_id, info in raw.items():
        parsed_id = parse_node_id(node_id, "node_delay.json")
        delays[parsed_id] = {
            "delay_min": float(info.get("delay_min", 0)),
            "reason": str(info.get("reason", "")).strip(),
        }
    return delays


def load_context_config(path=CONTEXT_CONFIG_PATH):
    with open(path, "r", encoding="utf-8-sig") as file:
        config = json.load(file)
    return {
        "weather": str(config.get("weather", "")).strip(),
        "cargo": str(config.get("cargo", "")).strip(),
        "description": str(config.get("description", "")).strip(),
    }


def parse_node_id(value, source):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{source} 中存在非法节点编号: {value!r}") from exc


def route_with_return(route, return_to_start=False):
    if return_to_start and route and route[-1] != route[0]:
        return route + [route[0]]
    return route[:]


def lookup_cost(cost_lookup, from_id, to_id):
    key = (from_id, to_id)
    if key not in cost_lookup:
        raise KeyError(f"cost matrix 缺少 {from_id}->{to_id} 的代价。")
    cost = cost_lookup[key]
    if math.isinf(cost):
        raise ValueError(f"{from_id}->{to_id} 不可达，代价为 inf。")
    return cost


def route_cost(route, cost_lookup, return_to_start=False):
    actual_route = route_with_return(route, return_to_start)
    if len(actual_route) < 2:
        return 0.0
    total = 0.0
    for from_id, to_id in zip(actual_route, actual_route[1:]):
        total += lookup_cost(cost_lookup, from_id, to_id)
    return total


def format_route_names(route, nodes, return_to_start=False):
    actual_route = route_with_return(route, return_to_start)
    return " -> ".join(nodes[node_id]["name"] for node_id in actual_route)


def format_route_labels(route, nodes, return_to_start=False):
    actual_route = route_with_return(route, return_to_start)
    return " -> ".join(f"{node_id} {nodes[node_id]['name']}" for node_id in actual_route)


def expand_full_path(route, path_matrix, return_to_start=False):
    actual_route = route_with_return(route, return_to_start)
    if not actual_route:
        return []
    expanded = [actual_route[0]]
    for from_id, to_id in zip(actual_route, actual_route[1:]):
        segment = path_matrix.get((from_id, to_id))
        if segment is None:
            raise KeyError(f"path matrix 缺少 {from_id}->{to_id} 的路径。")
        if not segment:
            raise ValueError(f"path matrix 中 {from_id}->{to_id} 的路径为空。")
        if segment[0] != from_id or segment[-1] != to_id:
            raise ValueError(f"path matrix 中 {from_id}->{to_id} 的路径端点不匹配: {segment}")
        expanded.extend(segment[1:])
    return expanded


def calculate_node_delay(full_path, node_delay, nodes):
    triggered = []
    seen = set()
    for node_id in full_path:
        if node_id in node_delay and node_id not in seen:
            seen.add(node_id)
            triggered.append((node_id, node_delay[node_id]))
    delay_time = sum(info["delay_min"] for _node_id, info in triggered)
    delayed_nodes = "; ".join(f"{node_id} {nodes[node_id]['name']}" for node_id, _info in triggered)
    return delay_time, triggered, delayed_nodes


def add_delay_nodes_from_segment(segment, node_delay, seen_delay_nodes):
    for node_id in segment:
        if node_id in node_delay:
            seen_delay_nodes.add(node_id)


def new_delay_time_for_segment(segment, node_delay, seen_delay_nodes):
    total = 0.0
    for node_id in segment:
        if node_id in node_delay and node_id not in seen_delay_nodes:
            total += node_delay[node_id]["delay_min"]
    return total


def segment_total_cost(from_id, to_id, cost_lookup, path_matrix=None, node_delay=None, seen_delay_nodes=None):
    drive_cost = lookup_cost(cost_lookup, from_id, to_id)
    if path_matrix is None or node_delay is None or seen_delay_nodes is None:
        return drive_cost

    segment = path_matrix.get((from_id, to_id))
    if segment is None:
        raise KeyError(f"path matrix 缺少 {from_id}->{to_id} 的路径。")
    return drive_cost + new_delay_time_for_segment(segment, node_delay, seen_delay_nodes)


def evaluate_route(route, cost_lookup, path_matrix, node_delay, nodes, return_to_start=False):
    drive_time = route_cost(route, cost_lookup, return_to_start)
    full_path = expand_full_path(route, path_matrix, return_to_start)
    delay_time, triggered, delayed_nodes = calculate_node_delay(full_path, node_delay, nodes)
    return {
        "route": route_with_return(route, return_to_start),
        "drive_time": drive_time,
        "delay_time": delay_time,
        "total_time": drive_time + delay_time,
        "triggered": triggered,
        "delayed_nodes": delayed_nodes,
    }


def nearest_neighbor_route(start, points, cost_lookup):
    route = [start]
    current = start
    unvisited = set(points)
    while unvisited:
        next_point = min(unvisited, key=lambda point: (lookup_cost(cost_lookup, current, point), point))
        lookup_cost(cost_lookup, current, next_point)
        route.append(next_point)
        unvisited.remove(next_point)
        current = next_point
    return route


def nearest_neighbor_route_with_delay(start, points, cost_lookup, path_matrix, node_delay):
    route = [start]
    current = start
    unvisited = set(points)
    seen_delay_nodes = set()
    add_delay_nodes_from_segment([start], node_delay, seen_delay_nodes)

    while unvisited:
        next_point = min(
            unvisited,
            key=lambda point: (
                segment_total_cost(current, point, cost_lookup, path_matrix, node_delay, seen_delay_nodes),
                point,
            ),
        )
        segment = path_matrix.get((current, next_point))
        if segment is None:
            raise KeyError(f"path matrix 缺少 {current}->{next_point} 的路径。")
        add_delay_nodes_from_segment(segment, node_delay, seen_delay_nodes)
        route.append(next_point)
        unvisited.remove(next_point)
        current = next_point
    return route


def save_algorithm_result(path, algorithm, config, route, nodes, drive_time, delay_time, total_time, delayed_nodes, return_to_start):
    row = {
        "algorithm": algorithm,
        "weather": config["weather"],
        "cargo": config["cargo"],
        "route_ids": json.dumps(route, ensure_ascii=False, separators=(",", ":")),
        "route_names": format_route_names(route, nodes, return_to_start=False),
        "drive_time": f"{drive_time:.2f}",
        "delay_time": f"{delay_time:.2f}",
        "total_time": f"{total_time:.2f}",
        "delayed_nodes": delayed_nodes,
        "return_to_start": str(return_to_start).lower(),
    }
    write_csv(
        path,
        [
            "algorithm",
            "weather",
            "cargo",
            "route_ids",
            "route_names",
            "drive_time",
            "delay_time",
            "total_time",
            "delayed_nodes",
            "return_to_start",
        ],
        [row],
    )
    return row

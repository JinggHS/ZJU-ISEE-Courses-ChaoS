import csv
import math
from collections import defaultdict, deque
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"

TERRAIN_FACTORS = {
    "flat": 1.00,
    "slight_up": 1.20,
    "steep_up": 1.50,
    "slight_down": 0.85,
    "steep_down": 0.75,
}

# Calibration from the marked map:
# 94 + 204 map units from North Gate to the campus-hospital axis is about 200 m.
MAP_UNITS_PER_200M = 94 + 204
METERS_PER_MAP_UNIT = 200 / MAP_UNITS_PER_200M
E_BIKE_SPEED_KMH = 25
E_BIKE_SPEED_M_PER_MIN = E_BIKE_SPEED_KMH * 1000 / 60

REVERSE_SLOPE = {
    "flat": "flat",
    "slight_up": "slight_down",
    "steep_up": "steep_down",
    "slight_down": "slight_up",
    "steep_down": "steep_up",
    "TODO": "TODO",
}


def warn(message):
    print(f"WARNING: {message}")


def read_csv(path):
    with open(path, "r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def write_csv(path, fieldnames, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def load_nodes(path=None):
    path = path or DATA_DIR / "nodes.csv"
    nodes = read_csv(path)
    seen = set()
    for row in nodes:
        node_id = row.get("node_id", "").strip()
        if not node_id:
            warn("nodes.csv contains an empty node_id.")
            continue
        if node_id in seen:
            warn(f"Duplicate node_id in nodes.csv: {node_id}")
        seen.add(node_id)

    required = {str(i) for i in range(1, 20)}
    missing = sorted(required - seen, key=int)
    if missing:
        warn(f"Missing required location nodes 1-19: {missing}")
    return nodes


def load_edges_raw(path=None):
    path = path or DATA_DIR / "edges_raw.csv"
    return read_csv(path)


def parse_distance(value, edge_id):
    text = str(value).strip()
    if not text or text.upper() == "TODO":
        warn(f"{edge_id}: distance is TODO and will be skipped.")
        return None
    try:
        return float(text)
    except ValueError:
        warn(f"{edge_id}: distance is not numeric: {value!r}; edge will be skipped.")
        return None


def normalize_slope(value, edge_id):
    slope = str(value).strip()
    if not slope:
        warn(f"{edge_id}: empty slope_type; defaulting to flat.")
        return "flat", False
    if slope == "TODO":
        warn(f"{edge_id}: slope_type is TODO; defaulting to flat for preprocessing.")
        return "flat", True
    if slope not in TERRAIN_FACTORS:
        warn(f"{edge_id}: invalid slope_type {slope!r}; defaulting to flat.")
        return "flat", True
    return slope, False


def validate_edges(nodes, edges_raw):
    node_ids = {row["node_id"] for row in nodes}
    todo_distance = []
    todo_slope = []
    for edge in edges_raw:
        edge_id = edge.get("edge_id", "")
        from_id = edge.get("from_id", "")
        to_id = edge.get("to_id", "")
        if from_id not in node_ids:
            warn(f"{edge_id}: from_id {from_id!r} is not in nodes.csv.")
        if to_id not in node_ids:
            warn(f"{edge_id}: to_id {to_id!r} is not in nodes.csv.")
        distance = str(edge.get("distance", "")).strip()
        if not distance or distance.upper() == "TODO":
            todo_distance.append(edge_id)
        else:
            try:
                float(distance)
            except ValueError:
                warn(f"{edge_id}: distance is not numeric: {distance!r}")
        if str(edge.get("slope_type", "")).strip() == "TODO":
            todo_slope.append(edge_id)

    if todo_distance:
        warn(f"Edges with TODO distance: {todo_distance}")
    if todo_slope:
        warn(f"Edges with TODO slope_type: {todo_slope}")
    return todo_distance, todo_slope


def build_directed_edges(nodes, edges_raw):
    validate_edges(nodes, edges_raw)
    rows = []
    for edge in edges_raw:
        edge_id = edge["edge_id"]
        distance = parse_distance(edge.get("distance", ""), edge_id)
        if distance is None:
            continue
        distance_m = distance * METERS_PER_MAP_UNIT
        time_min = distance_m / E_BIKE_SPEED_M_PER_MIN
        slope, _had_slope_issue = normalize_slope(edge.get("slope_type", ""), edge_id)
        reverse_slope = REVERSE_SLOPE[slope]

        for from_id, to_id, direction_slope in (
            (edge["from_id"], edge["to_id"], slope),
            (edge["to_id"], edge["from_id"], reverse_slope),
        ):
            factor = TERRAIN_FACTORS[direction_slope]
            rows.append({
                "directed_edge_id": f"DE{len(rows) + 1:03d}",
                "from_id": from_id,
                "to_id": to_id,
                "distance": format_number(distance),
                "distance_m": format_number(distance_m),
                "slope_type": direction_slope,
                "factor": f"{factor:.2f}",
                "time_min": format_number(time_min),
                "cost": format_number(time_min * factor),
                "source_edge_id": edge_id,
            })
    return rows


def format_number(value):
    rounded = round(float(value), 3)
    if math.isclose(rounded, round(rounded)):
        return str(int(round(rounded)))
    return f"{rounded:.3f}".rstrip("0").rstrip(".")


def write_directed_edges(rows, path=None):
    path = path or DATA_DIR / "directed_edges.csv"
    write_csv(
        path,
        [
            "directed_edge_id",
            "from_id",
            "to_id",
            "distance",
            "distance_m",
            "slope_type",
            "factor",
            "time_min",
            "cost",
            "source_edge_id",
        ],
        rows,
    )


def build_undirected_adjacency(nodes, directed_edges):
    adjacency = defaultdict(set)
    for node in nodes:
        adjacency[node["node_id"]]
    for edge in directed_edges:
        adjacency[edge["from_id"]].add(edge["to_id"])
        adjacency[edge["to_id"]].add(edge["from_id"])
    return adjacency


def connectivity_report(nodes, directed_edges):
    adjacency = build_undirected_adjacency(nodes, directed_edges)
    node_ids = [node["node_id"] for node in nodes]
    isolated = sorted([node_id for node_id in node_ids if not adjacency[node_id]], key=sort_node_id)
    if isolated:
        warn(f"Isolated nodes: {isolated}")

    if not node_ids:
        return False, isolated

    start = node_ids[0]
    seen = {start}
    queue = deque([start])
    while queue:
        current = queue.popleft()
        for neighbor in adjacency[current]:
            if neighbor not in seen:
                seen.add(neighbor)
                queue.append(neighbor)
    connected = len(seen) == len(node_ids)
    if not connected:
        missing = sorted(set(node_ids) - seen, key=sort_node_id)
        warn(f"Graph is not connected. Unreachable from {start}: {missing}")
    return connected, isolated


def sort_node_id(value):
    text = str(value)
    return (0, int(text)) if text.isdigit() else (1, text)

import csv
import json
import math
from pathlib import Path

from build_graph import DATA_DIR, load_nodes, sort_node_id
from generate_matrix import format_cost, write_cost_matrix
from shortest_path import build_adjacency, dijkstra, reconstruct_path


DIRECTED_EDGES_PATH = DATA_DIR / "directed_edges.csv"
CONTEXT_CONFIG_PATH = DATA_DIR / "context_config.json"
CONTEXT_EDGES_PATH = DATA_DIR / "context_edges.csv"
CONTEXT_COST_MATRIX_PATH = DATA_DIR / "context_cost_matrix.csv"
CONTEXT_PATH_MATRIX_PATH = DATA_DIR / "context_path_matrix.json"

DEFAULT_CONTEXT_CONFIG = {
    "weather": "rainy",
    "cargo": "heavy",
    "description": "默认场景：雨天重货物",
}

WEATHER_FACTORS = {
    "sunny": {"flat": 1.00, "up": 1.00, "down": 1.00},
    "rainy": {"flat": 1.25, "up": 1.00, "down": 1 / 0.6},
    "hot": {"flat": 1 / 0.9, "up": 1 / 0.75, "down": 1.00},
}

CARGO_FACTORS = {
    "small": {"flat": 1.00, "up": 1.00, "down": 1.00},
    "medium": {"flat": 1.00, "up": 1 / 0.8, "down": 1.00},
    "heavy": {"flat": 1.00, "up": 2.00, "down": 1 / 0.8},
}

SLOPE_GROUPS = {
    "flat": "flat",
    "slight_up": "up",
    "steep_up": "up",
    "slight_down": "down",
    "steep_down": "down",
}


def read_csv(path):
    with open(path, "r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def write_csv(path, fieldnames, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def ensure_context_config():
    if CONTEXT_CONFIG_PATH.exists():
        return
    with open(CONTEXT_CONFIG_PATH, "w", encoding="utf-8-sig") as file:
        json.dump(DEFAULT_CONTEXT_CONFIG, file, ensure_ascii=False, indent=2)
        file.write("\n")
    print(f"已创建默认情景配置文件: {CONTEXT_CONFIG_PATH}")


def load_context_config():
    ensure_context_config()
    with open(CONTEXT_CONFIG_PATH, "r", encoding="utf-8-sig") as file:
        config = json.load(file)

    weather = str(config.get("weather", "")).strip().lower()
    cargo = str(config.get("cargo", "")).strip().lower()
    if weather not in WEATHER_FACTORS:
        valid = ", ".join(WEATHER_FACTORS)
        raise ValueError(f"context_config.json 中 weather={weather!r} 非法，必须是: {valid}")
    if cargo not in CARGO_FACTORS:
        valid = ", ".join(CARGO_FACTORS)
        raise ValueError(f"context_config.json 中 cargo={cargo!r} 非法，必须是: {valid}")

    return {
        "weather": weather,
        "cargo": cargo,
        "description": str(config.get("description", "")).strip(),
    }


def save_context_config(weather, cargo, description=None):
    config = {
        "weather": str(weather).strip().lower(),
        "cargo": str(cargo).strip().lower(),
        "description": description or f"交互选择场景：{weather} + {cargo}",
    }
    if config["weather"] not in WEATHER_FACTORS:
        valid = ", ".join(WEATHER_FACTORS)
        raise ValueError(f"weather={config['weather']!r} 非法，必须是: {valid}")
    if config["cargo"] not in CARGO_FACTORS:
        valid = ", ".join(CARGO_FACTORS)
        raise ValueError(f"cargo={config['cargo']!r} 非法，必须是: {valid}")

    with open(CONTEXT_CONFIG_PATH, "w", encoding="utf-8-sig") as file:
        json.dump(config, file, ensure_ascii=False, indent=2)
        file.write("\n")
    return config


def slope_group(slope_type):
    slope = str(slope_type).strip()
    if slope not in SLOPE_GROUPS:
        raise ValueError(f"directed_edges.csv 中存在未知 slope_type: {slope!r}")
    return SLOPE_GROUPS[slope]


def parse_cost(value, edge_id):
    try:
        return float(str(value).strip())
    except (TypeError, ValueError) as exc:
        raise ValueError(f"directed_edges.csv 中 {edge_id} 的 cost 不是数字: {value!r}") from exc


def build_context_edges(directed_edges, config):
    weather = config["weather"]
    cargo = config["cargo"]
    rows = []

    for edge in directed_edges:
        edge_id = edge["directed_edge_id"]
        base_cost = parse_cost(edge.get("cost"), edge_id)
        group = slope_group(edge.get("slope_type", ""))
        weather_factor = WEATHER_FACTORS[weather][group]
        cargo_factor = CARGO_FACTORS[cargo][group]
        context_cost = base_cost * weather_factor * cargo_factor

        rows.append({
            "directed_edge_id": edge_id,
            "from_id": edge["from_id"],
            "to_id": edge["to_id"],
            "distance": edge["distance"],
            "slope_type": edge["slope_type"],
            "base_cost": format_cost(base_cost),
            "weather": weather,
            "cargo": cargo,
            "weather_factor": format_cost(weather_factor),
            "cargo_factor": format_cost(cargo_factor),
            "context_cost": format_cost(context_cost),
            "source_edge_id": edge["source_edge_id"],
        })
    return rows


def generate_context_matrices(nodes, context_edges):
    matrix_edges = [
        {"from_id": row["from_id"], "to_id": row["to_id"], "cost": row["context_cost"]}
        for row in context_edges
    ]
    adjacency = build_adjacency(matrix_edges)
    node_ids = sorted([row["node_id"] for row in nodes], key=sort_node_id)
    cost_rows = []
    path_map = {}
    unreachable = []

    for source in node_ids:
        distances, previous = dijkstra(adjacency, source)
        for target in node_ids:
            cost = distances.get(target, math.inf)
            if math.isinf(cost):
                unreachable.append((source, target))
                cost_text = "inf"
                path = []
            else:
                cost_text = format_cost(cost)
                path = reconstruct_path(previous, source, target)
            cost_rows.append({"from_id": source, "to_id": target, "cost": cost_text})
            path_map[f"{source}->{target}"] = [int(node) if str(node).isdigit() else node for node in path]

    return cost_rows, path_map, unreachable


def generate_context_outputs(config=None, verbose=True):
    if not DIRECTED_EDGES_PATH.exists():
        raise FileNotFoundError(
            f"找不到 {DIRECTED_EDGES_PATH}，请先运行: python src/generate_matrix.py"
        )

    config = config or load_context_config()
    directed_edges = read_csv(DIRECTED_EDGES_PATH)
    context_edges = build_context_edges(directed_edges, config)
    write_csv(
        CONTEXT_EDGES_PATH,
        [
            "directed_edge_id",
            "from_id",
            "to_id",
            "distance",
            "slope_type",
            "base_cost",
            "weather",
            "cargo",
            "weather_factor",
            "cargo_factor",
            "context_cost",
            "source_edge_id",
        ],
        context_edges,
    )

    nodes = load_nodes()
    cost_rows, path_map, unreachable = generate_context_matrices(nodes, context_edges)
    write_cost_matrix(cost_rows, CONTEXT_COST_MATRIX_PATH)
    with open(CONTEXT_PATH_MATRIX_PATH, "w", encoding="utf-8") as file:
        json.dump(path_map, file, ensure_ascii=False, indent=2)

    if not verbose:
        return {
            "config": config,
            "edge_count": len(context_edges),
            "unreachable_count": len(unreachable),
            "context_edges_path": CONTEXT_EDGES_PATH,
            "context_cost_matrix_path": CONTEXT_COST_MATRIX_PATH,
            "context_path_matrix_path": CONTEXT_PATH_MATRIX_PATH,
        }

    print("当前情景:")
    print(f"weather = {config['weather']}")
    print(f"cargo = {config['cargo']}")
    if config["description"]:
        print(f"说明: {config['description']}")
    print()
    print(f"有向边数量: {len(context_edges)}")
    print(f"无法到达节点对数量: {len(unreachable)}")
    print(f"context_edges.csv 输出位置: {CONTEXT_EDGES_PATH}")
    print(f"context_cost_matrix.csv 输出位置: {CONTEXT_COST_MATRIX_PATH}")
    print(f"context_path_matrix.json 输出位置: {CONTEXT_PATH_MATRIX_PATH}")
    return {
        "config": config,
        "edge_count": len(context_edges),
        "unreachable_count": len(unreachable),
        "context_edges_path": CONTEXT_EDGES_PATH,
        "context_cost_matrix_path": CONTEXT_COST_MATRIX_PATH,
        "context_path_matrix_path": CONTEXT_PATH_MATRIX_PATH,
    }


def main():
    generate_context_outputs()


if __name__ == "__main__":
    main()

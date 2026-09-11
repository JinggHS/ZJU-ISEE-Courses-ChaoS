import csv
import json
import math
from pathlib import Path

from build_graph import (
    DATA_DIR,
    build_directed_edges,
    connectivity_report,
    load_edges_raw,
    load_nodes,
    sort_node_id,
    warn,
    write_directed_edges,
)
from shortest_path import build_adjacency, dijkstra, reconstruct_path


def write_cost_matrix(rows, path):
    with open(path, "w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["from_id", "to_id", "cost"])
        writer.writeheader()
        writer.writerows(rows)


def generate_matrices(nodes, directed_edges):
    adjacency = build_adjacency(directed_edges)
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

    if unreachable:
        preview = ", ".join(f"{a}->{b}" for a, b in unreachable[:20])
        more = "" if len(unreachable) <= 20 else f" ... (+{len(unreachable) - 20})"
        warn(f"Unreachable node pairs: {preview}{more}")

    return cost_rows, path_map, unreachable


def format_cost(value):
    rounded = round(float(value), 3)
    if math.isclose(rounded, round(rounded)):
        return str(int(round(rounded)))
    return f"{rounded:.3f}".rstrip("0").rstrip(".")


def has_todo(edges_raw):
    for edge in edges_raw:
        if str(edge.get("distance", "")).strip().upper() == "TODO":
            return True
        if str(edge.get("slope_type", "")).strip().upper() == "TODO":
            return True
    return False


def main():
    nodes = load_nodes()
    edges_raw = load_edges_raw()
    directed_edges = build_directed_edges(nodes, edges_raw)
    write_directed_edges(directed_edges)
    connected, isolated = connectivity_report(nodes, directed_edges)
    cost_rows, path_map, unreachable = generate_matrices(nodes, directed_edges)

    cost_path = DATA_DIR / "cost_matrix.csv"
    path_path = DATA_DIR / "path_matrix.json"
    write_cost_matrix(cost_rows, cost_path)
    with open(path_path, "w", encoding="utf-8") as file:
        json.dump(path_map, file, ensure_ascii=False, indent=2)

    print(f"节点数量: {len(nodes)}")
    print(f"原始边数量: {len(edges_raw)}")
    print(f"有向边数量: {len(directed_edges)}")
    print(f"是否连通: {'是' if connected else '否'}")
    print(f"孤立节点数量: {len(isolated)}")
    print(f"无法到达节点对数量: {len(unreachable)}")
    print(f"是否存在 TODO: {'是' if has_todo(edges_raw) else '否'}")
    print(f"cost_matrix.csv 输出位置: {cost_path}")
    print(f"path_matrix.json 输出位置: {path_path}")


if __name__ == "__main__":
    main()

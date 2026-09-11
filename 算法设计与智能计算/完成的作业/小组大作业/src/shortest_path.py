import heapq
import math
from collections import defaultdict


def build_adjacency(directed_edges):
    adjacency = defaultdict(list)
    for edge in directed_edges:
        adjacency[edge["from_id"]].append((edge["to_id"], float(edge["cost"])))
    return adjacency


def dijkstra(adjacency, source):
    distances = {source: 0.0}
    previous = {}
    queue = [(0.0, source)]

    while queue:
        current_cost, current = heapq.heappop(queue)
        if current_cost > distances.get(current, math.inf):
            continue
        for neighbor, edge_cost in adjacency.get(current, []):
            candidate = current_cost + edge_cost
            if candidate < distances.get(neighbor, math.inf):
                distances[neighbor] = candidate
                previous[neighbor] = current
                heapq.heappush(queue, (candidate, neighbor))

    return distances, previous


def reconstruct_path(previous, source, target):
    if source == target:
        return [source]
    if target not in previous:
        return []

    path = [target]
    while path[-1] != source:
        parent = previous.get(path[-1])
        if parent is None:
            return []
        path.append(parent)
    path.reverse()
    return path

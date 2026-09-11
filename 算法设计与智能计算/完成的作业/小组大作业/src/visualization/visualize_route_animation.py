from PIL import Image

import visualize_route_animation as legacy_viz
from route_common import expand_full_path


def visualize_route(route, full_path, result_info, nodes):
    base_path = legacy_viz.find_base_map()
    topology_path = legacy_viz.find_topology_map()
    base = Image.open(base_path).convert("RGB")
    topology_base = Image.open(topology_path).convert("RGB")

    edge_segments = legacy_viz.load_edge_segments(nodes)
    polyline = legacy_viz.build_route_polyline(full_path, edge_segments, base.size)
    topology_polyline = legacy_viz.build_route_polyline(full_path, edge_segments, topology_base.size)
    if len(polyline) < 2:
        raise RuntimeError("路线坐标不足，无法绘图。")
    if len(topology_polyline) < 2:
        raise RuntimeError("拓扑图路线坐标不足，无法绘图。")

    legacy_viz.ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    title_lines = [
        f"{result_info['algorithm']}  总计 {result_info['total_time']:.2f} 分钟",
        (
            f"{result_info['weather']} + {result_info['cargo']}  "
            f"行驶 {result_info['drive_time']:.2f} + 停留 {result_info['delay_time']:.2f}"
        ),
    ]

    static_image = legacy_viz.draw_route(
        base,
        polyline,
        route,
        nodes,
        title_lines,
        progress_ratio=1.0,
        moving_dot=False,
    )
    static_image.save(legacy_viz.STATIC_OUTPUT)

    topology_image = legacy_viz.draw_route(
        topology_base,
        topology_polyline,
        route,
        nodes,
        title_lines,
        progress_ratio=1.0,
        moving_dot=False,
    )
    topology_image.save(legacy_viz.TOPOLOGY_STATIC_OUTPUT)
    legacy_viz.save_animation(base, polyline, route, nodes, title_lines, legacy_viz.ANIMATION_OUTPUT)

    return {
        "map": legacy_viz.STATIC_OUTPUT,
        "topology": legacy_viz.TOPOLOGY_STATIC_OUTPUT,
        "animation": legacy_viz.ANIMATION_OUTPUT,
    }


def visualize_from_route(route, path_matrix, result_info, nodes, return_to_start=False):
    full_path = expand_full_path(route, path_matrix, return_to_start=return_to_start)
    return visualize_route(route, full_path, result_info, nodes)

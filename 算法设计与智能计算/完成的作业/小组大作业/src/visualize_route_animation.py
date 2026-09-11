import csv
import json
import math
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from algorithms.greedy import solve as greedy_solve
from route_common import (
    DATA_DIR,
    CONTEXT_PATH_MATRIX_PATH,
    evaluate_route,
    expand_full_path,
    format_route_labels,
    load_cost_matrix,
    load_delivery_task,
    load_node_delay,
    load_nodes,
    load_path_matrix,
)


ROOT_DIR = Path(__file__).resolve().parents[1]
ROUTE_DIR = ROOT_DIR / "route"
BASE_MAP_NAME = "yuquan_gps_中轴线_标注.png"
TOPOLOGY_MAP_NAME = "yuquan_gps_map_road_topology_orthogonal_cleaned_colored_slope_check.png"
STATIC_OUTPUT = ROUTE_DIR / "route_on_yuquan_map.png"
TOPOLOGY_STATIC_OUTPUT = ROUTE_DIR / "route_on_topology_slope_check.png"
ANIMATION_OUTPUT = ROUTE_DIR / "route_animation.gif"

TOPOLOGY_WIDTH = 1600
TOPOLOGY_HEIGHT = 2560


def read_csv(path):
    with open(path, "r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def find_base_map():
    preferred = DATA_DIR / BASE_MAP_NAME
    if preferred.exists():
        return preferred
    matches = [path for path in DATA_DIR.glob("*.png") if "中轴线" in path.name and "标注" in path.name]
    if not matches:
        raise FileNotFoundError(f"找不到底图: {preferred}")
    return matches[0]


def find_topology_map():
    path = DATA_DIR / TOPOLOGY_MAP_NAME
    if not path.exists():
        raise FileNotFoundError(f"找不到拓扑底图: {path}")
    return path


def parse_topology_coord(text):
    match = re.search(r"像素坐标\(([-\d.]+),([-\d.]+)\)", text or "")
    if not match:
        return None
    return float(match.group(1)), float(match.group(2))


def parse_segment(text):
    match = re.search(
        r"pixel segment \(([-\d.]+),([-\d.]+)\)-\(([-\d.]+),([-\d.]+)\)",
        text or "",
    )
    if not match:
        return None
    return (
        (float(match.group(1)), float(match.group(2))),
        (float(match.group(3)), float(match.group(4))),
    )


def distance(point_a, point_b):
    return math.hypot(point_a[0] - point_b[0], point_a[1] - point_b[1])


def load_reference_node_coords(nodes):
    coords = {}
    for node_id, row in nodes.items():
        coord = parse_topology_coord(row.get("note", ""))
        if coord is not None:
            coords[node_id] = coord
    return coords


def ordered_segment(from_id, to_id, point_a, point_b, reference_coords):
    from_coord = reference_coords.get(from_id)
    to_coord = reference_coords.get(to_id)

    if from_coord is not None:
        return (point_a, point_b) if distance(from_coord, point_a) <= distance(from_coord, point_b) else (point_b, point_a)
    if to_coord is not None:
        return (point_b, point_a) if distance(to_coord, point_a) <= distance(to_coord, point_b) else (point_a, point_b)
    return point_a, point_b


def load_edge_segments(nodes):
    edges = read_csv(DATA_DIR / "edges_raw.csv")
    reference_coords = load_reference_node_coords(nodes)
    segments = {}

    for edge in edges:
        segment = parse_segment(edge.get("comment", ""))
        if segment is None:
            continue
        from_id = int(edge["from_id"])
        to_id = int(edge["to_id"])
        start, end = ordered_segment(from_id, to_id, segment[0], segment[1], reference_coords)
        segments[(from_id, to_id)] = (start, end)
        segments[(to_id, from_id)] = (end, start)
    return segments


def scale_point(point, image_size):
    width, height = image_size
    return (
        point[0] * width / TOPOLOGY_WIDTH,
        point[1] * height / TOPOLOGY_HEIGHT,
    )


def build_route_polyline(full_path, edge_segments, image_size):
    points = []
    missing = []
    for from_id, to_id in zip(full_path, full_path[1:]):
        segment = edge_segments.get((from_id, to_id))
        if segment is None:
            missing.append((from_id, to_id))
            continue
        start, end = scale_point(segment[0], image_size), scale_point(segment[1], image_size)
        if not points:
            points.append(start)
        elif distance(points[-1], start) > 0.1:
            points.append(start)
        points.append(end)
    if missing:
        preview = ", ".join(f"{a}->{b}" for a, b in missing[:8])
        more = "" if len(missing) <= 8 else f" ... (+{len(missing) - 8})"
        print(f"WARNING: 缺少以下路径段的绘图坐标: {preview}{more}")
    return points


def load_font(size):
    candidates = [
        Path("C:/Windows/Fonts/msyh.ttc"),
        Path("C:/Windows/Fonts/simhei.ttf"),
        Path("C:/Windows/Fonts/simsun.ttc"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def draw_label(draw, xy, text, font, fill=(0, 0, 0), bg=(255, 255, 255), anchor="left"):
    x, y = xy
    bbox = draw.multiline_textbbox((x, y), text, font=font, spacing=4)
    if anchor == "top_right":
        width = bbox[2] - bbox[0]
        x = x - width
        bbox = draw.multiline_textbbox((x, y), text, font=font, spacing=4)
    padding = 4
    box = (
        bbox[0] - padding,
        bbox[1] - padding,
        bbox[2] + padding,
        bbox[3] + padding,
    )
    draw.rounded_rectangle(box, radius=3, fill=bg, outline=fill, width=1)
    draw.multiline_text((x, y), text, font=font, fill=fill, spacing=4)


def arrow_polygon(point, angle, size):
    x, y = point
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    back_x = x - size * cos_a
    back_y = y - size * sin_a
    wing = size * 0.58
    return [
        (x, y),
        (back_x - wing * sin_a, back_y + wing * cos_a),
        (back_x + wing * sin_a, back_y - wing * cos_a),
    ]


def draw_arrowheads(draw, points, color, step=150, size=14):
    if len(points) < 2:
        return

    segment_lengths = [distance(a, b) for a, b in zip(points, points[1:])]
    total = sum(segment_lengths)
    if total <= 0:
        return

    targets = []
    current = step
    while current < total:
        targets.append(current)
        current += step
    targets.append(total)

    walked = 0.0
    target_index = 0
    for start, end, length in zip(points, points[1:], segment_lengths):
        if length <= 0:
            continue
        while target_index < len(targets) and targets[target_index] <= walked + length:
            remain = targets[target_index] - walked
            ratio = remain / length
            point = (
                start[0] + (end[0] - start[0]) * ratio,
                start[1] + (end[1] - start[1]) * ratio,
            )
            angle = math.atan2(end[1] - start[1], end[0] - start[0])
            draw.polygon(arrow_polygon(point, angle, size), fill=color)
            target_index += 1
        walked += length


def draw_route(
    base,
    polyline,
    route,
    nodes,
    title_lines,
    progress_ratio=1.0,
    moving_dot=True,
    route_color=(0, 150, 80, 255),
    show_arrows=True,
):
    image = base.convert("RGBA")
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    if len(polyline) >= 2:
        visible = partial_polyline(polyline, progress_ratio)
        if len(visible) >= 2:
            draw.line(visible, fill=(255, 255, 255, 230), width=16, joint="curve")
            draw.line(visible, fill=route_color, width=10, joint="curve")
            if show_arrows:
                draw_arrowheads(draw, visible, route_color)
            if moving_dot:
                x, y = visible[-1]
                draw.ellipse((x - 9, y - 9, x + 9, y + 9), fill=(30, 90, 240, 255), outline=(255, 255, 255, 255), width=3)

    image = Image.alpha_composite(image, overlay)
    draw = ImageDraw.Draw(image)
    title_font = load_font(20)
    label_font = load_font(15)

    draw_label(draw, (image.size[0] - 14, 14), "\n".join(title_lines), title_font, anchor="top_right")

    if polyline:
        start = polyline[0]
        end = polyline[-1]
        draw.ellipse((start[0] - 8, start[1] - 8, start[0] + 8, start[1] + 8), fill=(20, 150, 60), outline=(255, 255, 255), width=3)
        draw.ellipse((end[0] - 8, end[1] - 8, end[0] + 8, end[1] + 8), fill=(130, 55, 200), outline=(255, 255, 255), width=3)
        draw_label(draw, (start[0] + 12, start[1] - 22), "起点", label_font, fill=(20, 110, 45))
        draw_label(draw, (end[0] + 12, end[1] - 22), "终点", label_font, fill=(90, 35, 160))

    return image.convert("RGB")


def partial_polyline(polyline, progress_ratio):
    if not polyline:
        return []
    if progress_ratio >= 1:
        return polyline[:]

    segment_lengths = [distance(a, b) for a, b in zip(polyline, polyline[1:])]
    total = sum(segment_lengths)
    if total <= 0:
        return [polyline[0]]

    target = total * max(0.0, min(1.0, progress_ratio))
    points = [polyline[0]]
    walked = 0.0
    for start, end, length in zip(polyline, polyline[1:], segment_lengths):
        if walked + length < target:
            points.append(end)
            walked += length
            continue
        remain = target - walked
        ratio = 0 if length == 0 else remain / length
        points.append((start[0] + (end[0] - start[0]) * ratio, start[1] + (end[1] - start[1]) * ratio))
        break
    return points


def save_animation(base, polyline, route, nodes, title_lines, output_path):
    frames = []
    frame_count = 90
    for index in range(frame_count):
        ratio = index / (frame_count - 1)
        frame = draw_route(
            base,
            polyline,
            route,
            nodes,
            title_lines,
            progress_ratio=ratio,
            moving_dot=True,
            show_arrows=False,
        )
        frames.append(frame)
    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=70,
        loop=0,
        optimize=True,
    )


def main():
    nodes = load_nodes()
    task = load_delivery_task()
    costs = load_cost_matrix()
    path_matrix = load_path_matrix(CONTEXT_PATH_MATRIX_PATH)
    node_delay = load_node_delay()

    solved = greedy_solve(
        task["start"],
        task["points"],
        costs,
        return_to_start=task["return_to_start"],
        path_matrix=path_matrix,
        node_delay=node_delay,
        nodes=nodes,
    )
    route_eval = evaluate_route(
        solved["route"],
        costs,
        path_matrix,
        node_delay,
        nodes,
        task["return_to_start"],
    )
    route = route_eval["route"]
    full_path = expand_full_path(solved["route"], path_matrix, task["return_to_start"])
    base_path = find_base_map()
    topology_path = find_topology_map()
    base = Image.open(base_path).convert("RGB")
    topology_base = Image.open(topology_path).convert("RGB")

    edge_segments = load_edge_segments(nodes)
    polyline = build_route_polyline(full_path, edge_segments, base.size)
    topology_polyline = build_route_polyline(full_path, edge_segments, topology_base.size)
    if len(polyline) < 2:
        raise RuntimeError("路线坐标不足，无法绘图。")
    if len(topology_polyline) < 2:
        raise RuntimeError("拓扑图路线坐标不足，无法绘图。")

    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    title_lines = [
        f"贪心路线  总计 {route_eval['total_time']:.2f} 分钟",
        f"行驶 {route_eval['drive_time']:.2f} 分钟 + 停留 {route_eval['delay_time']:.2f} 分钟",
    ]
    static_image = draw_route(base, polyline, route, nodes, title_lines, progress_ratio=1.0, moving_dot=False)
    static_image.save(STATIC_OUTPUT)
    topology_image = draw_route(
        topology_base,
        topology_polyline,
        route,
        nodes,
        title_lines,
        progress_ratio=1.0,
        moving_dot=False,
    )
    topology_image.save(TOPOLOGY_STATIC_OUTPUT)
    save_animation(base, polyline, route, nodes, title_lines, ANIMATION_OUTPUT)

    print("贪心算法路线:")
    print(format_route_labels(route, nodes))
    print(f"行驶时间: {route_eval['drive_time']:.2f} 分钟")
    print(f"停留惩罚: {route_eval['delay_time']:.2f} 分钟")
    if route_eval["triggered"]:
        print("触发停留节点:")
        for node_id, info in route_eval["triggered"]:
            print(f"{node_id} {nodes[node_id]['name']}: {info['delay_min']:.2f} 分钟，{info['reason']}")
    else:
        print("触发停留节点: 无")
    print(f"总时间: {route_eval['total_time']:.2f} 分钟")
    print(f"底图: {base_path}")
    print(f"拓扑底图: {topology_path}")
    print(f"静态路线图: {STATIC_OUTPUT}")
    print(f"拓扑静态路线图: {TOPOLOGY_STATIC_OUTPUT}")
    print(f"路线动画: {ANIMATION_OUTPUT}")


if __name__ == "__main__":
    main()

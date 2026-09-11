import argparse
import csv
import json
import math
import time

from algorithms import exact_dp
from context_cost_model import (
    CONTEXT_COST_MATRIX_PATH,
    CONTEXT_PATH_MATRIX_PATH,
    generate_context_outputs,
    load_context_config,
    save_context_config,
)
from route_common import (
    RESULTS_DIR,
    evaluate_route,
    format_route_names,
    load_cost_matrix,
    load_delivery_task,
    load_node_delay,
    load_nodes,
    load_path_matrix,
    write_csv,
)


RESULT_PATH = RESULTS_DIR / "exact_dp_result_context.csv"
INTERACTIVE_RESULT_PATH = RESULTS_DIR / "interactive_result.csv"


def run_exact_dp(max_points=12, source="auto"):
    task, config, source_name = load_task_and_config(source)
    generate_context_outputs(config, verbose=False)

    nodes = load_nodes()
    cost_matrix = load_cost_matrix(CONTEXT_COST_MATRIX_PATH)
    path_matrix = load_path_matrix(CONTEXT_PATH_MATRIX_PATH)
    node_delay = load_node_delay()

    start_time = time.perf_counter()
    solved = exact_dp.solve(
        task["start"],
        task["points"],
        cost_matrix,
        return_to_start=task["return_to_start"],
        path_matrix=path_matrix,
        node_delay=node_delay,
        nodes=nodes,
        max_points=max_points,
    )
    runtime_seconds = time.perf_counter() - start_time
    evaluated = evaluate_route(
        solved["route"],
        cost_matrix,
        path_matrix,
        node_delay,
        nodes,
        task["return_to_start"],
    )

    result = {
        "algorithm": solved["algorithm"],
        "config": config,
        "route": evaluated["route"],
        "route_names": format_route_names(evaluated["route"], nodes),
        "drive_time": evaluated["drive_time"],
        "delay_time": evaluated["delay_time"],
        "total_time": evaluated["total_time"],
        "delayed_nodes": evaluated["delayed_nodes"],
        "return_to_start": task["return_to_start"],
        "checked_routes": solved["checked_routes"],
        "checked_states": solved.get("checked_states", ""),
        "checked_transitions": solved.get("checked_transitions", ""),
        "runtime_seconds": runtime_seconds,
        "source": source_name,
    }
    save_result(result)
    return result


def load_task_and_config(source):
    normalized = str(source).strip().lower()
    if normalized not in {"auto", "ui", "task"}:
        raise ValueError("source 必须是 auto、ui 或 task。")

    if normalized in {"auto", "ui"}:
        ui_task = load_task_from_interactive_result()
        if ui_task is not None:
            task, config = ui_task
            saved_config = save_context_config(
                config["weather"],
                config["cargo"],
                description=f"exact_dp 验证 UI 最近一次任务：{config['weather']} + {config['cargo']}",
            )
            return task, saved_config, "interactive_result.csv"
        if normalized == "ui":
            raise FileNotFoundError(f"找不到可用的 UI 结果文件: {INTERACTIVE_RESULT_PATH}")

    return load_delivery_task(), load_context_config(), "delivery_task.json"


def load_task_from_interactive_result():
    if not INTERACTIVE_RESULT_PATH.exists():
        return None
    with open(INTERACTIVE_RESULT_PATH, "r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))
    if not rows:
        return None

    row = rows[-1]
    route = json.loads(row["route_ids"])
    if not route:
        return None

    start = int(route[0])
    return_to_start = parse_bool(row.get("return_to_start", "false"))
    route_without_return = route[:]
    if return_to_start and len(route_without_return) > 1 and route_without_return[-1] == start:
        route_without_return = route_without_return[:-1]

    points = []
    seen = set()
    for node_id in route_without_return[1:]:
        node_id = int(node_id)
        if node_id == start or node_id in seen:
            continue
        seen.add(node_id)
        points.append(node_id)

    config = {
        "weather": str(row.get("weather", "")).strip().lower(),
        "cargo": str(row.get("cargo", "")).strip().lower(),
    }
    return {
        "start": start,
        "points": points,
        "return_to_start": return_to_start,
        "description": "从 UI 最近一次结果中提取的任务",
    }, config


def parse_bool(value):
    return str(value).strip().lower() in {"true", "1", "yes", "y", "是"}


def save_result(result):
    config = result["config"]
    write_csv(
        RESULT_PATH,
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
            "checked_routes",
            "checked_states",
            "checked_transitions",
            "runtime_seconds",
            "source",
        ],
        [{
            "algorithm": result["algorithm"],
            "weather": config["weather"],
            "cargo": config["cargo"],
            "route_ids": json.dumps(result["route"], ensure_ascii=False, separators=(",", ":")),
            "route_names": result["route_names"],
            "drive_time": f"{result['drive_time']:.2f}",
            "delay_time": f"{result['delay_time']:.2f}",
            "total_time": f"{result['total_time']:.2f}",
            "delayed_nodes": result["delayed_nodes"],
            "return_to_start": str(result["return_to_start"]).lower(),
            "checked_routes": result["checked_routes"],
            "checked_states": result["checked_states"],
            "checked_transitions": result["checked_transitions"],
            "runtime_seconds": f"{result['runtime_seconds']:.6f}",
            "source": result["source"],
        }],
    )


def main():
    args = parse_args()
    task, _config, source_name = load_task_and_config(args.source)
    point_count = len(task["points"])
    factorial = math.factorial(point_count)
    state_upper_bound = (2 ** point_count) * max(point_count, 1)
    print(f"配送点数量: {point_count}")
    print(f"任务来源: {source_name}")
    print(f"等价全排列路线数: {factorial}")
    print(f"DP 状态规模上界约: {state_upper_bound}")
    print("说明: exact_dp 使用状态压缩动态规划求小规模精确最优解。")
    print()

    result = run_exact_dp(max_points=args.max_points, source=args.source)
    print("精确最优对照结果:")
    print(f"路线: {result['route_names']}")
    print(f"行驶时间: {result['drive_time']:.2f} min")
    print(f"停留时间: {result['delay_time']:.2f} min")
    print(f"总时间: {result['total_time']:.2f} min")
    print(f"等价全排列路线数: {result['checked_routes']}")
    print(f"访问 DP 状态数: {result['checked_states']}")
    print(f"状态转移次数: {result['checked_transitions']}")
    print(f"运行时间: {result['runtime_seconds']:.4f} s")
    print(f"结果文件: {RESULT_PATH}")


def parse_args():
    parser = argparse.ArgumentParser(description="小规模配送任务精确最优解对照")
    parser.add_argument(
        "--source",
        choices=["auto", "ui", "task"],
        default="auto",
        help="任务来源：auto 优先读取 UI 最近一次结果；ui 强制读取 UI；task 使用 delivery_task.json。",
    )
    parser.add_argument(
        "--max-points",
        type=int,
        default=12,
        help="允许精确 DP 处理的最大配送点数量。",
    )
    return parser.parse_args()


if __name__ == "__main__":
    main()

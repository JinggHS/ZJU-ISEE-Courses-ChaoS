# -*- coding: utf-8 -*-
"""
Tkinter 桌面 UI：浙大跑腿哥校园配送路径规划系统

放置位置：src/interface/planner_ui.py
运行方式：python src/interface/planner_ui.py

功能：
1. 选择起点、多个配送点、是否回到起点；
2. 选择天气、货物类型、算法；
3. 调用现有 context_cost_model / route_common / algorithms / visualization 模块；
4. 在界面中展示结果表、静态路线图、拓扑路线图和 GIF 动画。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import tkinter as tk
from tkinter import messagebox, ttk

try:
    from PIL import Image, ImageSequence, ImageTk
    PIL_AVAILABLE = True
except Exception:  # pragma: no cover
    Image = None
    ImageSequence = None
    ImageTk = None
    PIL_AVAILABLE = False


# -----------------------------------------------------------------------------
# 路径与项目模块导入
# -----------------------------------------------------------------------------
THIS_FILE = Path(__file__).resolve()
SRC_DIR = THIS_FILE.parents[1]
ROOT_DIR = SRC_DIR.parent
DATA_DIR = ROOT_DIR / "data"
RESULTS_DIR = ROOT_DIR / "results"
ROUTE_DIR = ROOT_DIR / "route"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

try:
    from algorithms import ant_colony, greedy, simulated_annealing
    from context_cost_model import generate_context_outputs, save_context_config
    from route_common import (
        CONTEXT_COST_MATRIX_PATH,
        CONTEXT_PATH_MATRIX_PATH,
        evaluate_route,
        format_route_names,
        load_cost_matrix,
        load_delivery_task,
        load_node_delay,
        load_nodes,
        load_path_matrix,
        write_csv,
    )
    from visualization.visualize_route_animation import visualize_from_route
except Exception as exc:  # pragma: no cover
    raise RuntimeError(
        "无法导入项目模块。请确认本文件放在 src/interface/planner_ui.py，"
        "并从项目根目录运行：python src/interface/planner_ui.py"
    ) from exc


# -----------------------------------------------------------------------------
# 常量
# -----------------------------------------------------------------------------
WEATHER_LABELS = {
    "sunny": "sunny 晴天",
    "rainy": "rainy 下雨天",
    "hot": "hot 大热天",
}

WEATHER_DESCRIPTIONS = {
    "sunny": "晴天：正常速度",
    "rainy": "下雨天：平地减速20%，下坡减速40%，上坡不变",
    "hot": "大热天：平地减速10%，上坡减速25%，下坡不变",
}

CARGO_LABELS = {
    "small": "small 小货物",
    "medium": "medium 中货物",
    "heavy": "heavy 重货物",
}

CARGO_DESCRIPTIONS = {
    "small": "小货物：上坡、下坡、平地都不变",
    "medium": "中货物：上坡减速20%，下坡和平地不变",
    "heavy": "重货物：上坡减速50%，下坡减速20%，平地不变",
}

ALGORITHM_LABELS = {
    "greedy": "greedy 贪心算法",
    "simulated_annealing": "simulated_annealing 模拟退火",
    "ant_colony": "ant_colony 蚁群算法",
    "all": "all 三种算法对比",
}

ALGORITHM_SOLVERS = {
    "greedy": greedy.solve,
    "simulated_annealing": simulated_annealing.solve,
    "ant_colony": ant_colony.solve,
}

INTERACTIVE_RESULT_PATH = RESULTS_DIR / "interactive_result.csv"
COMPARISON_RESULT_PATH = RESULTS_DIR / "algorithm_comparison_context.csv"

FONT_FAMILY = "Microsoft YaHei UI"
APP_BG = "#f4f7fb"
PANEL_BG = "#ffffff"
CARD_BG = "#fbfdff"
TEXT_COLOR = "#1f2937"
MUTED_COLOR = "#64748b"
PRIMARY_COLOR = "#2563eb"
PRIMARY_ACTIVE = "#1d4ed8"
BORDER_COLOR = "#d8e2ee"
SELECTION_BG = "#dbeafe"


# -----------------------------------------------------------------------------
# UI 样式
# -----------------------------------------------------------------------------
def configure_app_style(root: tk.Tk):
    root.configure(bg=APP_BG)
    root.option_add("*Font", f"{{{FONT_FAMILY}}} 10")
    root.option_add("*TCombobox*Listbox.font", f"{{{FONT_FAMILY}}} 10")
    root.option_add("*selectBackground", SELECTION_BG)
    root.option_add("*selectForeground", TEXT_COLOR)

    style = ttk.Style(root)
    try:
        if "clam" in style.theme_names():
            style.theme_use("clam")
        elif "vista" in style.theme_names():
            style.theme_use("vista")
    except Exception:
        pass

    style.configure(".", font=(FONT_FAMILY, 10), background=PANEL_BG, foreground=TEXT_COLOR)
    style.configure("App.TFrame", background=APP_BG)
    style.configure("Panel.TFrame", background=PANEL_BG)
    style.configure("Card.TFrame", background=CARD_BG)
    style.configure("TLabel", background=PANEL_BG, foreground=TEXT_COLOR)
    style.configure("Title.TLabel", background=PANEL_BG, foreground=TEXT_COLOR, font=(FONT_FAMILY, 18, "bold"))
    style.configure("Field.TLabel", background=PANEL_BG, foreground=TEXT_COLOR, font=(FONT_FAMILY, 10, "bold"))
    style.configure("Muted.TLabel", background=PANEL_BG, foreground=MUTED_COLOR, font=(FONT_FAMILY, 9))
    style.configure("Status.TLabel", background=PANEL_BG, foreground=PRIMARY_ACTIVE, font=(FONT_FAMILY, 10, "bold"))
    style.configure("Image.TLabel", background=CARD_BG, foreground=MUTED_COLOR, font=(FONT_FAMILY, 12))

    style.configure("TButton", font=(FONT_FAMILY, 10), padding=(12, 7), background="#eef2f7")
    style.map(
        "TButton",
        background=[("active", "#e2e8f0"), ("pressed", "#cbd5e1")],
        foreground=[("disabled", "#94a3b8")],
    )
    style.configure("Accent.TButton", font=(FONT_FAMILY, 10, "bold"), padding=(12, 7), background=PRIMARY_COLOR, foreground="#ffffff")
    style.map(
        "Accent.TButton",
        background=[("active", PRIMARY_ACTIVE), ("pressed", "#1e40af"), ("disabled", "#93c5fd")],
        foreground=[("active", "#ffffff"), ("pressed", "#ffffff"), ("disabled", "#f8fafc")],
    )

    style.configure("TCombobox", padding=(8, 5), fieldbackground="#ffffff", background="#ffffff", foreground=TEXT_COLOR)
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", "#ffffff"), ("focus", "#ffffff")],
        foreground=[("readonly", TEXT_COLOR), ("focus", TEXT_COLOR)],
        selectbackground=[("readonly", SELECTION_BG), ("focus", SELECTION_BG)],
        selectforeground=[("readonly", TEXT_COLOR), ("focus", TEXT_COLOR)],
    )
    style.configure("TCheckbutton", background=PANEL_BG, foreground=TEXT_COLOR, font=(FONT_FAMILY, 10))

    style.configure("TNotebook", background=APP_BG, borderwidth=0, tabmargins=(2, 2, 2, 0))
    style.configure("TNotebook.Tab", font=(FONT_FAMILY, 10), padding=(16, 8), background="#e8eef7", foreground=MUTED_COLOR)
    style.map(
        "TNotebook.Tab",
        background=[("selected", PANEL_BG), ("active", "#f1f5f9")],
        foreground=[("selected", TEXT_COLOR), ("active", TEXT_COLOR)],
    )

    style.configure(
        "Treeview",
        background="#ffffff",
        fieldbackground="#ffffff",
        foreground=TEXT_COLOR,
        rowheight=30,
        borderwidth=0,
        font=(FONT_FAMILY, 10),
    )
    style.configure(
        "Treeview.Heading",
        background="#edf2f7",
        foreground=TEXT_COLOR,
        font=(FONT_FAMILY, 10, "bold"),
        padding=(8, 6),
    )
    style.map("Treeview", background=[("selected", SELECTION_BG)], foreground=[("selected", TEXT_COLOR)])


# -----------------------------------------------------------------------------
# 服务层：给 UI 调用的非交互规划函数
# -----------------------------------------------------------------------------
def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _json_route(route: List[int]) -> str:
    return json.dumps(route, ensure_ascii=False, separators=(",", ":"))


def _normalize_name(text: Any) -> str:
    return str(text).strip()


def resolve_node_id(value: Any, nodes: Dict[int, Dict[str, str]]) -> int:
    """把节点编号、'2 菜鸟驿站'、'菜鸟驿站' 都解析成 int 节点编号。"""
    text = _normalize_name(value)
    if not text:
        raise ValueError("节点输入为空。")

    first = text.split()[0]
    if first.isdigit():
        node_id = int(first)
        if node_id not in nodes:
            raise ValueError(f"节点编号 {node_id} 不存在。")
        return node_id

    # 允许输入完整显示项，例如“2 菜鸟驿站”里中文前面带编号的情况已经处理；这里处理纯中文名
    matches = [node_id for node_id, row in nodes.items() if row.get("name", "").strip() == text]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise ValueError(f"地点名 {text!r} 对应多个节点，请改用节点编号。")

    # 宽松匹配：输入中包含地点名
    loose = [node_id for node_id, row in nodes.items() if row.get("name", "").strip() in text]
    if len(loose) == 1:
        return loose[0]

    raise ValueError(f"无法识别节点：{text}")


def deduplicate_points(start: int, points: List[int]) -> List[int]:
    result = []
    seen = set()
    for point in points:
        if point == start:
            continue
        if point in seen:
            continue
        seen.add(point)
        result.append(point)
    return result


def result_to_row(result: Dict[str, Any], weather: str, cargo: str, nodes: Dict[int, Dict[str, str]]) -> Dict[str, str]:
    return {
        "algorithm": str(result["algorithm"]),
        "weather": weather,
        "cargo": cargo,
        "route_ids": _json_route(result["route"]),
        "route_names": format_route_names(result["route"], nodes, return_to_start=False),
        "drive_time": f"{_safe_float(result.get('drive_time')):.2f}",
        "delay_time": f"{_safe_float(result.get('delay_time')):.2f}",
        "total_time": f"{_safe_float(result.get('total_time')):.2f}",
        "delayed_nodes": str(result.get("delayed_nodes", "")),
        "return_to_start": str(bool(result.get("return_to_start", False))).lower(),
    }


def run_one_algorithm(
    algorithm: str,
    start: int,
    points: List[int],
    return_to_start: bool,
    cost_matrix: Dict[Tuple[int, int], float],
    path_matrix: Dict[Tuple[int, int], List[int]],
    node_delay: Dict[int, Dict[str, Any]],
    nodes: Dict[int, Dict[str, str]],
) -> Dict[str, Any]:
    if algorithm not in ALGORITHM_SOLVERS:
        raise ValueError(f"未知算法：{algorithm}")

    solved = ALGORITHM_SOLVERS[algorithm](
        start,
        points,
        cost_matrix,
        return_to_start=return_to_start,
        path_matrix=path_matrix,
        node_delay=node_delay,
        nodes=nodes,
    )

    evaluated = evaluate_route(
        solved["route"],
        cost_matrix,
        path_matrix,
        node_delay,
        nodes,
        return_to_start,
    )

    return {
        "algorithm": solved.get("algorithm", algorithm),
        "route": evaluated["route"],
        "history": solved.get("history", []),
        "drive_time": evaluated["drive_time"],
        "delay_time": evaluated["delay_time"],
        "total_time": evaluated["total_time"],
        "delayed_nodes": evaluated["delayed_nodes"],
        "triggered": evaluated.get("triggered", []),
        "return_to_start": return_to_start,
    }


def plan_route_from_ui(
    start: Any,
    points: List[Any],
    return_to_start: bool,
    weather: str,
    cargo: str,
    algorithm: str,
    generate_visualization: bool = True,
) -> Dict[str, Any]:
    """UI 专用非交互接口。"""
    try:
        nodes = load_nodes()
        start_id = resolve_node_id(start, nodes)
        point_ids = [resolve_node_id(point, nodes) for point in points]
        point_ids = deduplicate_points(start_id, point_ids)
        if not point_ids:
            raise ValueError("请至少选择一个不等于起点的配送点。")

        weather = str(weather).strip().lower()
        cargo = str(cargo).strip().lower()
        algorithm = str(algorithm).strip().lower()
        if weather not in WEATHER_LABELS:
            raise ValueError(f"天气类型非法：{weather}")
        if cargo not in CARGO_LABELS:
            raise ValueError(f"货物类型非法：{cargo}")
        if algorithm not in {"greedy", "simulated_annealing", "ant_colony", "all"}:
            raise ValueError(f"算法类型非法：{algorithm}")

        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        ROUTE_DIR.mkdir(parents=True, exist_ok=True)

        config = save_context_config(weather, cargo, description=f"UI选择场景：{weather} + {cargo}")
        generate_context_outputs(config, verbose=False)

        cost_matrix = load_cost_matrix(CONTEXT_COST_MATRIX_PATH)
        path_matrix = load_path_matrix(CONTEXT_PATH_MATRIX_PATH)
        node_delay = load_node_delay()

        selected_algorithms = list(ALGORITHM_SOLVERS.keys()) if algorithm == "all" else [algorithm]
        results = [
            run_one_algorithm(
                name,
                start_id,
                point_ids,
                return_to_start,
                cost_matrix,
                path_matrix,
                node_delay,
                nodes,
            )
            for name in selected_algorithms
        ]
        best = min(results, key=lambda item: item["total_time"])

        fieldnames = [
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
        ]
        write_csv(INTERACTIVE_RESULT_PATH, fieldnames, [result_to_row(best, weather, cargo, nodes)])
        if algorithm == "all":
            write_csv(COMPARISON_RESULT_PATH, fieldnames, [result_to_row(item, weather, cargo, nodes) for item in results])

        output_files: Dict[str, Optional[str]] = {
            "csv": str(INTERACTIVE_RESULT_PATH),
            "comparison_csv": str(COMPARISON_RESULT_PATH) if algorithm == "all" else None,
            "map_image": None,
            "topology_image": None,
            "gif": None,
        }
        visualization_error = ""
        if generate_visualization:
            try:
                route_files = visualize_from_route(
                    best["route"],
                    path_matrix,
                    {
                        "algorithm": best["algorithm"],
                        "weather": weather,
                        "cargo": cargo,
                        "drive_time": best["drive_time"],
                        "delay_time": best["delay_time"],
                        "total_time": best["total_time"],
                    },
                    nodes,
                    return_to_start=return_to_start,
                )
                output_files.update({key: str(value) for key, value in route_files.items()})
                # 兼容 wrapper 返回的 key 名
                output_files["map_image"] = str(route_files.get("map", output_files.get("map_image")))
                output_files["topology_image"] = str(route_files.get("topology", output_files.get("topology_image")))
                output_files["gif"] = str(route_files.get("animation", output_files.get("gif")))
            except Exception as exc:
                visualization_error = f"可视化生成失败：{exc}"

        return {
            "success": True,
            "message": "规划完成" if not visualization_error else f"规划完成，但{visualization_error}",
            "task": {
                "start": start_id,
                "points": point_ids,
                "return_to_start": return_to_start,
                "weather": weather,
                "cargo": cargo,
                "algorithm": algorithm,
            },
            "best_algorithm": best["algorithm"],
            "results": results,
            "selected_result": best,
            "output_files": output_files,
            "visualization_error": visualization_error,
        }
    except Exception as exc:
        return {
            "success": False,
            "message": str(exc),
            "traceback": traceback.format_exc(),
        }


# -----------------------------------------------------------------------------
# 图片和 GIF 显示工具
# -----------------------------------------------------------------------------
def load_resized_photo(path: str | Path, max_width: int, max_height: int):
    if not PIL_AVAILABLE:
        raise RuntimeError("Pillow 未安装，无法显示图片。请运行：pip install pillow")
    image_path = Path(path)
    if not image_path.exists():
        raise FileNotFoundError(f"图片不存在：{image_path}")
    image = Image.open(image_path).convert("RGB")
    width, height = image.size
    if width <= 0 or height <= 0:
        raise ValueError(f"图片尺寸非法：{image_path}")
    ratio = min(max_width / width, max_height / height)
    new_size = (max(1, int(width * ratio)), max(1, int(height * ratio)))
    image = image.resize(new_size, Image.LANCZOS)
    return ImageTk.PhotoImage(image)


class GifPlayer:
    def __init__(self, label: ttk.Label):
        self.label = label
        self.frames: List[Any] = []
        self.index = 0
        self.after_id: Optional[str] = None
        self.delay_ms = 80

    def stop(self):
        if self.after_id is not None:
            try:
                self.label.after_cancel(self.after_id)
            except Exception:
                pass
        self.after_id = None
        self.frames = []
        self.index = 0

    def load(self, path: str | Path, max_width: int, max_height: int):
        self.stop()
        if not PIL_AVAILABLE:
            raise RuntimeError("Pillow 未安装，无法播放 GIF。请运行：pip install pillow")
        gif_path = Path(path)
        if not gif_path.exists():
            raise FileNotFoundError(f"GIF 不存在：{gif_path}")

        image = Image.open(gif_path)
        frames = []
        duration = image.info.get("duration", 80)
        self.delay_ms = max(40, int(duration or 80))
        for frame in ImageSequence.Iterator(image):
            frame = frame.convert("RGB")
            width, height = frame.size
            ratio = min(max_width / width, max_height / height)
            new_size = (max(1, int(width * ratio)), max(1, int(height * ratio)))
            frame = frame.resize(new_size, Image.LANCZOS)
            frames.append(ImageTk.PhotoImage(frame))

        if not frames:
            raise RuntimeError(f"GIF 没有可播放帧：{gif_path}")
        self.frames = frames
        self.index = 0
        self._play()

    def _play(self):
        if not self.frames:
            return
        frame = self.frames[self.index]
        self.label.configure(image=frame, text="")
        self.label.image = frame
        self.index = (self.index + 1) % len(self.frames)
        self.after_id = self.label.after(self.delay_ms, self._play)


# -----------------------------------------------------------------------------
# Tkinter UI
# -----------------------------------------------------------------------------
class PlannerUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("浙大跑腿哥：校园配送路径规划系统")
        self.root.geometry("1500x950")
        self.root.minsize(1180, 760)
        self._is_fullscreen = False

        self.nodes = load_nodes()
        try:
            self.default_task = load_delivery_task()
        except Exception:
            first_id = sorted(self.nodes)[0]
            self.default_task = {"start": first_id, "points": [], "return_to_start": False, "description": ""}

        self.node_items = self._build_node_items(include_all=True)
        self.delivery_items = self._build_node_items(include_all=False)
        self.display_to_id = {label: node_id for label, node_id in self.node_items}
        self.delivery_display_to_id = {label: node_id for label, node_id in self.delivery_items}

        self.current_image_paths = {"map": None, "topology": None, "gif": None}
        self.map_photo = None
        self.topology_photo = None
        self.gif_player = None

        self._build_widgets()
        self._load_defaults()
        self.root.after(0, self._maximize_window)
        self.root.bind("<F11>", self._toggle_fullscreen)
        self.root.bind("<Escape>", self._exit_fullscreen)

    def _maximize_window(self):
        try:
            self.root.state("zoomed")
        except Exception:
            width = self.root.winfo_screenwidth()
            height = self.root.winfo_screenheight()
            self.root.geometry(f"{width}x{height}+0+0")

    def _toggle_fullscreen(self, _event=None):
        self._is_fullscreen = not self._is_fullscreen
        self.root.attributes("-fullscreen", self._is_fullscreen)

    def _exit_fullscreen(self, _event=None):
        if self._is_fullscreen:
            self._is_fullscreen = False
            self.root.attributes("-fullscreen", False)

    def _bind_combobox_readability(self, combo: ttk.Combobox):
        def clear_selection(_event=None):
            self.root.after_idle(lambda: self._clear_combobox_selection(combo))

        combo.bind("<FocusIn>", clear_selection, add="+")
        combo.bind("<ButtonRelease-1>", clear_selection, add="+")
        combo.bind("<<ComboboxSelected>>", clear_selection, add="+")

    @staticmethod
    def _clear_combobox_selection(combo: ttk.Combobox):
        try:
            combo.selection_clear()
            combo.icursor(tk.END)
        except tk.TclError:
            pass

    def _build_node_items(self, include_all: bool) -> List[Tuple[str, int]]:
        items = []
        for node_id in sorted(self.nodes):
            row = self.nodes[node_id]
            is_delivery = str(row.get("is_delivery", "0")).strip() in {"1", "true", "True", "yes"}
            if include_all or is_delivery:
                items.append((f"{node_id} {row.get('name', '')}", node_id))
        return items

    def _build_widgets(self):
        self.root.configure(bg=APP_BG)
        self.root.columnconfigure(0, weight=0)
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)

        self.left = ttk.Frame(self.root, padding=20, style="Panel.TFrame")
        self.left.grid(row=0, column=0, sticky="ns", padx=(18, 10), pady=18)
        self.left.configure(width=380)

        self.right = ttk.Frame(self.root, padding=(0, 18, 18, 18), style="App.TFrame")
        self.right.grid(row=0, column=1, sticky="nsew")
        self.right.columnconfigure(0, weight=1)
        self.right.rowconfigure(0, weight=1)

        title = ttk.Label(self.left, text="参数设置", style="Title.TLabel")
        title.grid(row=0, column=0, sticky="w", pady=(0, 16))

        ttk.Label(self.left, text="起点", style="Field.TLabel").grid(row=1, column=0, sticky="w")
        self.start_var = tk.StringVar()
        self.start_combo = ttk.Combobox(
            self.left,
            textvariable=self.start_var,
            values=[label for label, _node_id in self.node_items],
            width=30,
            state="readonly",
        )
        self.start_combo.grid(row=2, column=0, sticky="ew", pady=(4, 14))
        self._bind_combobox_readability(self.start_combo)

        ttk.Label(self.left, text="配送点（Ctrl / Shift 多选）", style="Field.TLabel").grid(row=3, column=0, sticky="w")
        list_frame = ttk.Frame(self.left, style="Panel.TFrame")
        list_frame.grid(row=4, column=0, sticky="nsew", pady=(4, 14))
        self.left.rowconfigure(4, weight=1)
        self.point_listbox = tk.Listbox(
            list_frame,
            selectmode=tk.EXTENDED,
            height=12,
            exportselection=False,
            relief="flat",
            borderwidth=0,
            highlightthickness=1,
            highlightbackground=BORDER_COLOR,
            highlightcolor=PRIMARY_COLOR,
            bg=CARD_BG,
            fg=TEXT_COLOR,
            selectbackground=SELECTION_BG,
            selectforeground=TEXT_COLOR,
            activestyle="none",
            font=(FONT_FAMILY, 10),
        )
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.point_listbox.yview)
        self.point_listbox.configure(yscrollcommand=scrollbar.set)
        self.point_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        for label, _node_id in self.delivery_items:
            self.point_listbox.insert(tk.END, label)

        self.return_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(self.left, text="完成后回到起点", variable=self.return_var).grid(
            row=5, column=0, sticky="w", pady=(0, 14)
        )

        ttk.Label(self.left, text="天气", style="Field.TLabel").grid(row=6, column=0, sticky="w")
        self.weather_var = tk.StringVar(value="sunny")
        self.weather_combo = ttk.Combobox(
            self.left,
            textvariable=self.weather_var,
            values=list(WEATHER_LABELS.values()),
            state="readonly",
            width=30,
        )
        self.weather_combo.grid(row=7, column=0, sticky="ew", pady=(4, 4))
        self.weather_hint = ttk.Label(self.left, text="", wraplength=330, style="Muted.TLabel")
        self.weather_hint.grid(row=8, column=0, sticky="w", pady=(0, 14))
        self.weather_combo.bind("<<ComboboxSelected>>", lambda _e: self._update_hints())
        self._bind_combobox_readability(self.weather_combo)

        ttk.Label(self.left, text="货物类型", style="Field.TLabel").grid(row=9, column=0, sticky="w")
        self.cargo_var = tk.StringVar(value="small")
        self.cargo_combo = ttk.Combobox(
            self.left,
            textvariable=self.cargo_var,
            values=list(CARGO_LABELS.values()),
            state="readonly",
            width=30,
        )
        self.cargo_combo.grid(row=10, column=0, sticky="ew", pady=(4, 4))
        self.cargo_hint = ttk.Label(self.left, text="", wraplength=330, style="Muted.TLabel")
        self.cargo_hint.grid(row=11, column=0, sticky="w", pady=(0, 14))
        self.cargo_combo.bind("<<ComboboxSelected>>", lambda _e: self._update_hints())
        self._bind_combobox_readability(self.cargo_combo)

        ttk.Label(self.left, text="算法", style="Field.TLabel").grid(row=12, column=0, sticky="w")
        self.algorithm_var = tk.StringVar(value=ALGORITHM_LABELS["all"])
        self.algorithm_combo = ttk.Combobox(
            self.left,
            textvariable=self.algorithm_var,
            values=list(ALGORITHM_LABELS.values()),
            state="readonly",
            width=30,
        )
        self.algorithm_combo.grid(row=13, column=0, sticky="ew", pady=(4, 14))
        self._bind_combobox_readability(self.algorithm_combo)

        self.progress_var = tk.StringVar(value="就绪")
        ttk.Label(self.left, textvariable=self.progress_var, style="Status.TLabel").grid(
            row=14, column=0, sticky="w", pady=(0, 10)
        )

        button_frame = ttk.Frame(self.left, style="Panel.TFrame")
        button_frame.grid(row=15, column=0, sticky="ew")
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        self.run_button = ttk.Button(button_frame, text="开始规划", command=self.on_run, style="Accent.TButton")
        self.run_button.grid(row=0, column=0, sticky="ew", padx=(0, 5), pady=4)
        ttk.Button(button_frame, text="清空选择", command=self.clear_selection).grid(row=0, column=1, sticky="ew", padx=(5, 0), pady=4)
        ttk.Button(button_frame, text="打开输出文件夹", command=self.open_output_folder).grid(row=1, column=0, sticky="ew", padx=(0, 5), pady=4)
        ttk.Button(button_frame, text="退出", command=self.root.destroy).grid(row=1, column=1, sticky="ew", padx=(5, 0), pady=4)

        self.notebook = ttk.Notebook(self.right)
        self.notebook.grid(row=0, column=0, sticky="nsew")

        self.summary_text = self._add_text_tab("结果摘要")
        self.comparison_tree = self._add_comparison_tab("算法对比")
        self.map_label = self._add_image_tab("校园地图路线")
        self.topology_label = self._add_image_tab("拓扑图路线")
        self.gif_label = self._add_image_tab("动态路线 GIF")
        self.gif_player = GifPlayer(self.gif_label)
        self.log_text = self._add_text_tab("日志")

        self.root.bind("<Configure>", self._on_resize)

    def _add_text_tab(self, title: str) -> tk.Text:
        frame = ttk.Frame(self.notebook, padding=12, style="Panel.TFrame")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        text = tk.Text(
            frame,
            wrap="word",
            font=(FONT_FAMILY, 10),
            bg="#ffffff",
            fg=TEXT_COLOR,
            insertbackground=TEXT_COLOR,
            relief="flat",
            borderwidth=0,
            highlightthickness=1,
            highlightbackground=BORDER_COLOR,
            highlightcolor=PRIMARY_COLOR,
            padx=12,
            pady=10,
        )
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=text.yview)
        text.configure(yscrollcommand=scrollbar.set)
        text.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.notebook.add(frame, text=title)
        return text

    def _add_comparison_tab(self, title: str) -> ttk.Treeview:
        frame = ttk.Frame(self.notebook, padding=12, style="Panel.TFrame")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        columns = ("algorithm", "route", "drive", "delay", "total", "delayed")
        tree = ttk.Treeview(frame, columns=columns, show="headings")
        headings = {
            "algorithm": "算法",
            "route": "路线",
            "drive": "行驶时间",
            "delay": "停留时间",
            "total": "总时间",
            "delayed": "触发停留点",
        }
        widths = {
            "algorithm": 130,
            "route": 420,
            "drive": 90,
            "delay": 90,
            "total": 90,
            "delayed": 220,
        }
        for col in columns:
            tree.heading(col, text=headings[col])
            tree.column(col, width=widths[col], anchor="w")
        ybar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        xbar = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=ybar.set, xscrollcommand=xbar.set)
        tree.grid(row=0, column=0, sticky="nsew")
        ybar.grid(row=0, column=1, sticky="ns")
        xbar.grid(row=1, column=0, sticky="ew")
        self.notebook.add(frame, text=title)
        return tree

    def _add_image_tab(self, title: str) -> ttk.Label:
        frame = ttk.Frame(self.notebook, padding=12, style="Panel.TFrame")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        label = ttk.Label(frame, text="尚未生成", anchor="center", style="Image.TLabel")
        label.grid(row=0, column=0, sticky="nsew")
        self.notebook.add(frame, text=title)
        return label

    def _load_defaults(self):
        start_id = self.default_task.get("start")
        for label, node_id in self.node_items:
            if node_id == start_id:
                self.start_var.set(label)
                break
        default_points = set(self.default_task.get("points", []))
        for i, (_label, node_id) in enumerate(self.delivery_items):
            if node_id in default_points:
                self.point_listbox.selection_set(i)
        self.return_var.set(bool(self.default_task.get("return_to_start", False)))
        self.weather_var.set(WEATHER_LABELS["sunny"])
        self.cargo_var.set(CARGO_LABELS["small"])
        self.algorithm_var.set(ALGORITHM_LABELS["all"])
        self._update_hints()

    def _update_hints(self):
        weather = self._selected_key(self.weather_var.get(), WEATHER_LABELS)
        cargo = self._selected_key(self.cargo_var.get(), CARGO_LABELS)
        self.weather_hint.configure(text=WEATHER_DESCRIPTIONS.get(weather, ""))
        self.cargo_hint.configure(text=CARGO_DESCRIPTIONS.get(cargo, ""))

    @staticmethod
    def _selected_key(label: str, label_map: Dict[str, str]) -> str:
        for key, value in label_map.items():
            if label == value or label.startswith(key):
                return key
        return next(iter(label_map))

    def selected_start(self) -> int:
        value = self.start_var.get()
        if not value:
            raise ValueError("请选择起点。")
        return self.display_to_id[value]

    def selected_points(self) -> List[int]:
        selected_indices = list(self.point_listbox.curselection())
        if not selected_indices:
            raise ValueError("请至少选择一个配送点。")
        return [self.delivery_items[i][1] for i in selected_indices]

    def clear_selection(self):
        self.point_listbox.selection_clear(0, tk.END)
        self.return_var.set(False)
        self.progress_var.set("已清空配送点选择")

    def open_output_folder(self):
        folder = ROUTE_DIR if ROUTE_DIR.exists() else ROOT_DIR
        try:
            if sys.platform.startswith("win"):
                os.startfile(str(folder))  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(folder)])
            else:
                subprocess.Popen(["xdg-open", str(folder)])
        except Exception as exc:
            messagebox.showerror("打开失败", str(exc))

    def log(self, message: str):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    def on_run(self):
        try:
            start = self.selected_start()
            points = self.selected_points()
            return_to_start = bool(self.return_var.get())
            weather = self._selected_key(self.weather_var.get(), WEATHER_LABELS)
            cargo = self._selected_key(self.cargo_var.get(), CARGO_LABELS)
            algorithm = self._selected_key(self.algorithm_var.get(), ALGORITHM_LABELS)
            points = deduplicate_points(start, points)
            if not points:
                raise ValueError("配送点不能只包含起点。")
        except Exception as exc:
            messagebox.showerror("输入错误", str(exc))
            return

        self.run_button.configure(state="disabled")
        self.progress_var.set("正在计算，请稍候...")
        self.log("开始规划...")
        self.log(f"起点: {start}; 配送点: {points}; 天气: {weather}; 货物: {cargo}; 算法: {algorithm}")

        def worker():
            result = plan_route_from_ui(
                start=start,
                points=points,
                return_to_start=return_to_start,
                weather=weather,
                cargo=cargo,
                algorithm=algorithm,
                generate_visualization=True,
            )
            self.root.after(0, lambda: self.on_result(result))

        threading.Thread(target=worker, daemon=True).start()

    def on_result(self, result: Dict[str, Any]):
        self.run_button.configure(state="normal")
        if not result.get("success"):
            self.progress_var.set("规划失败")
            self.log("规划失败：" + str(result.get("message", "未知错误")))
            if result.get("traceback"):
                self.log(result["traceback"])
            messagebox.showerror("规划失败", str(result.get("message", "未知错误")))
            return

        self.progress_var.set("规划完成")
        self.log(str(result.get("message", "规划完成")))
        self.update_summary(result)
        self.update_comparison(result)
        self.update_images(result)
        self.notebook.select(0)

    def update_summary(self, result: Dict[str, Any]):
        task = result.get("task", {})
        best = result.get("selected_result", {})
        nodes = self.nodes
        start_name = nodes.get(task.get("start"), {}).get("name", task.get("start"))
        point_names = [nodes.get(pid, {}).get("name", str(pid)) for pid in task.get("points", [])]

        content = []
        content.append("当前任务")
        content.append("=" * 60)
        content.append(f"起点：{task.get('start')} {start_name}")
        content.append(f"配送点：{'、'.join(point_names)}")
        content.append(f"天气：{WEATHER_LABELS.get(task.get('weather'), task.get('weather'))}")
        content.append(f"货物：{CARGO_LABELS.get(task.get('cargo'), task.get('cargo'))}")
        content.append(f"算法选择：{ALGORITHM_LABELS.get(task.get('algorithm'), task.get('algorithm'))}")
        content.append(f"是否回到起点：{str(task.get('return_to_start')).lower()}")
        content.append("")
        content.append("推荐结果")
        content.append("=" * 60)
        content.append(f"推荐算法：{best.get('algorithm')}")
        content.append(f"推荐路线：{format_route_names(best.get('route', []), nodes)}")
        content.append(f"行驶时间：{_safe_float(best.get('drive_time')):.2f} min")
        content.append(f"停留时间：{_safe_float(best.get('delay_time')):.2f} min")
        content.append(f"总时间：{_safe_float(best.get('total_time')):.2f} min")
        content.append(f"触发停留惩罚：{best.get('delayed_nodes') or '无'}")
        content.append("")
        content.append("输出文件")
        content.append("=" * 60)
        for key, value in result.get("output_files", {}).items():
            if value:
                content.append(f"{key}: {value}")
        if result.get("visualization_error"):
            content.append("")
            content.append(str(result["visualization_error"]))

        self.summary_text.delete("1.0", tk.END)
        self.summary_text.insert(tk.END, "\n".join(content))

    def update_comparison(self, result: Dict[str, Any]):
        for item in self.comparison_tree.get_children():
            self.comparison_tree.delete(item)
        for row in result.get("results", []):
            route_names = format_route_names(row.get("route", []), self.nodes)
            self.comparison_tree.insert(
                "",
                tk.END,
                values=(
                    row.get("algorithm", ""),
                    route_names,
                    f"{_safe_float(row.get('drive_time')):.2f}",
                    f"{_safe_float(row.get('delay_time')):.2f}",
                    f"{_safe_float(row.get('total_time')):.2f}",
                    row.get("delayed_nodes", ""),
                ),
            )

    def _tab_size_for_label(self, label: ttk.Label) -> Tuple[int, int]:
        # 优先使用右侧 notebook 的实际大小，而不是 label 自己的大小
        width = max(self.notebook.winfo_width(), 1000)
        height = max(self.notebook.winfo_height(), 720)
        return width - 40, height - 60

    def update_images(self, result: Dict[str, Any]):
        files = result.get("output_files", {})
        self.current_image_paths["map"] = files.get("map_image")
        self.current_image_paths["topology"] = files.get("topology_image")
        self.current_image_paths["gif"] = files.get("gif")
        self.refresh_static_images()
        self.refresh_gif()

    def refresh_static_images(self):
        for key, label, attr_name in [
            ("map", self.map_label, "map_photo"),
            ("topology", self.topology_label, "topology_photo"),
        ]:
            path = self.current_image_paths.get(key)
            if not path:
                label.configure(text="路线图尚未生成", image="")
                continue
            try:
                width, height = self._tab_size_for_label(label)
                photo = load_resized_photo(path, width, height)
                setattr(self, attr_name, photo)
                label.configure(image=photo, text="")
            except Exception as exc:
                label.configure(text=f"无法显示图片：\n{path}\n\n{exc}", image="")

    def refresh_gif(self):
        path = self.current_image_paths.get("gif")
        if not path:
            self.gif_label.configure(text="GIF 尚未生成", image="")
            return
        try:
            width, height = self._tab_size_for_label(self.gif_label)
            self.gif_player.load(path, width, height)
        except Exception as exc:
            self.gif_label.configure(text=f"无法播放 GIF：\n{path}\n\n{exc}", image="")

    def _on_resize(self, _event=None):
        # 避免窗口拖动时频繁重读大图，这里只在已有结果时做轻量刷新。
        # 如果 GIF 很大，拖动窗口时不主动重载 GIF。
        pass


# -----------------------------------------------------------------------------
# 主入口
# -----------------------------------------------------------------------------
def main():
    root = tk.Tk()
    configure_app_style(root)

    app = PlannerUI(root)
    if not PIL_AVAILABLE:
        app.log("警告：未检测到 Pillow，路线图和 GIF 可能无法在 UI 内显示。请运行：pip install pillow")
    root.mainloop()


if __name__ == "__main__":
    main()

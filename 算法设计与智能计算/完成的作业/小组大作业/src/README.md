# 玉泉校区跑腿配送路径规划系统

本目录保留当前工程的有效代码，面向最终展示和演示使用。

## 推荐运行方式

启动图形界面：

```bash
python src/interface/planner_ui.py
```

界面支持：

- 选择起点；
- 多选配送点；
- 选择是否回到起点；
- 选择天气；
- 选择货物重量；
- 选择贪心、模拟退火、蚁群或三算法对比；
- 自动生成路线结果、算法对比、地图路线图和 GIF。

## 核心流程

```text
edges_raw.csv + nodes.csv
-> directed_edges.csv
-> cost_matrix.csv + path_matrix.json
-> context_edges.csv
-> context_cost_matrix.csv + context_path_matrix.json
-> 贪心 / 模拟退火 / 蚁群
-> 加入 node_delay
-> 输出结果和路线图
```

## 主要代码文件

```text
src/build_graph.py
  将原始道路边展开为正反两个方向的有向边，并计算基础行驶时间。

src/shortest_path.py
  自己实现的 Dijkstra 最短路算法。

src/generate_matrix.py
  生成基础 cost_matrix.csv 和 path_matrix.json。

src/context_cost_model.py
  根据天气和货物重量重新计算情景边代价与最短路矩阵。

src/route_common.py
  路线代价、路径展开、停留惩罚、CSV 读写等公共函数。

src/algorithms/
  greedy.py：最近邻贪心算法。
  simulated_annealing.py：模拟退火算法。
  ant_colony.py：蚁群算法。
  exact_dp.py：小规模状态压缩 DP 精确最优解对照。

src/interface/planner_ui.py
  Tkinter 图形界面，是当前推荐演示入口。

src/visualize_route_animation.py
src/visualization/visualize_route_animation.py
  路线静态图和 GIF 动画生成。
```

## 主要数据文件

```text
data/nodes.csv
  节点表，包含 1-19 个主要地点和道路辅助节点。

data/edges_raw.csv
  手工整理的道路拓扑边。

data/directed_edges.csv
  自动生成的有向边表。

data/cost_matrix.csv
data/path_matrix.json
  基础最短路矩阵和路径矩阵。

data/context_config.json
  当前天气和货物重量配置。

data/context_edges.csv
data/context_cost_matrix.csv
data/context_path_matrix.json
  当前情景下的边代价、最短路矩阵和路径矩阵。

data/delivery_task.json
  示例配送任务。

data/node_delay.json
  地点停留惩罚配置。
```

图片文件保留在 `data/` 中，用于路线绘制和展示。

## 常用命令

重新生成基础矩阵：

```bash
python src/generate_matrix.py
```

重新生成情景矩阵：

```bash
python src/context_cost_model.py
```

运行小规模精确最优解对照：

```bash
python src/exact_dp_context.py
```

默认会优先读取 `results/interactive_result.csv`，用于验证 UI 最近一次点击规划后的起点、配送点、天气和货物类型。也可以显式指定来源：

```bash
python src/exact_dp_context.py --source ui
python src/exact_dp_context.py --source task
```

其中 `--source ui` 强制验证 UI 最近一次结果，`--source task` 使用 `data/delivery_task.json`。

启动 UI：

```bash
python src/interface/planner_ui.py
```

## 输出文件

```text
results/interactive_result.csv
  当前 UI 推荐路线结果。

results/algorithm_comparison_context.csv
  三种算法对比结果。

results/exact_dp_result_context.csv
  小规模精确最优解对照结果。

route/route_on_yuquan_map.png
route/route_on_topology_slope_check.png
route/route_animation.gif
  路线可视化输出。
```

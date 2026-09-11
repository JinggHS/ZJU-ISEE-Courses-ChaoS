from utils import Board, Player, Record
from utils import opposite, make_state
from typing import Tuple
import json
import math
import os
import random

class Agent:
    def __init__(self, color: Player, algorithm='minimax', max_iter=100):
        """
        Args:
            color (Player): AI 选择的颜色
            algorithm ('minimax' | 'alphabeta' | 'ucb1'): Agent 采取的算法. default: 'minimax'
            max_iter: MCTS 模拟次数. default: 100
        """
        self.color = color
        self.algorithm = algorithm

        # variables for MCTS
        self.max_iter = max_iter
        self.history = {}

        # Optional Alpha-Beta pruning log for reports.
        ab_log = os.environ.get("AB_LOG")
        if ab_log and ab_log.lower() not in ("0", "false", "off"):
            self.ab_log_path = os.environ.get("AB_LOG_FILE")
            if self.ab_log_path is None:
                self.ab_log_path = "alphabeta_pruning.jsonl" if ab_log == "1" else ab_log
        else:
            self.ab_log_path = None

    def _format_board(self, board: Board):
        # 将棋盘转成人类可读的形式，仅用于剪枝日志。
        symbols = {None: ".", 0: "W", 1: "B"}
        return ["".join(symbols[cell] for cell in row) for row in board.board]

    def _log_ab_prune(self, board: Board, player: Player, action, node_type: str,
                      alpha: int, beta: int, value: int, condition: str) -> None:
        if self.ab_log_path is None:
            return
        # 每次剪枝写一行 JSON，便于报告中直接引用具体案例。
        data = {
            "node_type": node_type,
            "player": player,
            "action": action,
            "alpha": alpha,
            "beta": beta,
            "value": value,
            "condition": condition,
            "board": self._format_board(board),
            "state": make_state(board, player),
        }
        with open(self.ab_log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")

    def action(self, board: Board) -> Tuple[int, int]:
        """
        Args:
            board: 棋盘
        Returns:
            action: (x, y). AI决策的落子位置
        """
        best_score = float('-inf')
        best_move = None

        if self.algorithm == 'ucb1':
            # 记录根结点
            self.history = {
                make_state(board, self.color) : Record(board.actions(self.color))
            }
            # MCTS
            for _ in range(self.max_iter):
                self.MCTS(board, self.color)

        for action in board.actions(self.color):
            # 枚举每个可能的落子方式，并获取最佳的落子方式
            if self.algorithm == 'minimax':
                score = self.minimax(board.result(action, self.color), opposite(self.color))
            elif self.algorithm == 'alphabeta':
                # 将已知的最好结果作为 alpha 值传下去，加速后续分支的剪枝
                alpha_val = max(best_score, -1) if best_score != float('-inf') else -1
                score = self.alphabeta(board.result(action, self.color), opposite(self.color), alpha=alpha_val, beta=1)
            elif self.algorithm == 'ucb1':
                # 根据历史信息计算行动的平均效用
                score = self.ucb1(board, self.color, action, real=True)
            else:
                raise NotImplementedError
                
            if score >= best_score:
                best_move = action
                best_score = score
                
            # 根节点提前终止：如果已经找到必胜的走法，直接停止搜索
            if (self.algorithm in ['minimax', 'alphabeta']) and best_score >= 1:
                break

        if best_move is None:
            raise ValueError
        return best_move

    def minimax(self, board: Board, player: Player) -> int:
        """
        Minmax 算法
        Args:
            board: 棋盘
            player: 棋盘的落子方
        Returns:
            score: 算法决策计算得到效用
        """
        if board.terminated():
            # 到达终止状态，计算对应的效用函数
            return board.utility(self.color)

        # 计算每个落子方式对应的回报
        scores = [self.minimax(board.result(action, player), opposite(player))
                  for action in board.actions(player)]

        # 根据当前的行动方，决定取这些回报中的最大值还是最小值
        if player == self.color:
            return max(scores)
        else:
            return min(scores)

    def alphabeta(self, board: Board, player: Player, alpha: int = -1, beta : int = 1) -> int:
        """
        Alpha-beta 剪枝
        Args:
            board: 棋盘
            player: 当前状态的行动方
            alpha, beta: alpha-beta 区间
        Returns:
            score: 算法决策计算得到效用
        """
        if board.terminated():
            # 终止状态
            return board.utility(self.color)
        # 初始化回报v
        if player == self.color:
            v = alpha
        else:
            v = beta
        # 枚举落子方式
        for action in board.actions(player):
            if player == self.color:
                v = max(v, self.alphabeta(board.result(action, player), opposite(player), alpha, beta))
                if v >= beta:
                    self._log_ab_prune(board, player, action, "max", alpha, beta, v, "value >= beta")
                    # 区间为空，剪枝
                    break
                # 更新区间
                alpha = max(alpha, v)
            else:
                """
                Min node: search children, update beta, and prune when alpha catches beta.
                    请编写合理的代码段。
                    这部分代码将实现Min的情况下的搜索和区间更新。
                Note:
                    请参考Max的情况的实现。
                """
                # Min 层表示对手行动，因此选择使 AI 效用最小的子节点。
                v = min(v, self.alphabeta(board.result(action, player), opposite(player), alpha, beta))
                if v <= alpha:
                    # Min node can prune once Max already has a better option.
                    self._log_ab_prune(board, player, action, "min", alpha, beta, v, "value <= alpha")
                    break
                beta = min(beta, v)
        return v

    def ucb1(self, board: Board, player: Player, action, real=False) -> float:
        """
        UCB1 score
        根据board和player，从历史信息中计算ucb1
        Args:
            board: 棋盘
            player: 落子方
            real: 若为True则直接计算效用均值，若为False则给出UCB1
        Returns:
            score: UCB1 score
        """
        state = make_state(board, player)
        factor = 1 if player == self.color else -1
        if real:
            factor = 0

        if state in self.history:
            record : Record = self.history[state]
            if action in record.actions:
                if real:
                    # 根节点最终决策只看经验平均收益，不再加入探索奖励。
                    return record.average(action)
                action_times = record.times(action)
                if record.n > 0 and action_times > 0:
                    # UCB1 同时考虑利用项（平均收益）和探索项（访问次数奖励）。
                    return record.average(action) + factor * (2 * math.log(record.n) / action_times) ** 0.5
        if real:
            return 0.0
        return float('inf') * factor

    def MCTS(self, board: Board, player: Player, rollout=False) -> int:
        """
        Monte-Carlo Tree Search
        Args:
            board: 当前结点的局面
            player: 当前结点的落子方
            rollout: 快速模拟标记. 若为True则为快速模拟阶段
        Returns:
            score: 返回效用，用于更新结点信息
        """
        if board.terminated():
            return board.utility(self.color)

        if not rollout:
            record = self.history[make_state(board, player)]
            # 未完全展开的结点, Expand
            if len(record.rest_actions) > 0:
                # Expand
                # 选择叶子结点
                action = random.choice(record.rest_actions)
                record.rest_actions.remove(action)
                new_board = board.result(action, player)
                # 注意：在本规则下，博弈树并不严格保证不同分支之间的不相交，可能存在不同的结点指向同一个状态的情况
                new_state = make_state(new_board, opposite(player))
                if new_state not in self.history:
                    self.history[new_state] = Record(new_board.actions(opposite(player)))
                # Rollout
                score = self.MCTS(new_board, opposite(player), rollout=True)
            # 结点完全展开, Select
            else:
                # 根据ucb1选择最佳策略
                """
                Select one expanded child according to UCB1.
                    请编写合理的代码段。
                    这部分代码将实现MCTS的Select部分
                Note:
                    可以通过调用`self.ucb1(board, player, action)`来计算`action`对应的UCB1值
                """
                actions = board.actions(player)
                # MCTS 的收益始终从当前 AI 视角记录：
                # AI 自己行动时取最大，对手行动时取最小。
                if player == self.color:
                    action = max(actions, key=lambda a: self.ucb1(board, player, a))
                else:
                    action = min(actions, key=lambda a: self.ucb1(board, player, a))
                new_board = board.result(action, player)
                new_state = make_state(new_board, opposite(player))
                if new_state not in self.history:
                    self.history[new_state] = Record(new_board.actions(opposite(player)))
                # 选中子节点后，继续向下进行树搜索。
                score = self.MCTS(new_board, opposite(player))

            # Backpropagation
            # 回溯更新历史信息
            state = make_state(board, player)
            # 将模拟得到的效用回传到当前节点所选择的动作上。
            self.history[state].update(score, action)
        else:
            # Rollout
            action = random.choice(board.actions(player))
            new_result = board.result(action, player)
            score = self.MCTS(new_result, opposite(player), rollout=True)
        return score

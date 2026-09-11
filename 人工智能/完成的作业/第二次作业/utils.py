from typing import Literal, Union, Tuple, List
from enum import Enum
import copy
import pdb

WHITE = 0
BLACK = 1
EMPTY = None

type Color = Union[int, None]
type Player = Color


def opposite(player: Player):
    """
    Args:
        player
    Return:
        opposite_player: 根据输入方返回其对手
    """
    if player != None:
        return 1 - player
    else:
        raise ValueError


class Board:
    def __init__(self, board=None):
        if board is None:
            self.board =  [[EMPTY, EMPTY, EMPTY, EMPTY],
                           [EMPTY, WHITE, BLACK, EMPTY],
                           [EMPTY, BLACK, WHITE, EMPTY],
                           [EMPTY, EMPTY, EMPTY, EMPTY]]
        else:
            self.board = copy.deepcopy(board)

    def terminated(self) -> bool:
        """
        判断棋局是否结束
        """
        # 双方都无法下了，游戏结束
        return self.actions(WHITE)[0] == None and self.actions(BLACK)[0] == None

    def actions(self, player: Player) -> List[Tuple[int, int]]:
        """
        给定落子方，返回能够落子的位置
        Args:
            player: 落子方
        Returns:
            actions: 可落子的位置，若轮空则为`[None]`
        """
        ret = []
        for i in range(4):
            for j in range(4):
                if self.board[i][j] == EMPTY:
                    flag = False
                    # 检查落子在此处时，4个方向是否能够引起翻转
                    ## 上
                    if i > 0 and self.board[i - 1][j] == opposite(player):
                        for k in reversed(range(0, i - 1)):
                            if self.board[k][j] == player:
                                ret.append((i, j))
                                flag = True
                                break
                            elif self.board[k][j] == EMPTY:
                                break
                    ## 下
                    if not flag and i < 3 and self.board[i + 1][j] == opposite(player):
                        for k in range(i + 2, 4):
                            if self.board[k][j] == player:
                                ret.append((i, j))
                                flag = True
                                break
                            elif self.board[k][j] == EMPTY:
                                break
                    ## 左
                    """
                    Check whether placing here can flip pieces to the left.
                        请编写合理的代码段。
                        这部分代码将实现水平方向向左的落子检查。
                    Note:
                        请参考竖直方向向上的检查的实现。
                    """
                    if not flag and j > 0 and self.board[i][j - 1] == opposite(player):
                        # 向左合法落子要求：中间夹住至少一个对方棋子，并在更左侧遇到己方棋子。
                        for k in reversed(range(0, j - 1)):
                            if self.board[i][k] == player:
                                ret.append((i, j))
                                flag = True
                                break
                            elif self.board[i][k] == EMPTY:
                                break
                    ## 右
                    """
                    Check whether placing here can flip pieces to the right.
                        请编写合理的代码段。
                        这部分代码将实现水平方向向右的落子检查。
                    Note:
                        请参考竖直方向向下的检查的实现。
                    """
                    if not flag and j < 3 and self.board[i][j + 1] == opposite(player):
                        # 向右合法落子同样要求形成“己方-对方-己方”的夹击结构。
                        for k in range(j + 2, 4):
                            if self.board[i][k] == player:
                                ret.append((i, j))
                                flag = True
                                break
                            elif self.board[i][k] == EMPTY:
                                break

        if len(ret) == 0:
            # Pass
            ret.append(None)
        return ret

    def result(self, pos: Union[None, Tuple[int, int]], player: Player):
        """
        根据落子方和其采取的行动产生对应的新局面
        Args:
            pos: 落子方采取的行动
            player: 落子方
        Returns:
            board: 行动后的新局面
        """
        if pos is None:
            # 轮空
            return Board(copy.deepcopy(self.board))

        x, y = pos
        board = copy.deepcopy(self.board)
        # 对4个方向做翻转
        ## 上
        if x > 0 and board[x - 1][y] == opposite(player):
            for i in reversed(range(0, x - 1)):
                if board[i][y] == player:
                    for j in range(i + 1, x):
                        board[j][y] = player
                    break
                elif board[i][y] == EMPTY:
                    break
        ## 下
        if x < 3 and board[x + 1][y] == opposite(player):
            for i in range(x + 2, 4):
                if board[i][y] == player:
                    for j in range(x + 1, i):
                        board[j][y] = player
                    break
                elif board[i][y] == EMPTY:
                    break
        ## 左
        """
        Flip bracketed pieces to the left after placing a piece.
            请编写合理的代码段。
            这部分代码将实现水平方向向左的翻转。
        Note:
            请参考竖直方向向上的翻转的实现。
        """
        if y > 0 and board[x][y - 1] == opposite(player):
            # 只有左侧最终被己方棋子封闭时，才翻转中间的对方棋子。
            for i in reversed(range(0, y - 1)):
                if board[x][i] == player:
                    for j in range(i + 1, y):
                        board[x][j] = player
                    break
                elif board[x][i] == EMPTY:
                    break

        ## 右

        """
        Flip bracketed pieces to the right after placing a piece.
            请编写合理的代码段。
            这部分代码将实现水平方向向右的翻转。
        Note:
            请参考竖直方向向下的翻转的实现。
        """
        if y < 3 and board[x][y + 1] == opposite(player):
            # 只有右侧最终被己方棋子封闭时，才翻转中间的对方棋子。
            for i in range(y + 2, 4):
                if board[x][i] == player:
                    for j in range(y + 1, i):
                        board[x][j] = player
                    break
                elif board[x][i] == EMPTY:
                    break
        board[x][y] = player
        return Board(board)

    def utility(self, player: Player) -> Literal[-1, 0, 1]:
        """
        效用函数
        Args:
            player: 选择的棋手
        Returns:
            utility: 表示对棋手player而言当前局面的胜负产生的效用值
                - 1: 当前局面player获胜
                - 0: 当前局面为平局
                - -1: 当前局面player告负
        """
        winner = self.winner()
        if winner == player:
            return 1
        if winner == opposite(player):
            return -1
        return 0

    def winner(self) -> Player:
        """
        Returns:
            winner:
                - WHITE 表示白方获胜
                - BLACK 表示黑方获胜
                - EMPTY 表示无人获胜，即平局
        """
        nWhite = 0
        nBlack = 0
        for i in range(4):
            for j in range(4):
                if self.board[i][j] == WHITE:
                    nWhite += 1
                elif self.board[i][j] == BLACK:
                    nBlack += 1
        if nWhite > nBlack:
            return WHITE
        elif nWhite < nBlack:
            return BLACK
        else:
            return EMPTY

    def compact(self) -> str:
        """
        将棋盘转化成字符串的形式，便于在dict中作为key使用
        Returns:
            repr: 一个表示当前棋盘的字符串
        """
        repr = ''
        for i in range(4):
            for j in range(4):
                if self.board[i][j] == EMPTY:
                    repr += 'E'
                elif self.board[i][j] == WHITE:
                    repr += 'W'
                else:
                    repr += 'B'
        return repr


def make_state(board: Board, player: Player):
    """
    根据棋盘和落子方构造一个不可变值，用于表示搜索树的结点状态
    Args:
        board: 棋盘
        player: 落子方
    Returns:
        state: 一个由board和player拼接的表示
    """
    s = (board.compact(), player)
    return s


class Record:
    """
    用于记录结点历史信息的结构体
    Args:
        actions: 该结点的可选行动方式
    """
    def __init__(self, actions) -> None:
        self.n = 0
        self.actions = {}
        # MCTS 扩展阶段会删除未扩展动作，因此这里保存一份私有拷贝。
        self.rest_actions = list(actions)

    def update(self, v: int, action) -> None:
        """
        更新结点信息
        Args:
            v: 反向传播得到的效用值
            action: 本次模拟中结点选择的行动方式
        """
        """
        Store total value and visit count for the selected action.
            请编写合理的代码段。
            这部分代码将实现反向传播时结点信息的更新。
        Note:
            只需修改`self.actions`中的内容，注意判断`action`是否出现在`self.actions`中。
        """
        # self.actions[action] 保存 [累计收益, 访问次数]。
        self.n += 1
        if action not in self.actions:
            self.actions[action] = [0, 0]
        self.actions[action][0] += v
        self.actions[action][1] += 1

    def average(self, action) -> float:
        """
        历史行动的效用的均值
        Args:
            action: 被询问的行动
        Returns:
            x_bar: 历史中结点选择了行动action得到的效用的均值
        """
        """
        Return the mean value observed for the selected action.
            请编写合理的代码段。
            这部分代码将返回当前结点的历史行动的效用均值。
        Note:
            可从`self.actions`中查询相关信息，注意判断`action`是否出现在`self.actions`中。
        """
        # 未访问动作还没有经验平均值，返回 0 避免除零。
        if action not in self.actions:
            return 0.0
        total_value, visit_count = self.actions[action]
        if visit_count == 0:
            return 0.0
        return total_value / visit_count

    def times(self, action) -> int:
        """
        历史中行动的次数
        Args:
            action: 被询问的行动
        Returns:
            n: 历史中结点选择行动action的次数
        """
        """
        Return how many times the selected action has been visited.
            请编写合理的代码段。
            这部分代码将返回当前结点的历史行动的行动次数。
        Note:
            可从`self.actions`中查询相应信息，注意判断`action`是否出现在`self.actions`中。
        """
        # UCB1 的探索项需要使用该动作的访问次数。
        if action not in self.actions:
            return 0
        return self.actions[action][1]

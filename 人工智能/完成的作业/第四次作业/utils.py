import numpy as np
from typing import Tuple, List, Dict


# 定义贝叶斯网络中共有n个节点，第i个节点有m_i个属性值[v_i_0, v_i_1, ..., v_i_{m_i-1}]
# 为了方便python中的下标取值，节点下标和属性值下标都从0开始

# size定义了每个节点对应的属性值个数，即(m_0, m_1, ..., m_n-1)
size = (2, 2, 3, 2, 2)

# loc_cond_prob为local conditional probability
# loc_cond_prob[idx][state]描述了第idx个节点在state中的局部条件概率
# 其中state=(v_0, v_1, ..., v_n-1)，即state[idx]为第idx个节点在当前联合中的属性值
# eg. state=(0, 0, 1, 1, 0)代表了(B0, E0, A1, R1, C0)的联合
# loc_cond_prob[1][state]代表P(E0|B0, A1, R1, C0) = P(E0)，（因为E不依赖于其他任何节点，所以state里其他节点的取值并不影响）
# loc_cond_prob[2][state]代表P(A1|B0, E0, R1, C0) = P(1|B0, E0)，（因为A只依赖于B和E）

loc_cond_prob = {}
loc_cond_prob[0] = np.zeros(size)
# 因为Burglary与其他节点都无关，所以无论其他节点的值如何（用:表明不在意下标），
# loc_cond_prob[0][state]即为P(Burglary)
loc_cond_prob[0][0, :, :, :, :] = 0.7
loc_cond_prob[0][1, :, :, :, :] = 0.3

loc_cond_prob[1] = np.zeros(size)
loc_cond_prob[1][:, 0, :, :, :] = 0.9
loc_cond_prob[1][:, 1, :, :, :] = 0.1

loc_cond_prob[2] = np.zeros(size)
loc_cond_prob[2][0, 0, 0, :, :] = 0.9
loc_cond_prob[2][0, 0, 1, :, :] = 0.09
loc_cond_prob[2][0, 0, 2, :, :] = 0.01
loc_cond_prob[2][0, 1, 0, :, :] = 0.05
loc_cond_prob[2][0, 1, 1, :, :] = 0.2
loc_cond_prob[2][0, 1, 2, :, :] = 0.75
loc_cond_prob[2][1, 0, 0, :, :] = 0.05
loc_cond_prob[2][1, 0, 1, :, :] = 0.7
loc_cond_prob[2][1, 0, 2, :, :] = 0.25
loc_cond_prob[2][1, 1, 0, :, :] = 0.01
loc_cond_prob[2][1, 1, 1, :, :] = 0.19
loc_cond_prob[2][1, 1, 2, :, :] = 0.8

# 根据贝叶斯网络结构补全 Radio 和 Call 的局部条件概率表。
loc_cond_prob[3] = np.zeros(size)
# Radio 只依赖 Earthquake：P(R|E)
loc_cond_prob[3][:, 0, :, 0, :] = 0.95
loc_cond_prob[3][:, 0, :, 1, :] = 0.05
loc_cond_prob[3][:, 1, :, 0, :] = 0.1
loc_cond_prob[3][:, 1, :, 1, :] = 0.9

loc_cond_prob[4] = np.zeros(size)
# Call 只依赖 Alarm：P(C|A)
loc_cond_prob[4][:, :, 0, :, 0] = 0.99
loc_cond_prob[4][:, :, 0, :, 1] = 0.01
loc_cond_prob[4][:, :, 1, :, 0] = 0.4
loc_cond_prob[4][:, :, 1, :, 1] = 0.6
loc_cond_prob[4][:, :, 2, :, 0] = 0.1
loc_cond_prob[4][:, :, 2, :, 1] = 0.9

class BayesianNetwork:
    def __init__(self, size: Tuple, loc_cond_prob: Dict) -> None:
        """
        初始化
        """
        self.size = size
        self.loc_cond_prob = loc_cond_prob
        # self.joint_states[i]为第i个state
        self.joint_states = {}
        # 记录在该贝叶斯网络中一共有多少个state
        self.state_num = 0
        # 初始化state
        self.cur_state = [0] * len(self.size)
        # 从第0个节点开始枚举，递归调用直至最后一个节点
        self.enumerate_joint_states(0)
        # self.joint_prob[state]即为P(state)
        self.joint_prob = np.ones(size)
        self.cal_joint_prob()
        # 指定一个随机种子，使得每次的随机结果都是一致的
        np.random.seed(42)

    def enumerate_joint_states(self, start_idx: int) -> None:
        """
        枚举所有可能的state,即(0, 0, 0, 0, 0), (0, 0, 0, 0, 1), ..., (1, 1, 1, 1, 1)
        """
        if start_idx == len(self.size):
            self.joint_states[self.state_num] = tuple(self.cur_state)
            self.state_num += 1
            return

        for val in range(self.size[start_idx]):
            self.cur_state[start_idx] = val
            self.enumerate_joint_states(start_idx + 1)
    def cal_joint_prob(self) -> None:
        """
        计算每个state对应的联合分布的概率
        """
        for idx in range(len(self.size)):
            for state in self.joint_states.values():
                # 联合概率由每个节点的局部条件概率连乘得到。
                self.joint_prob[state] *= self.loc_cond_prob[idx][state]
    def prob_map_joint(self) -> np.array:
        """
        将所有state的概率映射到[0, 1]上，即概率分布函数
        eg. 一共有3个state, state_0, state_1, state_2出现的概率分别为0.2, 0.5, 0.3,
        则返回sample_prob=[0.2, 0.7, 1],
        若生成服从0-1均匀分布随机数0.34,因为0.2<0.34<0.7,所以对应state_1
        """
        sample_prob = np.zeros((len(self.joint_states)))
        for i, state in enumerate(self.joint_states.values()):
            if i == 0:
                sample_prob[i] = self.joint_prob[state]
            else:
                sample_prob[i] = self.joint_prob[state] + sample_prob[i - 1]
        total_prob = sample_prob[-1]
        if total_prob > 0:
            sample_prob = sample_prob / total_prob
            sample_prob[-1] = 1.0  # 避免浮点误差导致随机数落不到任何区间
        return sample_prob
    def prob_map_cond(self, idx: int, cur_state: List, prob: Dict) -> np.array:
        """
        针对第idx个节点与给定的cur_state,计算其他节点值固定时第idx个节点取不同值的条件概率,
        将其条件概率映射到[0, 1]上，即概率分布函数
        """
        sample_prob = np.zeros((self.size[idx]))
        old_val = cur_state[idx]
        for val in range(self.size[idx]):
            cur_state[idx] = val
            # 固定其他变量，只枚举当前变量取值，并对候选概率重新归一化。
            sample_prob[val] = prob[idx][tuple(cur_state)]

        total_prob = sample_prob.sum()
        if total_prob > 0:
            sample_prob = np.cumsum(sample_prob / total_prob)
            sample_prob[-1] = 1.0
        else:
            # 极端情况下若候选概率全为0，退化为均匀分布以避免除零。
            sample_prob = np.cumsum(np.ones(self.size[idx]) / self.size[idx])
        cur_state[idx] = old_val

        return sample_prob

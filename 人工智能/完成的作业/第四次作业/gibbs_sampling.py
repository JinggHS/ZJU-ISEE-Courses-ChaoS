import numpy as np
from typing import Tuple, List, Dict
try:
    from tqdm import tqdm
except ModuleNotFoundError:
    # tqdm 只是进度条，环境没有安装时保持原算法正常运行。
    def tqdm(iterable):
        return iterable
from utils import BayesianNetwork, size, loc_cond_prob


class GibbsSampling(BayesianNetwork):
    def __init__(self, size: Tuple, loc_cond_prob: Dict) -> None:
        super(GibbsSampling, self).__init__(size, loc_cond_prob)
        self.cond_prob = {}
        self.cal_cond_prob()

    def cal_cond_prob(self):
        """
        通过local conditional probability计算conditional probability
        eg. state=(0, 0, 1, 1, 0)代表了(B0, E0, A1, R1, C0)的联合
        self.cond_prob[1][state]代表了P(E0|B0, A1, R1, C0)
        注意区分cond_prob和loc_cond_prob的不同
        """
        for i in range(len(self.size)):
            # 对目标节点所在维度求和，得到固定其他节点时的归一化分母。
            s = self.joint_prob.sum(axis=i, keepdims=True)

            s = np.where(s == 0, 1, s)  # 将s中为0的值替换成1，防止除0报错
            self.cond_prob[i] = self.joint_prob / s  # 对目标节点所处条件概率进行归一化

    def sampling(self, initial_state: List, sample_round: int, target_idx: int, evidence_idxs: List) -> np.array:
        """
        :param initial_state: 除evidence的属性值固定外,随机定义其他节点的属性值,得到一个初始state
        :param sample_round: 采样轮数
        :param target_idx: 查询节点的下标
        :param evidence_idxs: evidence的下标
        """
        cur_state = initial_state.copy()
        counts = np.zeros((self.size[target_idx]))
        for _ in tqdm(range(sample_round)):
            for idx in range(len(self.size)):
                if idx not in evidence_idxs:
                    # 非证据变量使用 P(X_i | 当前其他变量) 重新采样。
                    sample_prob = self.prob_map_cond(idx, cur_state, self.cond_prob)
                    # 生成服从0-1均匀分布的随机数
                    random_num = np.random.rand()
                    new_val = np.where(sample_prob >= random_num)[0][0]
                    # 更新cur_state中第idx个节点的属性值
                    cur_state[idx] = new_val
            # 每完成一轮 Gibbs 更新后，统计当前目标变量取值。
            counts[cur_state[target_idx]] += 1
        total_count = counts.sum()
        if total_count == 0:
            return counts
        return counts / total_count


if __name__ == "__main__":
    sample_method = GibbsSampling(size, loc_cond_prob)
    # 三个初始状态分别固定对应查询中的证据变量。
    initial_state = [
        [0, 1, 0, 0, 0],
        [0, 0, 2, 1, 0],
        [0, 1, 0, 0, 1],
    ]
    target_idx = [4, 0, 2]
    evidence_idxs = [[0, 1], [2, 3], [1, 3, 4]]
    for i in range(3):
        result = sample_method.sampling(initial_state=initial_state[i],
                                        sample_round=10000,
                                        target_idx=target_idx[i],
                                        evidence_idxs=evidence_idxs[i])
        print(result)

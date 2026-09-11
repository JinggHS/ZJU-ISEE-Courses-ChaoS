import numpy as np
from typing import Tuple, List, Dict
try:
    from tqdm import tqdm
except ModuleNotFoundError:
    # tqdm 只用于显示进度，缺失时不影响采样逻辑。
    def tqdm(iterable):
        return iterable
from utils import BayesianNetwork, size, loc_cond_prob


class LikelihoodWeighting(BayesianNetwork):
    def __init__(self, size: Tuple, loc_cond_prob: Dict) -> None:
        super(LikelihoodWeighting, self).__init__(size, loc_cond_prob)

    def sampling(self, initial_state: List, sample_round: int, target_idx: int, evidence_idxs: List) -> np.array:
        """
        :param initial_state: 除evidence的属性值固定外,随机定义其他节点的属性值,得到一个初始state
        :param sample_round: 采样轮数
        :param target_idx: 查询节点的下标
        :param evidence_idxs: evidence的下标
        """
        counts = np.zeros((self.size[target_idx]))
        for _ in tqdm(range(sample_round)):
            w = 1
            cur_state = initial_state.copy()
            for idx in range(len(self.size)):
                if idx in evidence_idxs:
                    # 证据变量固定不采样，将其在当前父节点条件下的概率乘入权重。
                    w *= self.loc_cond_prob[idx][tuple(cur_state)]
                else:
                    # 非证据变量按当前状态下的局部条件概率分布采样。
                    sample_prob = self.prob_map_cond(idx, cur_state, self.loc_cond_prob)
                    # 生成服从0-1均匀分布的随机数
                    random_num = np.random.rand()
                    # 找到采样对应的值
                    new_val = np.where(sample_prob >= random_num)[0][0]
                    # 更新cur_state中第idx个节点的值
                    cur_state[idx] = new_val
            # 用该轮样本的似然权重累加目标变量计数。
            counts[cur_state[target_idx]] += w

        total_count = counts.sum()
        if total_count == 0:
            return counts
        return counts / total_count


if __name__ == "__main__":
    sample_method = LikelihoodWeighting(size, loc_cond_prob)
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

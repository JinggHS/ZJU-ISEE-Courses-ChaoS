import numpy as np
from typing import Tuple, List, Dict
try:
    from tqdm import tqdm
except ModuleNotFoundError:
    # tqdm 不是算法必需依赖，缺失时直接退化为普通迭代器。
    def tqdm(iterable):
        return iterable
from utils import BayesianNetwork, size, loc_cond_prob


class RejectionSampling(BayesianNetwork):
    def __init__(self, size: Tuple, loc_cond_prob: Dict) -> None:
        super(RejectionSampling, self).__init__(size, loc_cond_prob)

    def sampling(self, sample_round: int, target_idx: int, evidences: Dict) -> np.array:
        """
        :param sample_round: 采样轮数
        :param target_idx: 查询节点的下标
        :param evidences: 字典,其中key为evidence的下标,value为对应的属性值
        """

        counts = np.zeros((self.size[target_idx]))
        sample_prob = self.prob_map_joint()
        for _ in tqdm(range(sample_round)):

            # 生成服从0-1均匀分布的随机数
            random_num = np.random.rand()
            state_idx = np.where(sample_prob >= random_num)[0][0]
            cur_state = self.joint_states[state_idx]
            # reject_flag为True时代表该state被拒绝
            reject_flag = False
            # 只接受所有证据变量都匹配的完整样本。
            for idx, val in evidences.items():
                if cur_state[idx] != val:
                    reject_flag = True
                    break
            if not reject_flag:
                # 目标变量取到哪个属性值，就给对应计数加一。
                counts[cur_state[target_idx]] += 1

        total_count = counts.sum()
        if total_count == 0:
            return counts
        return counts / total_count  # normalize count


if __name__ == "__main__":
    sample_method = RejectionSampling(size, loc_cond_prob)
    target_idx = [4, 0, 2]
    evidences = [{0: 0, 1: 1}, {2: 2, 3: 1}, {1: 1, 3: 0, 4: 1}]
    for i in range(3):
        result = sample_method.sampling(sample_round=10000,
                                        target_idx=target_idx[i],
                                        evidences=evidences[i])
        print(result)

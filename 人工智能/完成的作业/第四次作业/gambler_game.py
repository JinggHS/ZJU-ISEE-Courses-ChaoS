import numpy as np


class MarkovChain:
    """马尔可夫链类"""
    def __init__(self, transition_matrix, init_state):
        self.transition_matrix = np.array(transition_matrix)
        self.cur_state = init_state
        # 指定一个随机种子，使得每次的随机结果都是一致的
        np.random.seed(42)

    def step(self):
        """执行马尔可夫链单步状态转移"""
        # 获取当前状态在转移矩阵中的概率分布
        probabilities = self.transition_matrix[self.cur_state]
        # 将当前行概率映射到[0, 1]累计区间，再用均匀随机数采样。
        sample_prob = np.cumsum(probabilities)
        if sample_prob[-1] > 0:
            sample_prob = sample_prob / sample_prob[-1]
            sample_prob[-1] = 1.0
        random_num = np.random.rand()
        new_state = int(np.where(sample_prob >= random_num)[0][0])

        # 更新当前状态为选中的下一个状态
        self.cur_state = new_state
        # 返回下一个状态
        return self.cur_state


class GamblerGame:
    """定义赌徒游戏类"""
    def __init__(self, p, q, a, b):
        self.p = p
        self.q = q
        self.a = a
        self.b = b
        self.c = a + b + 1
        self.states = np.arange(self.c)
        self.transition_matrix = self.build_transition_matrix()

    def build_transition_matrix(self):
        """
        根据p, q构造状态转移矩阵
        """
        transition_matrix = np.zeros((self.c, self.c))
        # 状态0和状态c-1为吸收态；中间状态按输赢概率向左右转移。
        transition_matrix[0, 0] = 1
        transition_matrix[self.c - 1, self.c - 1] = 1
        for i in range(1, self.c - 1):
            transition_matrix[i, i + 1] = self.p
            transition_matrix[i, i - 1] = self.q
        return transition_matrix

    def simulate(self, num_steps):
        """模拟赌博游戏过程"""
        Chain = MarkovChain(self.transition_matrix, self.a)
        results = []

        for _ in range(num_steps):
            state = Chain.step()
            results.append(state)

        return results

    def probability_of_ruin(self):
        """甲破产的概率"""
        init_state = self.a
        # 假设10000次已足够达到平稳状态
        # 调用linalg.matrix_power方法计算转移矩阵的转置的10000次幂
        probability_ruin = np.linalg.matrix_power(self.transition_matrix.T, 10000)[0, init_state]  # # 转移矩阵T的n次幂T^n中，T^n[i, j] 代表从状态 i 转移到 j 的概率。代码中使用 T.T 是为了配合矩阵索引习惯
        return probability_ruin


if __name__ == "__main__":
    """
    可以调整赌徒问题的参数（输赢概率和起始资金），观察结果的变化
    """
    p = 0.5
    q = 0.5
    a = 10
    b = 10

    gambler_chain = GamblerGame(p, q, a, b)

    # 模拟10轮赌博
    num_rounds = 10
    results = gambler_chain.simulate(num_rounds)
    print("Results after 10 rounds:", results)

    # 模拟50轮赌博
    num_rounds = 50
    results = gambler_chain.simulate(num_rounds)
    print("Results after 50 rounds:", results)

    # 甲输光的概率
    probability_ruin = gambler_chain.probability_of_ruin()
    print(f"The probability of A losing all the money: {probability_ruin}")


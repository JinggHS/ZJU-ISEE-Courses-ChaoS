import numpy as np
import cmath

# 1. 设置参数 (根据理论计算得出，需要修改参数)
theta = np.pi / 4  # 修改使得激发态概率为 25%
phi = 0.0          # 全局相位

# 2. 定义量子门矩阵
H = np.array([[1, 1], 
              [1, -1]]) / np.sqrt(2)

P_theta = np.array([[1, 0], 
                    [0, cmath.exp(1j * theta)]])

P_phi = np.array([[1, 0], 
                  [0, cmath.exp(1j * (np.pi/2 + phi))]])

# 3. 初始态 |0> (100% 基态），针对第二小问，此处需要修改参数
state = np.array([1.0+0.0j, 0.0+0.0j])

# 4. 依次作用量子门：U = P_phi * H * P_theta * H
state = np.dot(H, state)
state = np.dot(P_theta, state)
state = np.dot(H, state)
state = np.dot(P_phi, state)

# 5. 计算并输出概率
prob_0 = abs(state[0])**2
prob_1 = abs(state[1])**2

print(f"最终基态概率   (|0>): {prob_0 * 100:.2f}%")
print(f"最终激发态概率 (|1>): {prob_1 * 100:.2f}%")
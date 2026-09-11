from typing import List, Dict, Tuple, Callable, Optional
import time
import random
import logging
import networkx as nx
import matplotlib.pyplot as plt

# 是否输出执行日志
LOG = True

class CSP:
    ''' CSP 主类 '''

    def __init__(self, variables:List[str], domains:Dict[str,List[str]], constraints:Dict[Tuple[str, str], Callable[[str, str], bool]], logger:logging.Logger = None):
        ''' CSP 类初始化函数（只针对 binary CSP，即每个约束只涉及两个变量）

        Args:
            * variables: CSP 问题包含的变量，列表形式，列表的元素为变量名，例如 ['A', 'B', 'C']
            * domains: CSP 问题的变量的定义域，字典形式，字典的键为变量名，字典的值为变量的定义域，例如 {'A': ['red', 'green'], 'B': ['green', 'blue'], 'C': ['red', 'blue']}
            * constraints: CSP 问题的约束条件，字典形式，字典的键为约束的变量列表（元组），字典的值为约束的函数，例如 {('A', 'B'): lambda a, b: a != b, ('B', 'C'): lambda b, c: b != c}
            * logger: 日志输出对象，如果为 None，则使用默认日志设定

        Remarks:
            * List[str] 无实际意义，仅代表函数参数类型的注释
            * 注释格式参考: https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html ，个人感觉 google style 比较清楚
            * CSP 求解算法部分代码参考: https://github.com/aimacode/aima-python/blob/master/csp.py
        '''
        self.variables = variables
        self.domains = domains
        self.constraints = constraints

        # 获取邻接变量
        self.neighbors = {}
        for v in self.variables:
            self.neighbors[v] = set()
        for v in self.constraints.keys():
            self.neighbors[v[0]].add(v[1])
            self.neighbors[v[1]].add(v[0])

        # 获取邻接约束
        self.neighbor_constraints = {}
        for v in self.variables:
            self.neighbor_constraints[v] = {}
        for v, f in self.constraints.items():
            self.neighbor_constraints[v[0]][v[1]] = f
            self.neighbor_constraints[v[1]][v[0]] = f


        # 尝试次数
        self.attempts = 0

        # 日志输出
        if logger is None:
            self.logger = logging.getLogger('CSP')
            self.logger.setLevel(logging.DEBUG)
            self.logger.propagate = False
            if not self.logger.handlers:
                fh = logging.FileHandler('csp.log', mode="w", encoding='utf-8')
                fh.setLevel(logging.DEBUG)
                ch = logging.StreamHandler()
                ch.setLevel(logging.INFO)
                formatter = logging.Formatter('[%(levelname)s] %(message)s')
                ch.setFormatter(formatter)
                fh.setFormatter(formatter)
                self.logger.addHandler(fh)
                self.logger.addHandler(ch)
        else:
            self.logger = logger

        self.logger.info(f'变量数: {len(self.variables)}')
        self.logger.debug(f'变量: {self.variables}')
        if len(self.variables) > 0:
            self.logger.info(f'定义域: {self.domains[self.variables[0]]}')
        else:
            self.logger.info('定义域: []')
        self.logger.info(f'约束数: {len(self.constraints)}')
        self.logger.debug(f'邻接变量: {self.neighbors}')
        self.logger.debug(f"邻接变量约束：{self.neighbor_constraints}")

    def check_consistent_variable(self, var1:str, value1:str, var2:str, value2:str) -> bool:
        ''' 检查输入的一对变量的赋值是否满足约束要求

        Args:
            * var1: 变量 1 变量名
            * value1: 变量 1 的赋值
            * var2: 变量 2 变量名
            * value2: 变量 2 的赋值

        Returns:
            * 变量是否满足约束要求，True 代表满足，False 代表不满足
        '''

        return self.neighbor_constraints[var1][var2](value1, value2)


    def check_consistent_assignment(self, var:str, value:str, assignment: Dict[str, str]) -> bool:
        ''' 检查输入变量的赋值是否与已赋值的其它变量满足约束要求

        Args:
            * var: 输入变量名
            * value: 输入变量的赋值
            * assignment: 当前的已赋值的其它变量及其赋值结果
        Returns:
            * 变量是否满足约束要求，True 代表满足，False 代表不满足
        '''

        consistent = True

        # 遍历与变量有关的约束
        for v in self.neighbors[var]:
            if v in assignment:
                consistent = consistent and self.check_consistent_variable(var, value, v, assignment[v])

                # 输出日志
                self.logger.debug(f"检查约束：变量对 '{var}:{value},{v}:{assignment[v]}' 是否满足约束要求：{consistent}")

                if not consistent:
                    break

        return consistent

    def get_next_assign_variable(self, left_variables: List[str], method: str) -> str:
        ''' 获取下一个变量，基于 FIRST 准则或者 MRV 准则或者 MRV-DEGREE 准则选择下一个需要尝试赋值的变量

        Args:
            * left_variables: 剩余未赋值的变量
            * method: 选择下一个变量的方法，可以为 "first" 或者 "mrv" 或者 “mrv-degree"
                * "first" 代表 FIRST 准则，选择 left_variables[0] 作为下一个需要赋值的变量
                * "mrv" 代表 Minimum-remaining-values 准则，选择定义域最小的变量作为下一个赋值的变量
                * "mrv-degree" 代表 Minimum-remaining-values 准则和 Degree 准则的结合版本，选择定义域最小的变量作为下一个赋值的变量，如果存在多个定义域最小的变量，则选择与其他变量约束数最多的变量作为下一个赋值的变量
        Returns:
            * 下一个进行赋值的变量
        '''

        # 若没有可供选择的变量，则返回
        if(len(left_variables) == 0):
            return None

        # FIRST 准则
        if method == "first":
            return left_variables[0]
        # MRV 准则
        elif method == "mrv":
            min_domain = -1
            min_var = -1
            for var in left_variables:
                if min_domain == -1 or len(self.domains[var]) < min_domain:
                    min_domain = len(self.domains[var])
                    min_var = var
            self.logger.debug(f"MRV 准则：选择变量 {min_var} 进行赋值，该变量具有 {min_domain} 个可取值")
            return min_var
        # MRV+DEGREE 准则
        elif method == "mrv-degree":
            min_domain = -1
            max_degree = -1
            min_var = -1
            for var in left_variables:
                if min_domain == -1 or len(self.domains[var]) <= min_domain:
                    # 获取当前变量针对剩余未赋值变量的约束条数，也就是剩余未赋值的邻域变量数
                    degree = 0
                    for neib_var in self.neighbors[var]:
                        if neib_var in left_variables:
                            degree += 1
                    # 若定义域与最小定义域相同，则选择约束数最多的变量
                    if len(self.domains[var]) == min_domain:
                        if degree > max_degree:
                            max_degree = degree
                            min_var = var
                    # 若定义域小于最小定义域，则选择当前变量
                    else:
                        min_domain = len(self.domains[var])
                        max_degree = degree
                        min_var = var
            self.logger.debug(f"MRV-DEGREE 准则：选择变量 {min_var} 进行赋值，该变量具有 {min_domain} 个可取值以及关联 {max_degree} 个约束")
            return min_var
        else:
            raise ValueError(f"变量选择方法 {method} 不存在")

    def sort_assigned_value(self, var: str, assignment: Dict[str, str], method: str) -> List[str]:
        ''' 对测试的变量值进行排序，基于 FIRST 准则或者 LCV 准则排序变量定义域中值的测试顺序

        Args:
            * var: 变量名
            * assignment: 当前的已赋值变量及其赋值结果
            * method: 选择下一个变量的方法，可以为 "first" 或者 "lcv"
                * "first" 代表 FIRST 准则，选择 domains[0] 作为下一个需要赋值的变量
                * "lcv" 代表 Least-constraining-values heuristic 准则，选择引发最少冲突的变量值作为下一个赋值的变量
        Returns:
            * 变量值排序结果
        '''

        # FIRST 准则
        if method == "first":
            return self.domains[var]
        # LCV 准则
        elif method == "lcv":
            # 初始化 values_conflict_count 列表，该列表存储变量取值及其引发的冲突数
            values_conflict_count = []
            # 遍历所有可选值，计算每个值引发的冲突数
            for value in self.domains[var]:
                conflict_count = 0
                # 遍历所有未赋值变量的定义域，累加所有会引发冲突的取值的数量
                for neib_var in self.neighbors[var]:
                    if neib_var not in assignment:
                        for neib_val in self.domains[neib_var]:
                            if not self.check_consistent_variable(var, value, neib_var, neib_val):
                                conflict_count += 1
                # 将当前值及其引发的冲突数添加到 values_conflict_count 列表中
                values_conflict_count.append((value, conflict_count))
            # 对 values_conflict_count 按照冲突数从小到大排序
            values_conflict_count.sort(key=lambda x: x[1])
            self.logger.debug(f"LCV 准则：变量 {var} 的取值排序结果为 {values_conflict_count}")
            # 返回按照冲突数从小到大排序的变量取值
            return [x[0] for x in values_conflict_count]
        else:
            raise ValueError(f"变量值排序方法 {method} 不存在")

    def revise(self, center_var:str, neighbor_var:str, remove_values=List[Tuple[str, str, int]]) -> Tuple[bool, bool]:
        ''' 通过移除 neighbor_var 定义域中的不合理值令 center_var 和 neighbor_var 之间的实现 arc-consistent

        Args:
            * center_var: 中心变量
            * neighbor_var: 邻接变量，与中心变量之间存在约束连接，函数将修改邻接变量的定义域使得不管邻接变量取何值中心变量与邻接变量之间的约束均成立，即实现 arc-consistent
            * remove_values: 对变量定义域的修改记录
        Returns:
            * ret[0] 是否修改了邻接变量定义域，True 代表修改了，False 代表没有修改
            * ret[1] 是否成功实现了 arc_consistent，True 代表实现，False 代表由于邻接变量定义域为空而未实现
        '''

        revised = False
        arc_consistent = True

        # 遍历邻接变量的定义域，注意这里需要对邻接变量的定义域进行拷贝，因为在遍历的过程中会对定义域中的值进行移除，不使用拷贝方式的话遍历结果会不正确
        for neighbor_var_value in self.domains[neighbor_var].copy():
            # 遍历中心变量的定义域，查看是否存在满足需求的取值（任意邻接变量取值，均存在在中心变量取值，使得约束满足）
            consistent = False
            for center_var_value in self.domains[center_var]:
                if self.check_consistent_variable(center_var, center_var_value, neighbor_var, neighbor_var_value):
                    consistent = True
                    break
            # 如果邻接变量的某个定义域值无法找到实现 consistent 的中心变量值，则将该定义域值从邻接变量的定义域中删除
            if not consistent:
                remove_idx = self.domains[neighbor_var].index(neighbor_var_value) # 为了回溯时保持变量顺序不变，所以额外记录下位置，这个操作主要是为了性能比较的公平性，防止约束传播影响变量值的测试顺序。在实际 CSP 问题的求解中，这个操作不是必需的。
                self.domains[neighbor_var].remove(neighbor_var_value)
                revised = True
                remove_values.append((neighbor_var, neighbor_var_value, remove_idx))
                # 如果邻接变量的定义域为空，则 arc_consistent 未能成功实现
                if len(self.domains[neighbor_var]) == 0:
                    arc_consistent = False
                    return revised, arc_consistent
        return revised, arc_consistent

    def inference(self, var:str, value:str, method: str) -> Tuple[bool, List[Tuple[str, str, int]]]:
        ''' 约束传播函数，基于 Forward 或者 AC3 算法进行约束传播

        Args:
            * var: 变量名
            * value: 变量的赋值
            * method: 约束传播方法，可以为 "no_inference" 或者 "forward"，或者 "AC3"
                * no_inference：不进行约束传播
                * forward: 仅修改当前变量周围变量的定义域，不进行进一步的约束传播，仅使当前变量与周围变量之间 arc-consistent
                * AC3：基于 AC3 算法修改当前变量周围变量的定义域，并进行进一步的约束传播，使所有变量 arc-consistent
        Returns:
            * ret[0]: 约束传播是否成功，True 代表成功，False 代表失败
            * ret[1]: 当前变量周围变量的定义域修改记录，用于回溯时恢复定义域，例如 [('A', 'red', 0)] 代表删除了变量 A 的定义域中的位于索引 0 的 'red' 值，在后续回溯时会将 'red' 擦插入回变量 A 的索引 0 处
        '''

        # 初始化 remove_values 列表
        remove_values = [] # 记录需要从变量定义域中删除的值

        # 记录当前变量的 remove_values，当前变量选择了 value，因此其它定义域中的取值均视为 remove_values
        for domain_value in self.domains[var].copy():
            if domain_value != value:
                remove_idx = self.domains[var].index(domain_value)
                remove_values.append((var, domain_value, remove_idx))
                self.domains[var].remove(domain_value)
            # self.domains[var] = [value]

        if method == "forward":
            # 遍历所有邻接变量进行约束传播
            for neib_var in self.neighbors[var]:
                # 尝试修改定义域实现 arc_consistent
                revised, arc_consistent = self.revise(var, neib_var, remove_values)
                # 若无法实现 arc_consistent，则约束传播失败
                if not arc_consistent:
                    return False, remove_values
            self.logger.debug(f"Forward 约束传播后变量定义域：{self.domains}")
            return True, remove_values
        elif method == "AC3":
            # 定义一个队列，用于存储所有与当前变量有关的约束
            queue = []
            # 说明：这里队列元素建议使用 (center_var, neighbor_var)
            # 并调用 revise(center_var, neighbor_var, remove_values)。
            # revise 会“修改 neighbor_var 的定义域”以满足 neighbor_var -> center_var 的弧一致性。
            # 因此请注意弧方向，避免把会被删值的变量写反。

            # 将所有约束加入队列（提示：约束可以以（var, neib_var) 的元组进行表示，revise 函数可以自动根据这个元组找到对应约束））
            # 当前变量已经确定取值，先从它出发传播到所有邻居
            for neib_var in self.neighbors[var]:
                queue.append((var, neib_var))

            # 遍历队列中的所有约束
            while len(queue) > 0:

                # 获取队列中的第一个约束
                center_var, neighbor_var = queue.pop(0)

                # 尝试修改定义域实现 var 和 neib_var 的 arc_consistent（提示：调用 self.revise 函数）
                revised, arc_consistent = self.revise(center_var, neighbor_var, remove_values)

                # 若无法实现 arc_consistent，则约束传播失败
                if not arc_consistent:
                    return False, remove_values

                # 若修改了邻接变量的定义域，则将邻接变量的邻接变量也添加进队列中
                # 说明：若 neighbor_var 的定义域被修改，需要继续检查其余相关弧。
                # 常见做法是把 (neighbor_var, x) 或等价方向的弧重新入队（x 为 neighbor_var 的其它邻接变量）。
                if revised:
                    # 邻居定义域发生变化后，需要继续检查它对其它邻居的影响
                    for x in self.neighbors[neighbor_var]:
                        if x != center_var:
                            queue.append((neighbor_var, x))

            self.logger.debug(f"AC3 约束传播后变量定义域：{self.domains}")
            # 返回约束传播结果以及对定义域的修改记录
            return True, remove_values
        elif method == "no_inference":
            return True, remove_values
        else:
            raise ValueError(f"约束传播方法 {method} 不存在")

    def backtracking_search(self, assignment: Dict[str, str], left_variables: List[str], variable_choose_method:str = "first", value_sort_method:str = "first", inference_method:str = "no_inference") -> Dict[str, str]:
        ''' 回溯搜索算法

        Args:
            * assignment: 一组符合约束要求的变量赋值结果，例如 {'A': 'red', 'B': 'green'}
            * left_variables: 剩余未赋值的变量，例如 ['C']
            * variable_choose_method: 选择下一个搜索变量的方法，可以为 "first" 或者 "mrv" 或者 “mrv-degree"，默认为 "first"
            * value_sort_method: 排序搜索变量值的方法，可以为 "first" 或者 "lcv"，默认为 "first"
            * inference_method: 约束传播方法，可以为 "no_inference" 或者 "forward" 或者 "AC3"，默认为 "no_inference"
        Returns:
            * 一组符合约束要求且完整的变量赋值结果，例如 {'A': 'red', 'B': 'green', 'C': 'blue'}，或者 None，代表当前约束下无解
        Remarks:
            * 关于回溯算法的更多应用可见代码随想录的讲解，感兴趣的同学也可以对上面的例题练一练，这部分讲的内容实际上在互联网秋招的笔试面试里面也是很常考的 https://programmercarl.com/%E5%9B%9E%E6%BA%AF%E7%AE%97%E6%B3%95%E7%90%86%E8%AE%BA%E5%9F%BA%E7%A1%80.html#%E7%90%86%E8%AE%BA%E5%9F%BA%E7%A1%80
        '''

        # 递归终止条件，如果所有变量已赋值，则返回结果
        if len(left_variables) == 0:
            # 检查递归结果是否符合要求
            return assignment

        # 尝试次数过多，返回 None
        if self.attempts > 1e6:
            return None

        # 使用这段代码可以把仍未赋值的变量标成灰色
        # if self.attempts > 1e6:
        #     for var in left_variables:
        #         assignment[var] = 'grey'
        #     return assignment

        # 选择下一个测试变量（提示：调用 get_next_assign_variable 函数）
        # 按给定策略选择下一个待赋值变量
        var = self.get_next_assign_variable(left_variables, variable_choose_method)

        # 遍历变量的定义域（提示：调用 sort_assigned_value 函数）
        # 按给定策略决定当前变量的取值尝试顺序
        for value in self.sort_assigned_value(var, assignment, value_sort_method): # TODO_DONE: 已补全取值遍历逻辑

            # 尝试次数加一
            self.attempts += 1

            self.logger.debug(f'第 {self.attempts} 次尝试: 变量 {var} 选择值 {value}')

            # 检验选择的变量值是否满足约束（提示：调用 check_consistent_assignment 函数）
            if self.check_consistent_assignment(var, value, assignment): # TODO_DONE: 已补全一致性检查逻辑

                # 赋值（提示：需要更新 assignment 和 left_variables）
                # 说明：建议先把 var 从 left_variables 移除，再在 assignment[var] 写入 value。
                # 记录原位置，回溯时按原顺序插回
                var_idx = left_variables.index(var)
                left_variables.pop(var_idx)
                assignment[var] = value

                # 进行约束传播（提示：调用 inference 函数）
                # 说明：inference 会临时裁剪定义域，并返回 remove_values 供回溯恢复。
                inference_result, remove_values = self.inference(var, value, inference_method)

                # 如果约束传播成功，则继续递归求解
                if inference_result: # TODO_DONE: 已补全约束传播结果判断

                    # 输出日志（注意 f-string 需求 3.6 及以上 python 版本才能正常运行）
                    self.logger.info(f'第 {self.attempts} 次尝试[✔]: 变量 {var} 赋值 {value}，当前赋值结果: {assignment}')

                    # 递归求解
                    result = self.backtracking_search(
                        assignment,
                        left_variables,
                        variable_choose_method,
                        value_sort_method,
                        inference_method
                    )

                    # 如果求解成功，则返回结果
                    if result is not None:
                        return result
                else:
                    self.logger.info(f'第 {self.attempts} 次尝试[❌]: 变量 {var} 赋值 {value}，当前赋值结果: {assignment}，约束传播失败')

                # 回溯（提示：需要根据 remove_values 恢复定义域，以及恢复 left_variables 和 assignment 的内容）

                # 恢复定义域（如果约束传播不成功，回退到发生错误的变量，也就是当前变量）
                # 说明：按 remove_values 中记录的 (变量, 值, 索引) 恢复，
                # 建议用 insert(索引, 值) 而不是 append，以保持定义域顺序不变。
                # 逆序恢复定义域，避免插入位置受到前面恢复操作影响
                for domain_var, domain_value, remove_idx in reversed(remove_values):
                    self.domains[domain_var].insert(remove_idx, domain_value)
                # 恢复 left_variables 和 assignment（注意left_variables需要保证var顺序与原先一致）
                # 说明：left_variables 也建议按原位置插回 var，避免影响 FIRST/MRV-DEGREE 的可比性。
                del assignment[var]
                left_variables.insert(var_idx, var)
            else:
                self.logger.info(f'第 {self.attempts} 次尝试[❌]: 变量 {var} 赋值 {value}，当前赋值结果: {assignment}，当前变量值不满足约束')

        return None

    def solve(self, variable_choose_method:str = "first", value_sort_method:str = "first", inference_method:str = "no_inference") -> Dict[str, str]:
        return self.backtracking_search({}, self.variables, variable_choose_method, value_sort_method, inference_method)

class MapColoringCSP(CSP):
    ''' 地图着色问题类，继承自 CSP 类 '''

    def __init__(self, data="./city_connection/Australia.txt", color=3, logger=None):
        ''' 对地图上色问题进行抽象表示，同时进行变量初始化

        Args:
            * data: 地图数据文件路径
            * color: 地图着色颜色数
            * logger: 日志输出对象，如果为 None，则使用默认日志设定
        '''

        variables = []
        domains = {}
        constraints = {}
        color_table = ["red","green","blue","yellow","purple"]

        if color < 1 or color > len(color_table):
            raise ValueError(f"color 必须在 1 到 {len(color_table)} 之间，当前值为 {color}")

        # 读取地图数据
        # Australia.txt 文件内容如下：
        # ==============================
        # =  SA: WA, NT, Q, NSW, V     =
        # =  NT: WA, Q                 =
        # =  NSW: Q, V                 =
        # =  T:                        =
        # ==============================
        with open(data, 'r') as f:

            for line in f:
                var = line.split(":")[0].strip()
                neighbors = [i.strip() for i in line.split(":")[1].split(",") if i.strip() != ""]

                if var not in variables:
                    variables.append(var)
                    domains[var] = [color_table[i] for i in range(color)]

                for neighbor in neighbors:
                    if neighbor not in variables:
                        variables.append(neighbor)
                        domains[neighbor] = [color_table[i] for i in range(color)]
                    constraints[(var, neighbor)] = lambda x, y: x != y

        # 也可以通过下面的注释的形式手动指定 variables、domains、constraints 的取值
        # variables = ['WA', 'SA', 'Q', 'NT', 'NSW', 'V', 'T']
        # domains = {
        #     'WA': ['blue', 'green', 'red'],
        #     'NT': ['red', 'green', 'blue'],
        #     'SA': ['red', 'green', 'blue'],
        #     'Q': ['red', 'green', 'blue'],
        #     'NSW': ['red', 'green', 'blue'],
        #     'V': ['red', 'green', 'blue'],
        #     'T': ['red', 'green', 'blue']
        # }
        # constraints = {
        #     ('WA', 'NT'): lambda wa, nt: wa != nt,
        #     ('WA', 'SA'): lambda wa, sa: wa != sa,
        #     ('NT', 'SA'): lambda nt, sa: nt != sa,
        #     ('NT', 'Q'): lambda nt, q: nt != q,
        #     ('SA', 'Q'): lambda sa, q: sa != q,
        #     ('SA', 'NSW'): lambda sa, nsw: sa != nsw,
        #     ('SA', 'V'): lambda sa, v: sa != v,
        #     ('Q', 'NSW'): lambda q, nsw: q != nsw,
        #     ('NSW', 'V'): lambda nsw, v: nsw != v
        # }

        # 初始化 CSP 类
        super().__init__(variables, domains, constraints, logger)

    def solve(self, variable_choose_method:str = "first", value_sort_method:str = "first", inference_method:str = "no_inference") -> Optional[Dict[str, str]]:
        ''' 对地图上色问题进行求解

        Args:
            * variable_choose_method: 选择下一个搜索变量的方法，可以为 "first" 或者 "mrv" 或者 “mrv-degree"，默认为 "first"
            * value_sort_method: 排序搜索变量值的方法，可以为 "first" 或者 "lcv"，默认为 "first"
            * inference_method: 约束传播方法，可以为 "no_inference" 或者 "forward" 或者 "AC3"，默认为 "no_inference"

        Returns:
            * 一组符合约束要求且完整的变量赋值结果，例如 {'WA': 'red', 'NT': 'green', 'SA': 'blue', 'Q': 'red', 'NSW': 'green', 'V': 'red', 'T': 'red'}
        '''

        # 求解
        result = super().solve(variable_choose_method, value_sort_method, inference_method)

        # 输出日志
        self.logger.info(f'求解结果: {result}')

        return result

    def draw_map(self, colors: Dict[str, str]) -> None:
        ''' 对地图上色问题结果进行输出（绘制着色后地图）

        Args:
            * colors: 一组符合约束要求的变量赋值结果，例如 {'WA': 'red', 'NT': 'green', 'SA': 'blue', 'Q': 'red', 'NSW': 'green', 'V': 'red', 'T': 'red'}
        '''

        # 定义 nx.Graph 对象
        graph = nx.Graph()
        graph.add_nodes_from([var for var in self.variables if len(self.neighbors[var]) > 0])
        graph.add_edges_from([(x, y) for x, y in self.constraints.keys()])

        # 定义节点颜色
        node_colors = [colors[node] for node in graph.nodes()]

        # 计算节点位置（目前 spring_layout 在存在孤立节点时显示效果不太好，所以前面把孤立节点去掉了，或许也可以尝试其它的布局算法）
        pos = nx.spring_layout(graph)

        # 绘制图形
        nx.draw(graph, pos, node_color=node_colors, with_labels=True)

        # 显示图形
        plt.show()


class SudokuCSP(CSP):
    ''' 4x4 数独问题类，继承自 CSP 类 '''

    def __init__(self, board: List[List[int]], logger=None):
        ''' 对 4x4 数独问题进行抽象表示
        
        Args:
            * board: 一个 4x4 的二维列表，0 表示未填写的空格，1-4 表示已填写的数字
            * logger: 日志输出对象
        '''
        variables = []
        domains = {}
        constraints = {}

        # ==========================================
        # TODO_DONE 1: 已定义 variables 和 domains
        # 提示：
        # 1. 遍历 4x4 的棋盘 (i 范围 0~3, j 范围 0~3)。
        # 2. 可以使用类似 f"{i}-{j}" 的字符串作为变量名，添加到 variables 列表中。
        # 3. 检查 board[i][j] 的值。如果为 0，说明是空格，该变量的定义域 domains[var] 应该是 [1, 2, 3, 4]。
        # 4. 如果 board[i][j] 不为 0，说明是固定数字，该变量的定义域应该只包含这一个数字，例如 [board[i][j]]。
        # ==========================================
        # 每个格子对应一个变量，空格取值范围为 1~4，已填数字固定为单元素定义域
        for i in range(4):
            for j in range(4):
                var = f"{i}-{j}"
                variables.append(var)
                if board[i][j] == 0:
                    domains[var] = [1, 2, 3, 4]
                else:
                    domains[var] = [board[i][j]]

        # ==========================================
        # TODO_DONE 2: 已定义 constraints
        # 提示：
        # 1. 遍历所有的变量对 (var1, var2)。你可以使用两层嵌套循环来遍历变量列表，其中 var1 代表 "i1-j1", var2 代表 "i2-j2"。
        # 2. 如果 var1 和 var2 不是同一个格子，且它们满足以下任意一个条件，则需要添加约束（要求两个格子的值不能相同）：
        #    - 在同一行 (i1 == i2)
        #    - 在同一列 (j1 == j2)
        #    - 在同一个 2x2 宫格内 (i1//2 == i2//2 且 j1//2 == j2//2)
        # 3. 添加约束的方法：constraints[(var1, var2)] = lambda x, y: x != y
        # （注：你只需添加单向的 (var1, var2) 约束即可，无需重复添加反向的 (var2, var1) 约束，基类会自动处理对称关系）
        # ==========================================
        # 同行、同列、同宫的两个格子之间建立“不相等”约束
        for idx1 in range(len(variables)):
            for idx2 in range(idx1 + 1, len(variables)):
                var1 = variables[idx1]
                var2 = variables[idx2]
                i1, j1 = map(int, var1.split("-"))
                i2, j2 = map(int, var2.split("-"))

                same_row = i1 == i2
                same_col = j1 == j2
                same_box = i1 // 2 == i2 // 2 and j1 // 2 == j2 // 2

                if same_row or same_col or same_box:
                    constraints[(var1, var2)] = lambda x, y: x != y

        # 初始化 CSP 类
        super().__init__(variables, domains, constraints, logger)

    def print_board(self, assignment: Dict[str, int]) -> None:
        ''' 打印数独结果的辅助函数 '''
        if not assignment:
            print("当前数独无解！")
            return
        
        print("-" * 13)
        for i in range(4):
            row_str = "| "
            for j in range(4):
                var = f"{i}-{j}"
                val = assignment.get(var, ".")
                row_str += f"{val} "
                if j % 2 == 1:
                    row_str += "| "
            print(row_str)
            if i % 2 == 1:
                print("-" * 13)

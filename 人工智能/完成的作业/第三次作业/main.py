import random
import logging
from csp import MapColoringCSP, SudokuCSP

def csp_test(country, color) -> None:

    '''测试不同地图 CSP 算法的尝试次数，该函数会调用两次 CSP 求解算法，一次使用最基础的算法，一次使用启用了 MRV-DEGREE 准则 + LCV 准则 + AC3 约束传播算法的优化版本

    Args:
        * country: 地图名称，例如 "Australia"，函数会搜索 ./city_connection/ 目录下的给定名称的 txt 文件作为 MapColoringCSP 的输入
        * color: 地图着色颜色数，例如 3，代表使用 3 种颜色对地图进行着色
    '''

    # 关闭日志输出
    logger = logging.getLogger('CSPNOLOG')
    logger.setLevel(logging.ERROR)
    # fh = logging.FileHandler('csp.log', mode="w", encoding='utf-8')
    # ch = logging.StreamHandler()
    # formatter = logging.Formatter('[%(levelname)s] %(message)s')
    # ch.setFormatter(formatter)
    # fh.setFormatter(formatter)
    # logger.addHandler(fh)
    # logger.addHandler(ch)

    # 默认的读取方式形成的变量排序相当于近似 MRV 准则的结果，为了模拟真实的乱序排序，这里使用 random.shuffle 对变量排序进行打乱
    random.seed("AI2024")
    csp_origin = MapColoringCSP(f"./city_connection/{country}.txt", color, logger=logger)
    shuffled_variables = csp_origin.variables.copy()
    random.shuffle(shuffled_variables)

    # 执行基础版本的 CSP 求解算法
    csp = MapColoringCSP(f"./city_connection/{country}.txt", color, logger=logger)
    csp.variables = shuffled_variables.copy()
    _ = csp.solve(variable_choose_method="first", value_sort_method="first", inference_method="no_inference")
    print(f"{country} => 尝试次数（未优化）：{csp.attempts}")

    # MRV
    csp = MapColoringCSP(f"./city_connection/{country}.txt", color, logger=logger)
    csp.variables = shuffled_variables.copy()
    _ = csp.solve(variable_choose_method="mrv", value_sort_method="first", inference_method="no_inference")
    print(f"{country} => 尝试次数（MRV）+：{csp.attempts}")

    # MRV+DEGREE
    csp = MapColoringCSP(f"./city_connection/{country}.txt", color, logger=logger)
    csp.variables = shuffled_variables.copy()
    # print(f"{csp.variables}")
    _ = csp.solve(variable_choose_method="mrv-degree", value_sort_method="first", inference_method="no_inference")
    print(f"{country} => 尝试次数（MRV+DEGREE）+：{csp.attempts}")

    # LCV
    csp = MapColoringCSP(f"./city_connection/{country}.txt", color, logger=logger)
    csp.variables = shuffled_variables.copy()
    _ = csp.solve(variable_choose_method="first", value_sort_method="lcv", inference_method="no_inference")
    print(f"{country} => 尝试次数（LCV）+：{csp.attempts}")

    # Forward
    csp = MapColoringCSP(f"./city_connection/{country}.txt", color, logger=logger)
    csp.variables = shuffled_variables.copy()
    _ = csp.solve(variable_choose_method="first", value_sort_method="first", inference_method="forward")
    print(f"{country} => 尝试次数（Forward）+：{csp.attempts}")

    # Forward+MRV
    csp = MapColoringCSP(f"./city_connection/{country}.txt", color, logger=logger)
    csp.variables = shuffled_variables.copy()
    _ = csp.solve(variable_choose_method="mrv", value_sort_method="first", inference_method="forward")
    print(f"{country} => 尝试次数（Forward+MRV）+：{csp.attempts}")

    # Forward+MRV+DEGREE
    csp = MapColoringCSP(f"./city_connection/{country}.txt", color, logger=logger)
    csp.variables = shuffled_variables.copy()
    _ = csp.solve(variable_choose_method="mrv-degree", value_sort_method="first", inference_method="forward")
    print(f"{country} => 尝试次数（Forward+MRV+DEGREE）+：{csp.attempts}")

    # Forward+LCV
    csp = MapColoringCSP(f"./city_connection/{country}.txt", color, logger=logger)
    csp.variables = shuffled_variables.copy()
    # print(f"{csp.variables}")
    _ = csp.solve(variable_choose_method="first", value_sort_method="lcv", inference_method="forward")
    print(f"{country} => 尝试次数（Forward+LCV）+：{csp.attempts}")

    # AC3
    csp = MapColoringCSP(f"./city_connection/{country}.txt", color, logger=logger)
    csp.variables = shuffled_variables.copy()
    _ = csp.solve(variable_choose_method="first", value_sort_method="first", inference_method="AC3")
    print(f"{country} => 尝试次数（AC3）+：{csp.attempts}")

    # AC3+MRV
    csp = MapColoringCSP(f"./city_connection/{country}.txt", color, logger=logger)
    csp.variables = shuffled_variables.copy()
    _ = csp.solve(variable_choose_method="mrv", value_sort_method="first", inference_method="AC3")
    print(f"{country} => 尝试次数（AC3+MRV）+：{csp.attempts}")

    # AC3+MRV+DEGREE
    csp = MapColoringCSP(f"./city_connection/{country}.txt", color, logger=logger)
    csp.variables = shuffled_variables.copy()
    _ = csp.solve(variable_choose_method="mrv-degree", value_sort_method="first", inference_method="AC3")
    print(f"{country} => 尝试次数（AC3+MRV+DEGREE）+：{csp.attempts}")

    # AC3+LCV
    csp = MapColoringCSP(f"./city_connection/{country}.txt", color, logger=logger)
    csp.variables = shuffled_variables.copy()
    _ = csp.solve(variable_choose_method="first", value_sort_method="lcv", inference_method="AC3")
    print(f"{country} => 尝试次数（AC3+LCV）+：{csp.attempts}")

    # 执行优化版本的 CSP 求解算法
    csp = MapColoringCSP(f"./city_connection/{country}.txt", color, logger=logger)
    csp.variables = shuffled_variables.copy()
    result = csp.solve(variable_choose_method="mrv-degree", value_sort_method="lcv", inference_method="AC3")
    print(f"{country} => 尝试次数（AC3+MRV-DEGREE+LCV）：{csp.attempts}")

    # 输出地图着色结果
    print(f"{country} => 最终着色结果：{result}")

def csp_show(country, color):
    '''显示不同地图 CSP 算法的执行过程以及输出结果，该函数启用了 CSP 算法执行时的日志打印功能，可以在终端和 csp.log 文件中查看执行日志，其中在 csp.log 文件的日志内容更加详细

    Args:
        * country: 地图名称，例如 "Australia"，函数会搜索 ./city_connection/ 目录下的给定名称的 txt 文件作为 MapColoringCSP 的输入
        * color: 地图着色颜色数，例如 3，代表使用 3 种颜色对地图进行着色
    '''

    # 设定日志输出
    logger = logging.getLogger('CSP') # 不能跟前面定义的 CSPNOLOG 重名
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)
        
    fh = logging.FileHandler('csp.log', mode="w", encoding='utf-8')
    fh.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('[%(levelname)s] %(message)s')
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    logger.addHandler(ch)

    # 执行优化版本的 CSP 求解算法
    csp = MapColoringCSP(f"./city_connection/{country}.txt", color, logger=logger)
    random.shuffle(csp.variables) 
    result = csp.solve(variable_choose_method="mrv-degree", value_sort_method="lcv", inference_method="AC3")

    # 输出地图着色结果
    if result is None:
        print(f"{country} => 无解，无法绘图")
        return
    csp.draw_map(result)

def sudoku_test():
    ''' 测试 4x4 数独的求解 '''
    print("\n" + "="*30)
    print("开始测试 4x4 数独求解")
    print("="*30)

    # 设定日志输出
    logger = logging.getLogger('SUDOKU')
    logger.setLevel(logging.ERROR) # 保持终端清爽，只看结果
    if not logger.handlers:
        logger.addHandler(logging.NullHandler()) # 彻底静默，防止报 no handlers 警告

    # 定义一个 4x4 的残缺数独 (0代表空格)
    # 示例棋盘：
    # 1 0 | 0 0
    # 0 0 | 2 0
    # ---------
    # 0 3 | 0 0
    # 0 0 | 0 4
    board = [
        [1, 0, 0, 0],
        [0, 0, 2, 0],
        [0, 3, 0, 0],
        [0, 0, 0, 4]
    ]

    print("初始棋盘状态：")
    # 简单打印初始棋盘
    print("-" * 13)
    for i in range(4):
        row_str = "| "
        for j in range(4):
            val = board[i][j] if board[i][j] != 0 else "."
            row_str += f"{val} "
            if j % 2 == 1:
                row_str += "| "
        print(row_str)
        if i % 2 == 1:
            print("-" * 13)

    try:
        sudoku_csp = SudokuCSP(board, logger=logger)
        
        # 使用最强配置进行求解
        result = sudoku_csp.solve(variable_choose_method="mrv-degree", value_sort_method="lcv", inference_method="AC3")
        
        print("\n数独求解结果：")
        sudoku_csp.print_board(result)
        print(f"求解尝试次数: {sudoku_csp.attempts}")
    except NotImplementedError:
        print("\n提示：请先在 csp.py 中完成 SudokuCSP 类的 TODO 部分！")

if __name__ == '__main__':
    print("="*40)
    print(" 欢迎使用 CSP 算法测试程序")
    print("="*40)
    print("请选择要运行的测试任务：")
    print("1. 地图着色问题 (Map Coloring)")
    print("2. 4x4 数独问题 (Sudoku)")
    print("3. 运行全部任务")
    print("="*40)
    
    choice = input("请输入选项 (1/2/3): ").strip()

    if choice == '1':
        csp_test("Australia", 3)
        csp_test("France", 4)
        csp_test("USA", 4)
        csp_show("Australia", 3)
        csp_show("France", 4)
        csp_show("USA", 4)
        
    elif choice == '2':
        sudoku_test()
        
    elif choice == '3':
        print("\n--- 正在运行地图着色问题 ---")
        csp_test("Australia", 3)
        csp_test("France", 4)
        csp_test("USA", 4)
        csp_show("Australia", 3)
        csp_show("France", 4)
        csp_show("USA", 4)
        print("\n--- 正在运行 4x4 数独问题 ---")
        sudoku_test()
        
    else:
        print("无效的输入，请重新运行程序并输入 1、2 或 3。")
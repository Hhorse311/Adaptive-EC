# main.py

import config
from simulator import Simulator
from tqdm import tqdm


def run_bft_ec_simulation():
    """
    主函数，用于运行BFT-EC方案的模拟。
    [修改] 循环运行多次并取平均值。
    """
    # 1. 初始化模拟器
    sim = Simulator(config=config)

    # 2. [新增] 创建一个列表来存储每次模拟的结果
    all_run_results = []

    print(f"Starting simulation. Total runs to average: {config.SIMULATION_RUNS}")

    # 3. [新增] 循环运行整个模拟过程
    for i in tqdm(range(config.SIMULATION_RUNS), desc="Overall Simulation Progress"):
        # run_single_simulation_instance会返回一次完整模拟的DataFrame
        single_run_df = sim.run_single_simulation_instance()
        all_run_results.append(single_run_df)

    # 4. [新增] 所有模拟运行完毕后，生成最终的平均报告
    sim.generate_final_report(all_run_results)


if __name__ == "__main__":
    run_bft_ec_simulation()

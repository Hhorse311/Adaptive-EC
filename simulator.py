# simulator.py

import random
import pandas as pd
import numpy as np
from tqdm import tqdm
from node import NodeStatus
from network import Network


class Simulator:
    def __init__(self, config):
        self.config = config
        self.initial_nodes = config.INITIAL_HOST_NODES
        self.block_size_bytes = config.BLOCK_SIZE_MB * 1024 * 1024

    def _run_single_exit_step(self, network, num_nodes_to_exit):
        active_node_ids = [
            node_id for node_id, info in network.node_state_table.items()
            if info['status'] == NodeStatus.ACTIVE
        ]
        if not active_node_ids:
            return {'repair_bandwidth': 0, 'exit_latency': 0, 'avg_recovery_latency': float('inf'),
                    'max_recovery_level': -1}

        nodes_to_exit = random.sample(active_node_ids, min(num_nodes_to_exit, len(active_node_ids)))

        total_repair_bandwidth = 0
        total_exit_latency = 0
        for node_id in nodes_to_exit:
            repair_bandwidth, exit_latency = network.handle_node_exit(node_id)
            total_repair_bandwidth += repair_bandwidth
            total_exit_latency += exit_latency

        recovery_latencies = []
        max_recovery_level_in_run = -1
        for _ in range(self.config.RECOVERY_REPETITIONS):
            latency, _, recovery_level = network.retrieve_block(self.block_size_bytes)
            if latency != float('inf'):
                recovery_latencies.append(latency)
            max_recovery_level_in_run = max(max_recovery_level_in_run, recovery_level)

        avg_recovery_latency = np.mean(recovery_latencies) if recovery_latencies else float('inf')

        return {
            'repair_bandwidth': total_repair_bandwidth,
            'exit_latency': total_exit_latency,
            'avg_recovery_latency': avg_recovery_latency,
            'max_recovery_level': max_recovery_level_in_run
        }

    def run_single_simulation_instance(self):
        network = Network(
            num_nodes=self.initial_nodes,
            byzantine_percentage=self.config.BYZANTINE_PERCENTAGE,
            tree_depth=self.config.TREE_DEPTH,
            initial_block_size_bytes=self.block_size_bytes
        )
        results = []

        _, initial_write_latency, initial_k = network.initial_block_distribution()
        initial_storage_overhead = network.total_storage_overhead

        initial_recovery_latencies = []
        for _ in range(self.config.RECOVERY_REPETITIONS):
            lat, _, _ = network.retrieve_block(self.block_size_bytes)
            if lat != float('inf'):
                initial_recovery_latencies.append(lat)
        avg_initial_recovery_latency = np.mean(initial_recovery_latencies) if initial_recovery_latencies else float(
            'inf')

        results.append({
            'exit_percentage': 0,
            'remaining_nodes': self.initial_nodes,
            'total_storage_overhead': initial_storage_overhead,
            'total_repair_bandwidth': 0,
            'write_latency': initial_write_latency,
            'max_recovery_level': 0,
            'avg_recovery_latency': avg_initial_recovery_latency
        })

        step = int(self.initial_nodes * self.config.EXIT_PERCENTAGE_STEP)
        if step == 0: step = 1

        max_exited_nodes = int(self.initial_nodes * self.config.MAX_EXIT_PERCENTAGE)
        total_exited_nodes = 0

        current_nodes = self.initial_nodes
        while current_nodes > self.initial_nodes - max_exited_nodes and current_nodes > 0:
            num_to_exit = min(step, current_nodes - (self.initial_nodes - max_exited_nodes))
            if num_to_exit <= 0: break

            metrics = self._run_single_exit_step(network, num_nodes_to_exit=num_to_exit)
            total_exited_nodes += num_to_exit
            current_nodes -= num_to_exit

            exit_percentage = total_exited_nodes / self.initial_nodes

            results.append({
                'exit_percentage': exit_percentage,
                'remaining_nodes': current_nodes,
                'total_storage_overhead': network.total_storage_overhead,
                'total_repair_bandwidth': network.total_repair_bandwidth,
                'write_latency': metrics['exit_latency'] / num_to_exit if num_to_exit > 0 else 0,
                'max_recovery_level': metrics['max_recovery_level'],
                'avg_recovery_latency': metrics['avg_recovery_latency']
            })

        return pd.DataFrame(results)

    # --- [核心修改] 重写报告生成函数 ---
    def generate_final_report(self, all_results_dfs):
        if not all_results_dfs:
            print("No simulation results to report.")
            return

        combined_df = pd.concat(all_results_dfs)
        final_df = combined_df.groupby('exit_percentage').mean().reset_index()

        print(f"\n--- Final Simulation Results (Averaged over {len(all_results_dfs)} runs) ---")
        print("--- BFT-EC Scheme Data ---")

        # 定义一个辅助函数来格式化和打印列表
        def print_as_list(variable_name, data_series, precision=4):
            # 将Series转换为列表，并四舍五入到指定精度
            data_list = data_series.round(precision).tolist()
            # 打印成 "variable_name = [item1, item2, ...]" 的格式
            print(f"{variable_name} = {data_list}")

        # 1. 退出百分比 (作为整数百分比)
        exit_percentage_list = (final_df['exit_percentage'] * 100).astype(int).tolist()
        print(f"exit_percentage = {exit_percentage_list}")

        # 2. 恢复延迟
        print_as_list("bft_ec_recovery_latency_s", final_df['avg_recovery_latency'])

        # 3. 存储开销 (MB)
        storage_overhead_mb = final_df['total_storage_overhead'] / (1024 * 1024)
        print_as_list("bft_ec_storage_overhead_mb", storage_overhead_mb)

        # 4. 修复带宽 (MB)
        repair_bandwidth_mb = final_df['total_repair_bandwidth'] / (1024 * 1024)
        print_as_list("bft_ec_repair_bandwidth_mb", repair_bandwidth_mb)

        # 5. 写入/修复延迟 (注意：'write_latency'列在step>0时代表的是单节点修复延迟)
        # 为了清晰，我们分别处理初始写入和后续修复
        initial_write_latency = final_df.loc[0, 'write_latency']
        repair_latency_list = final_df.loc[1:, 'write_latency'].tolist()
        print(f"bft_ec_initial_write_latency_s = [{round(initial_write_latency, 4)}]")
        print(f"bft_ec_repair_latency_per_node_s = {[round(x, 4) for x in repair_latency_list]}")

        # 6. 剩余节点数
        remaining_nodes_list = final_df['remaining_nodes'].astype(int).tolist()
        print(f"remaining_nodes = {remaining_nodes_list}")

        # 7. 最大恢复层级
        max_recovery_level_list = final_df['max_recovery_level'].astype(int).tolist()
        print(f"max_recovery_level = {max_recovery_level_list}")

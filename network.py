# network.py

import random
import math
import numpy as np
from node import Node, NodeStatus
from utils import calculate_optimal_k
import config as network_config
from config import (
    RS_COMPUTE_TIME_PER_MB,
    HOMOMORPHIC_FINGERPRINT_SIZE_BYTES as HF_PRINT_SIZE_BYTES,
    HF_COMPUTE_TIME_PER_MB,
    HF_VERIFY_FIXED_TIME
)

# [新增] 定义一个常量，用于模拟一次失败的层级发现尝试的开销
# 假设每次尝试都需要一次网络往返来确定节点是否足够
LEVEL_DISCOVERY_FAILURE_PENALTY = network_config.NETWORK_CONNECTION_OVERHEAD_R

class Network:
    def __init__(self, num_nodes, byzantine_percentage, tree_depth, initial_block_size_bytes):
        self.num_nodes = num_nodes
        self.byzantine_percentage = network_config.BYZANTINE_PERCENTAGE
        self.tree_depth = tree_depth
        self.initial_block_size_bytes = initial_block_size_bytes
        self.node_state_table = {}
        self.tree_data_info = {}
        self.public_vouchers = {}
        self.current_block_height = 0
        self.total_repair_bandwidth = 0
        self.total_storage_overhead = 0
        self.config = network_config
        self._initialize_nodes()

    def _initialize_nodes(self):
        for i in range(self.num_nodes):
            node = Node(i)
            is_byzantine = random.random() < self.byzantine_percentage
            self.node_state_table[i] = {
                'node': node,
                'status': NodeStatus.ACTIVE,
                'storage': {},
                'is_byzantine': is_byzantine
            }

    def get_active_nodes_info(self):
        return [
            info for info in self.node_state_table.values()
            if info['status'] == NodeStatus.ACTIVE
        ]

    def _get_generator_matrix(self, k, n):
        return np.random.rand(n, k)

    def _distribute_and_encode(self, data_size_bytes, target_nodes_info, level, block_height):
        n = len(target_nodes_info)
        if n == 0: return 0, 0, 0, 0
        k = calculate_optimal_k(data_size_bytes, self.config.NETWORK_SPEED_GBPS * 1e9, n)
        if k > n: k = n
        if k == 0: return 0, 0, 0, 0
        piece_size = data_size_bytes / k
        generator_matrix = self._get_generator_matrix(k, n)
        self.tree_data_info[level] = {'k': k, 'piece_size': piece_size, 'G': generator_matrix}
        for i, info in enumerate(target_nodes_info):
            info['storage'][level] = block_height
            info['node'].storage[level] = block_height
        data_size_mb = data_size_bytes / (1024 * 1024)
        rs_encode_latency = data_size_mb * RS_COMPUTE_TIME_PER_MB
        hf_generation_latency = data_size_mb * HF_COMPUTE_TIME_PER_MB
        self.public_vouchers[block_height] = {'R': random.random(), 'Hd': [random.random() for _ in range(k)]}
        if target_nodes_info:
            transfer_size = piece_size + HF_PRINT_SIZE_BYTES
            transfer_latency = (transfer_size * 8 / (self.config.NETWORK_SPEED_GBPS * 1e9)) + self.config.NETWORK_CONNECTION_OVERHEAD_R
        else:
            transfer_latency = 0
        total_encode_latency = rs_encode_latency + hf_generation_latency
        storage_cost = n * piece_size
        return storage_cost, transfer_latency, total_encode_latency, k

    def initial_block_distribution(self):
        self.current_block_height = 1
        active_nodes_info = self.get_active_nodes_info()
        storage_cost, transfer_latency, encode_latency, k = self._distribute_and_encode(
            self.initial_block_size_bytes, active_nodes_info, level=0, block_height=self.current_block_height)
        self.total_storage_overhead += storage_cost
        write_latency = encode_latency + transfer_latency
        return storage_cost, write_latency, k

    def handle_node_exit(self, node_id):
        if self.node_state_table[node_id]['status'] == NodeStatus.INACTIVE: return 0, 0
        self.node_state_table[node_id]['status'] = NodeStatus.INACTIVE
        exited_node_storage = self.node_state_table[node_id]['storage']
        total_data_to_reencode_bytes = 0
        for level, block_height in exited_node_storage.items():
            if block_height == self.current_block_height:
                piece_size = self.tree_data_info[level]['piece_size']
                total_data_to_reencode_bytes += piece_size
        if total_data_to_reencode_bytes == 0: return 0, 0
        active_nodes_info = self.get_active_nodes_info()
        new_level = max(self.tree_data_info.keys()) + 1 if self.tree_data_info else 0
        storage_cost, transfer_latency, encode_latency, _ = self._distribute_and_encode(
            total_data_to_reencode_bytes, active_nodes_info, level=new_level, block_height=self.current_block_height)
        self.total_storage_overhead += storage_cost
        repair_bandwidth = total_data_to_reencode_bytes
        self.total_repair_bandwidth += repair_bandwidth
        exit_latency = encode_latency + transfer_latency
        return repair_bandwidth, exit_latency

    # --- [核心重构] 实现“串行试错”的真实恢复逻辑 ---
    def retrieve_block(self, block_size_bytes):
        total_search_and_recovery_latency = 0

        # 按层级顺序从0开始尝试
        sorted_levels = sorted(self.tree_data_info.keys())

        for level in sorted_levels:
            info = self.tree_data_info[level]
            k = info['k']
            piece_size = info['piece_size']

            available_providers = [
                p_info for p_info in self.get_active_nodes_info()
                if level in p_info['node'].storage and p_info['node'].storage[level] == self.current_block_height
            ]

            # 检查本层节点是否足够
            if len(available_providers) < k:
                # 失败！累加一次发现失败的惩罚时间，然后继续尝试下一层
                total_search_and_recovery_latency += LEVEL_DISCOVERY_FAILURE_PENALTY
                continue

            # 节点数足够，开始真正的恢复尝试
            random.shuffle(available_providers)
            valid_pieces_count = 0
            current_level_latency = 0
            providers_attempted = 0

            while valid_pieces_count < k and providers_attempted < len(available_providers):
                provider = available_providers[providers_attempted]
                providers_attempted += 1

                download_latency = (piece_size * 8 / (self.config.NETWORK_SPEED_GBPS * 1e9)) + self.config.NETWORK_CONNECTION_OVERHEAD_R
                piece_size_mb = piece_size / (1024 * 1024)
                hf_compute_actual_latency = piece_size_mb * HF_COMPUTE_TIME_PER_MB
                hf_verify_expected_latency = HF_VERIFY_FIXED_TIME

                # 累加本次下载和验证的延迟
                current_level_latency += download_latency + hf_compute_actual_latency + hf_verify_expected_latency

                if not provider['is_byzantine']:
                    valid_pieces_count += 1

            # 检查本轮尝试是否成功集齐k个分片
            if valid_pieces_count >= k:
                # 成功！加上最终的解码延迟
                data_size_mb = (k * piece_size) / (1024 * 1024)
                decode_latency = data_size_mb * RS_COMPUTE_TIME_PER_MB
                current_level_latency += decode_latency

                # 总延迟 = 之前所有失败层级的搜索延迟 + 本层成功的恢复延迟
                total_search_and_recovery_latency += current_level_latency

                bandwidth_cost = block_size_bytes
                # 找到第一个可行的方案后，立刻返回，不再继续搜索
                return total_search_and_recovery_latency, bandwidth_cost, level
            else:
                # 本层节点数虽然够，但拜占庭节点太多，导致尝试失败
                # 累加本层所有失败的下载和验证尝试的开销
                total_search_and_recovery_latency += current_level_latency
                # 继续去下一层寻找机会
                continue

        # 如果遍历完所有层级都无法恢复
        return float('inf'), 0, -1

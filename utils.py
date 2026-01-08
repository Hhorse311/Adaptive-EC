# utils.py

import math
# 从 config 模块导入计算所需的参数
from config import WEIGHT_A, WEIGHT_B, NETWORK_CONNECTION_OVERHEAD_R


def calculate_optimal_k(B, V_bps, n):
    """
    根据给定的成本函数和安全约束，计算最优的 k 值。
    """
    # --- 1. 确定 k 的有效范围 ---
    f = math.floor((n - 1) / 3)
    k_max = n - 2 * f
    k_min = 1

    if k_max < k_min:
        return k_max if k_max > 0 else 1

    # --- 2. 遍历所有可能的 k 值，寻找成本最低的解 ---
    min_cost = float('inf')
    optimal_k = k_min
    V_Bps = V_bps / 8.0

    # 遍历从 k_min 到 k_max 的所有整数 k
    for k in range(k_min, k_max + 1):
        if k == 0:
            continue

        # 对应公式中的变量
        S_bytes = B  # S_bytes 是以字节为单位的原始数据大小
        V = V_Bps
        A = WEIGHT_A
        B_weight = WEIGHT_B
        R = NETWORK_CONNECTION_OVERHEAD_R

        # --- [核心修改] ---
        # 为了平衡量级，存储成本部分将 S 按 MB 计算。
        # S_bytes / (1024 * 1024) 将字节转换为 MB。
        # 这使得存储成本项和延迟成本项在数值上具有可比性。
        S_mb = S_bytes / (1024 * 1024.0)
        storage_cost = A * n * S_mb / k

        # 延迟成本部分，S 仍需使用原始字节单位，以确保 S/V 的时间计算正确。
        # (字节) / (字节/秒) = 秒
        latency_cost = B_weight * 1.5 * (k - 1) * (R + S_bytes / (V * k))

        total_cost = storage_cost + latency_cost

        # 如果当前 k 的成本更低，则更新最优解
        if total_cost < min_cost:
            min_cost = total_cost
            optimal_k = k

    return optimal_k


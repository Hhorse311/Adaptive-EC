# node.py

from enum import Enum, auto
from config import PIECE_METADATA_SIZE_BYTES, HOMOMORPHIC_FINGERPRINT_SIZE_BYTES

class NodeStatus(Enum):
    """
    定义节点的状态。
    """
    ACTIVE = auto()    # 节点正常在线
    INACTIVE = auto()  # 节点已退出或离线

class Node:
    """
    代表网络中的一个存储节点。
    """
    def __init__(self, node_id, ip_address=None):
        self.id = node_id
        self.ip = ip_address
        # 存储结构: {level: block_height}
        # 简化存储，只记录节点存储了哪个层级的哪个区块
        self.storage = {}

    def store_piece(self, level, piece_index, metadata, piece_data, fingerprint_piece):
        """存储一个带有元数据和指纹分片的数据分片"""
        # 这个详细的方法在当前模拟中未被直接调用，但保留其结构
        if level not in self.storage:
            self.storage[level] = {}
        self.storage[level][piece_index] = {
            'metadata': metadata,
            'data': piece_data,
            'fingerprint_piece': fingerprint_piece
        }

    def get_piece_data(self, level, piece_index):
        """获取分片的数据部分"""
        piece = self.storage.get(level, {}).get(piece_index)
        return piece['data'] if piece else None

    def get_total_stored_size(self):
        """计算总存储大小，现在包含元数据和指纹分片"""
        total_size = 0
        for level_storage in self.storage.values():
            for piece in level_storage.values():
                total_size += len(piece['data'])
                total_size += PIECE_METADATA_SIZE_BYTES
                total_size += len(piece['fingerprint_piece'])
        return total_size

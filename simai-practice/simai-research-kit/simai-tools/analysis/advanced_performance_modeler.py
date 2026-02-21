#!/usr/bin/env python3
"""
SimAI高级性能建模器 v1.0
精确建模集合通信性能，考虑网络拥塞、流水线效应、混合拓扑

主要功能：
1. 精确的Ring/Tree/Hierarchical算法建模
2. 网络拥塞建模
3. 流水线效应建模
4. 混合拓扑性能预测
5. 异构网络建模（不同带宽）
6. 性能瓶颈分析

Author: 二愣子
Date: 2026-02-19
"""

import math
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
from enum import Enum


class Algorithm(Enum):
    """集合通信算法"""
    RING = "ring"
    TREE = "tree"
    HIERARCHICAL = "hierarchical"
    MESH = "mesh"


class Topology(Enum):
    """网络拓扑"""
    SINGLE_NODE = "single_node"
    FAT_TREE = "fat_tree"
    DRAGONFLY = "dragonfly"
    TORUS = "torus"
    HYBRID = "hybrid"


@dataclass
class NetworkLink:
    """网络链路特性"""
    bandwidth_gbps: float  # 带宽（Gbps）
    latency_us: float  # 延迟（微秒）
    num_links: int = 1  # 并行链路数

    @property
    def bandwidth_gbps_total(self) -> float:
        """总带宽（考虑并行链路）"""
        return self.bandwidth_gbps * self.num_links

    @property
    def bandwidth_mbps(self) -> float:
        """带宽（MB/s）"""
        return self.bandwidth_gbps_total * 125  # Gbps -> MB/s

    @property
    def bandwidth_bytes_per_sec(self) -> float:
        """带宽（bytes/s）"""
        return self.bandwidth_mbps * 1024 * 1024  # MB/s -> bytes/s


@dataclass
class NetworkConfig:
    """网络配置"""
    intra_node_link: NetworkLink  # 节点内链路（如NVLink）
    inter_node_link: NetworkLink  # 节点间链路（如NIC）
    topology: Topology
    num_nodes: int  # 节点数
    gpus_per_node: int  # 每节点GPU数

    @property
    def total_gpus(self) -> int:
        """总GPU数"""
        return self.num_nodes * self.gpus_per_node

    def get_hops(self, src_gpu: int, dst_gpu: int) -> int:
        """计算两个GPU之间的跳数"""
        src_node = src_gpu // self.gpus_per_node
        dst_node = dst_gpu // self.gpus_per_node

        if src_node == dst_node:
            return 1  # 同节点，1跳（NVLink）
        else:
            if self.topology == Topology.SINGLE_NODE:
                return 1
            elif self.topology == Topology.FAT_TREE:
                return 3  # 上行+下行+汇聚
            elif self.topology == Topology.DRAGONFLY:
                return min(abs(src_node - dst_node) + 1, 3)
            elif self.topology == Topology.TORUS:
                dx = abs(src_node % 8 - dst_node % 8)
                dy = abs(src_node // 8 - dst_node // 8)
                return dx + dy
            else:
                return 2

    def get_effective_bandwidth(self, src_gpu: int, dst_gpu: int) -> float:
        """获取有效带宽（考虑跳数和拓扑）"""
        hops = self.get_hops(src_gpu, dst_gpu)
        src_node = src_gpu // self.gpus_per_node
        dst_node = dst_gpu // self.gpus_per_node

        if src_node == dst_node:
            return self.intra_node_link.bandwidth_bytes_per_sec
        else:
            # 节点间通信，考虑路径上最慢的链路
            bw = min(self.intra_node_link.bandwidth_bytes_per_sec, self.inter_node_link.bandwidth_bytes_per_sec)

            # 拥塞因子：跳数越多，有效带宽越低
            congestion_factor = 1.0 / (1.0 + 0.1 * (hops - 1))
            return bw * congestion_factor


@dataclass
class CollectiveOperation:
    """集合通信操作"""
    op_type: str  # all_reduce, all_to_all, broadcast, etc.
    num_gpus: int
    msg_size_mb: float
    algorithm: Algorithm


class PerformanceModeler:
    """高级性能建模器"""

    def __init__(self, network: NetworkConfig):
        self.network = network
        self.pipeline_threshold_mb = 64.0  # 流水线阈值
        self.congestion_threshold = 0.8  # 拥塞阈值

    def estimate_all_reduce(self, op: CollectiveOperation) -> Dict:
        """
        估算AllReduce性能

        返回：
        - time_ms: 总时间（毫秒）
        - breakdown: 时间分解
        - bottleneck: 瓶颈分析
        """
        if op.algorithm == Algorithm.RING:
            return self._all_reduce_ring(op)
        elif op.algorithm == Algorithm.TREE:
            return self._all_reduce_tree(op)
        elif op.algorithm == Algorithm.HIERARCHICAL:
            return self._all_reduce_hierarchical(op)
        else:
            raise ValueError(f"Unsupported algorithm: {op.algorithm}")

    def _all_reduce_ring(self, op: CollectiveOperation) -> Dict:
        """
        Ring AllReduce建模

        阶段：
        1. Reduce-Scatter: (n-1)轮，每轮msg_size/n
        2. AllGather: (n-1)轮，每轮msg_size/n

        Ring特点：
        - 每个GPU与2个邻居通信
        - 带宽利用率高
        - 延迟敏感度低
        """
        n = op.num_gpus
        chunk_size_mb = op.msg_size_mb / n
        chunk_size_bytes = chunk_size_mb * 1024 * 1024

        # 计算每个GPU的平均带宽
        avg_bandwidth = self._calculate_avg_bandwidth(n)

        # Reduce-Scatter阶段
        rs_rounds = n - 1
        rs_data_per_round = chunk_size_bytes

        # 考虑流水线效果
        if chunk_size_mb > self.pipeline_threshold_mb:
            # 大消息，流水线有效
            rs_time = (rs_rounds * rs_data_per_round) / avg_bandwidth
        else:
            # 小消息，延迟主导
            avg_latency_us = self._calculate_avg_latency(n)
            rs_time = rs_rounds * (rs_data_per_round / avg_bandwidth + avg_latency_us / 1000)

        # AllGather阶段
        ag_rounds = n - 1
        ag_data_per_round = chunk_size_bytes

        if chunk_size_mb > self.pipeline_threshold_mb:
            ag_time = (ag_rounds * ag_data_per_round) / avg_bandwidth
        else:
            ag_time = ag_rounds * (ag_data_per_round / avg_bandwidth + avg_latency_us / 1000)

        total_time_sec = rs_time + ag_time
        total_time_ms = total_time_sec * 1000

        # 瓶颈分析
        bandwidth_bound = (chunk_size_mb > self.pipeline_threshold_mb)
        bottleneck = "bandwidth" if bandwidth_bound else "latency"

        # 带宽利用率：每个GPU发送 2*(n-1)*msg_size/n 的数据
        data_per_gpu_mb = 2 * (n - 1) * chunk_size_mb

        return {
            "time_ms": total_time_ms,
            "breakdown": {
                "reduce_scatter_ms": rs_time * 1000,
                "all_gather_ms": ag_time * 1000,
                "ratio_rs_to_ag": rs_time / ag_time if ag_time > 0 else 0
            },
            "bottleneck": bottleneck,
            "bandwidth_utilization_gbps": (data_per_gpu_mb * 8 / total_time_sec) if total_time_sec > 0 else 0,
            "efficiency": self._calculate_ring_efficiency(n, chunk_size_mb)
        }

    def _all_reduce_tree(self, op: CollectiveOperation) -> Dict:
        """
        Tree AllReduce建模

        特点：
        - log2(n)轮
        - 每轮消息大小递增
        - 延迟敏感度高
        - 适合小消息
        """
        n = op.num_gpus
        depth = math.ceil(math.log2(n))

        # 计算平均带宽和延迟
        avg_bandwidth = self._calculate_avg_bandwidth(n)
        avg_latency_us = self._calculate_avg_latency(n)

        total_time = 0.0
        data_per_round = []

        for level in range(depth):
            # 每轮的消息大小
            msg_bytes = op.msg_size_mb * 1024 * 1024

            # 参与通信的GPU对数
            active_pairs = n // (2 ** (level + 1))

            # 通信时间
            comm_time = msg_bytes / avg_bandwidth + avg_latency_us / 1000
            total_time += comm_time

            data_per_round.append({
                "level": level,
                "msg_size_mb": op.msg_size_mb,
                "active_pairs": active_pairs,
                "time_ms": comm_time * 1000
            })

        total_time_ms = total_time * 1000

        # Tree带宽利用率：每个GPU参与log2(n)轮，每轮发送msg_size
        data_per_gpu_mb = op.msg_size_mb * depth

        return {
            "time_ms": total_time_ms,
            "breakdown": {
                "depth": depth,
                "rounds": data_per_round,
                "avg_time_per_round_ms": total_time_ms / depth if depth > 0 else 0
            },
            "bottleneck": "latency" if op.msg_size_mb < self.pipeline_threshold_mb else "bandwidth",
            "bandwidth_utilization_gbps": (data_per_gpu_mb * 8 / total_time) if total_time > 0 else 0,
            "efficiency": self._calculate_tree_efficiency(n, op.msg_size_mb, depth)
        }

    def _all_reduce_hierarchical(self, op: CollectiveOperation) -> Dict:
        """
        Hierarchical AllReduce建模

        分两层：
        1. 节点内AllReduce（NVLink）
        2. 节点间AllReduce（NIC）

        特点：
        - 充分利用层级带宽
        - 节点内带宽通常更高
        - 适合多节点场景
        """
        n = op.num_gpus
        gpus_per_node = self.network.gpus_per_node
        num_nodes = self.network.num_nodes

        if num_nodes == 1:
            # 单节点，回退到Ring
            return self._all_reduce_ring(op)

        # 阶段1：节点内AllReduce
        intra_op = CollectiveOperation(
            op_type="all_reduce",
            num_gpus=gpus_per_node,
            msg_size_mb=op.msg_size_mb,
            algorithm=Algorithm.RING
        )
        intra_result = self._all_reduce_ring(intra_op)

        # 阶段2：节点间AllReduce
        # 每个节点代表一个虚拟GPU
        inter_bandwidth = self.network.inter_node_link.bandwidth_bytes_per_sec
        inter_latency_us = self.network.inter_node_link.latency_us

        # 节点间使用Ring算法
        inter_rounds = num_nodes - 1
        chunk_size_mb = op.msg_size_mb / num_nodes
        chunk_size_bytes = chunk_size_mb * 1024 * 1024

        if chunk_size_mb > self.pipeline_threshold_mb:
            inter_time = (inter_rounds * chunk_size_bytes) / inter_bandwidth
        else:
            inter_time = inter_rounds * (chunk_size_bytes / inter_bandwidth + inter_latency_us / 1000)

        # 阶段3：节点内AllGather（结果传播）
        ag_time = intra_result["breakdown"]["all_gather_ms"] / 1000

        total_time_sec = intra_result["breakdown"]["reduce_scatter_ms"] / 1000 + inter_time + ag_time
        total_time_ms = total_time_sec * 1000

        # 瓶颈分析
        intra_time_ms = intra_result["time_ms"]
        inter_time_ms = inter_time * 1000

        if intra_time_ms > inter_time_ms * 1.5:
            bottleneck = "intra_node"
        elif inter_time_ms > intra_time_ms * 1.5:
            bottleneck = "inter_node"
        else:
            bottleneck = "balanced"

        # Hierarchical带宽利用率
        data_per_gpu_mb = 2 * (gpus_per_node - 1) * op.msg_size_mb / gpus_per_node + 2 * (num_nodes - 1) * op.msg_size_mb / num_nodes

        return {
            "time_ms": total_time_ms,
            "breakdown": {
                "intra_node_ms": intra_time_ms,
                "inter_node_ms": inter_time_ms,
                "ratio": inter_time_ms / intra_time_ms if intra_time_ms > 0 else 0
            },
            "bottleneck": bottleneck,
            "bandwidth_utilization_gbps": (data_per_gpu_mb * 8 / total_time_sec) if total_time_sec > 0 else 0,
            "efficiency": self._calculate_hierarchical_efficiency(n, gpus_per_node, num_nodes, op.msg_size_mb)
        }

    def estimate_all_to_all(self, op: CollectiveOperation) -> Dict:
        """估算AllToAll性能"""
        n = op.num_gpus
        msg_per_pair_mb = op.msg_size_mb / n

        if op.algorithm == Algorithm.RING:
            # Ring AllToAll
            rounds = n - 1
            total_data_mb = msg_per_pair_mb * rounds * (n / 2)  # 每轮n/2对通信

            avg_bandwidth = self._calculate_avg_bandwidth(n)
            time_sec = (total_data_mb * 1024 * 1024) / avg_bandwidth

        elif op.algorithm == Algorithm.MESH:
            # Mesh AllToAll
            # 维度分解
            dims = self._factorize(n)
            total_time = 0.0

            for dim in dims:
                chunk_size_mb = op.msg_size_mb / dim
                avg_bandwidth = self._calculate_avg_bandwidth(n)
                time_sec = (chunk_size_mb * 1024 * 1024) / avg_bandwidth
                total_time += time_sec

            time_sec = total_time
        else:
            raise ValueError(f"Unsupported algorithm for AllToAll: {op.algorithm}")

        return {
            "time_ms": time_sec * 1000,
            "breakdown": {
                "total_data_mb": total_data_mb if op.algorithm == Algorithm.RING else op.msg_size_mb,
                "rounds": rounds if op.algorithm == Algorithm.RING else len(dims),
                "algorithm": op.algorithm.value
            },
            "bottleneck": "bandwidth",
            "bandwidth_utilization_gbps": (op.msg_size_mb * 8 / time_sec) if time_sec > 0 else 0
        }

    def estimate_broadcast(self, op: CollectiveOperation) -> Dict:
        """估算Broadcast性能"""
        n = op.num_gpus

        if op.algorithm == Algorithm.TREE:
            # Tree Broadcast: log2(n)轮
            depth = math.ceil(math.log2(n))
            avg_bandwidth = self._calculate_avg_bandwidth(n)
            avg_latency_us = self._calculate_avg_latency(n)

            total_time = 0.0
            for level in range(depth):
                msg_bytes = op.msg_size_mb * 1024 * 1024
                comm_time = msg_bytes / avg_bandwidth + avg_latency_us / 1000
                total_time += comm_time

            time_sec = total_time

        elif op.algorithm == Algorithm.RING:
            # Ring Broadcast: n-1轮
            avg_bandwidth = self._calculate_avg_bandwidth(n)
            msg_bytes = op.msg_size_mb * 1024 * 1024
            time_sec = ((n - 1) * msg_bytes) / avg_bandwidth

        else:
            raise ValueError(f"Unsupported algorithm for Broadcast: {op.algorithm}")

        return {
            "time_ms": time_sec * 1000,
            "breakdown": {
                "algorithm": op.algorithm.value,
                "rounds": math.ceil(math.log2(n)) if op.algorithm == Algorithm.TREE else n - 1
            },
            "bottleneck": "latency" if op.msg_size_mb < self.pipeline_threshold_mb else "bandwidth",
            "bandwidth_utilization_gbps": (op.msg_size_mb * 8 / time_sec) if time_sec > 0 else 0
        }

    def _calculate_avg_bandwidth(self, num_gpus: int) -> float:
        """计算平均有效带宽（考虑拓扑和拥塞）"""
        total_bandwidth = 0.0
        pair_count = 0

        for src in range(num_gpus):
            for dst in range(num_gpus):
                if src != dst:
                    bw = self.network.get_effective_bandwidth(src, dst)
                    total_bandwidth += bw
                    pair_count += 1

        return total_bandwidth / pair_count if pair_count > 0 else self.network.intra_node_link.bandwidth_mbps

    def _calculate_avg_latency(self, num_gpus: int) -> float:
        """计算平均延迟（考虑跳数）"""
        total_latency = 0.0
        pair_count = 0

        for src in range(num_gpus):
            for dst in range(num_gpus):
                if src != dst:
                    hops = self.network.get_hops(src, dst)
                    base_latency = self.network.inter_node_link.latency_us
                    latency = base_latency * hops
                    total_latency += latency
                    pair_count += 1

        return total_latency / pair_count if pair_count > 0 else self.network.inter_node_link.latency_us

    def _calculate_ring_efficiency(self, n: int, chunk_size_mb: float) -> float:
        """计算Ring效率"""
        # 理论最优：n个GPU同时通信
        # 实际：可能有流水线损失
        if chunk_size_mb > self.pipeline_threshold_mb:
            return 0.95  # 大消息，流水线效率高
        else:
            return 0.7 + 0.2 * (chunk_size_mb / self.pipeline_threshold_mb)  # 小消息效率降低

    def _calculate_tree_efficiency(self, n: int, msg_size_mb: float, depth: int) -> float:
        """计算Tree效率"""
        # Tree的效率受深度影响
        base_efficiency = 0.9
        depth_penalty = 0.05 * depth

        if msg_size_mb < self.pipeline_threshold_mb:
            # 小消息，延迟主导
            return base_efficiency - depth_penalty
        else:
            # 大消息，带宽主导
            return min(0.98, base_efficiency - depth_penalty / 2)

    def _calculate_hierarchical_efficiency(self, n: int, gpus_per_node: int,
                                          num_nodes: int, msg_size_mb: float) -> float:
        """计算Hierarchical效率"""
        # 理想情况下，节点内和节点间可以并行
        intra_efficiency = self._calculate_ring_efficiency(gpus_per_node, msg_size_mb / num_nodes)
        inter_efficiency = 0.9  # 节点间效率

        # 综合效率
        return min(0.98, intra_efficiency * inter_efficiency)

    def _factorize(self, n: int) -> List[int]:
        """将n分解为接近的因子（用于Mesh拓扑）"""
        if n <= 4:
            return [n]

        # 找到最接近的因子
        for i in range(int(math.sqrt(n)), 0, -1):
            if n % i == 0:
                return [i, n // i]

        return [n]

    def analyze_bottleneck(self, op: CollectiveOperation, result: Dict) -> Dict:
        """分析性能瓶颈"""
        bottleneck_type = result.get("bottleneck", "unknown")

        if bottleneck_type == "bandwidth":
            suggestion = "增加带宽或使用更高效的算法（如Hierarchical）"
        elif bottleneck_type == "latency":
            suggestion = "减少跳数、使用Tree算法或优化拓扑"
        elif bottleneck_type == "intra_node":
            suggestion = "优化节点内通信（增加NVLink带宽）"
        elif bottleneck_type == "inter_node":
            suggestion = "优化节点间通信（增加NIC带宽或优化拓扑）"
        else:
            suggestion = "平衡的配置，当前较优"

        return {
            "bottleneck_type": bottleneck_type,
            "suggestion": suggestion,
            "utilization": result.get("bandwidth_utilization_gbps", 0),
            "efficiency": result.get("efficiency", 0)
        }


def demo():
    """演示性能建模器"""
    print("=" * 80)
    print("SimAI高级性能建模器 v1.0")
    print("=" * 80)
    print()

    # 场景1：8 GPU单节点
    print("【场景1：8 GPU单节点 - AllReduce, 128 MB】")
    network1 = NetworkConfig(
        intra_node_link=NetworkLink(bandwidth_gbps=25.0, latency_us=2.0),
        inter_node_link=NetworkLink(bandwidth_gbps=25.0, latency_us=1.5),
        topology=Topology.SINGLE_NODE,
        num_nodes=1,
        gpus_per_node=8
    )

    modeler1 = PerformanceModeler(network1)
    op1 = CollectiveOperation("all_reduce", 8, 128.0, Algorithm.RING)
    result1 = modeler1.estimate_all_reduce(op1)

    print(f"Ring AllReduce: {result1['time_ms']:.2f} ms")
    print(f"  瓶颈: {result1['bottleneck']}")
    print(f"  带宽利用率: {result1['bandwidth_utilization_gbps']:.2f} Gbps")
    print(f"  效率: {result1['efficiency']*100:.1f}%")
    print()

    # 场景2：64 GPU多节点
    print("【场景2：64 GPU多节点 - AllReduce, 512 MB】")
    network2 = NetworkConfig(
        intra_node_link=NetworkLink(bandwidth_gbps=50.0, latency_us=2.0),
        inter_node_link=NetworkLink(bandwidth_gbps=25.0, latency_us=1.5),
        topology=Topology.FAT_TREE,
        num_nodes=8,
        gpus_per_node=8
    )

    modeler2 = PerformanceModeler(network2)
    op2 = CollectiveOperation("all_reduce", 64, 512.0, Algorithm.HIERARCHICAL)
    result2 = modeler2.estimate_all_reduce(op2)

    print(f"Hierarchical AllReduce: {result2['time_ms']:.2f} ms")
    print(f"  瓶颈: {result2['bottleneck']}")
    print(f"  节点内时间: {result2['breakdown']['intra_node_ms']:.2f} ms")
    print(f"  节点间时间: {result2['breakdown']['inter_node_ms']:.2f} ms")
    print(f"  带宽利用率: {result2['bandwidth_utilization_gbps']:.2f} Gbps")
    print()

    # 场景3：算法对比
    print("【场景3：算法对比 - 32 GPU, 256 MB】")
    network3 = NetworkConfig(
        intra_node_link=NetworkLink(bandwidth_gbps=50.0, latency_us=2.0),
        inter_node_link=NetworkLink(bandwidth_gbps=25.0, latency_us=1.5),
        topology=Topology.FAT_TREE,
        num_nodes=4,
        gpus_per_node=8
    )

    modeler3 = PerformanceModeler(network3)
    op3 = CollectiveOperation("all_reduce", 32, 256.0, Algorithm.RING)

    algorithms = [Algorithm.RING, Algorithm.TREE, Algorithm.HIERARCHICAL]
    print(f"{'算法':<15} {'时间(ms)':<12} {'瓶颈':<12} {'效率':<10}")
    print("-" * 55)

    for algo in algorithms:
        op3.algorithm = algo
        result = modeler3.estimate_all_reduce(op3)
        print(f"{algo.value:<15} {result['time_ms']:<12.2f} {result['bottleneck']:<12} {result['efficiency']*100:<10.1f}%")

    print()
    print("=" * 80)


if __name__ == "__main__":
    demo()

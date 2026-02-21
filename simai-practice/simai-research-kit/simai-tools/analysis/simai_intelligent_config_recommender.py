#!/usr/bin/env python3
"""
SimAI智能配置推荐器 v1.0
基于workload特征推荐最优系统配置和算法选择

Author: 二愣子
Date: 2026-02-19
"""

import json
import os
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
from enum import Enum


class WorkloadType(Enum):
    """Workload类型分类"""
    TRAINING = "training"
    INFERENCE = "inference"
    MOE_TRAINING = "moe_training"
    MOE_INFERENCE = "moe_inference"


class CollectiveOp(Enum):
    """集合通信操作类型"""
    ALL_REDUCE = "all_reduce"
    ALL_TO_ALL = "all_to_all"
    BROADCAST = "broadcast"
    ALL_GATHER = "all_gather"
    REDUCE_SCATTER = "reduce_scatter"
    REDUCE = "reduce"
    GATHER = "gather"
    SCATTER = "scatter"


class AlgorithmType(Enum):
    """算法类型"""
    TREE = "tree"
    RING = "ring"
    HIERARCHICAL = "hierarchical"
    AUTO = "auto"


@dataclass
class WorkloadCharacteristics:
    """Workload特征"""
    num_gpus: int
    msg_size_mb: float
    collective_ops: List[CollectiveOp]
    workload_type: WorkloadType
    iteration_count: int = 1
    compute_intensity: float = 1.0  # 计算强度（计算/通信比）


@dataclass
class NetworkConfig:
    """网络配置"""
    nvlink_bandwidth_gbps: float = 25.0  # NVLink带宽
    nvlink_latency_us: float = 2.0  # NVLink延迟
    nic_bandwidth_gbps: float = 25.0  # NIC带宽
    nic_latency_us: float = 1.5  # NIC延迟
    topology: str = "fat-tree"  # 网络拓扑


@dataclass
class AlgorithmConfig:
    """算法配置"""
    all_reduce_algo: AlgorithmType = AlgorithmType.AUTO
    all_to_all_algo: AlgorithmType = AlgorithmType.AUTO
    broadcast_algo: AlgorithmType = AlgorithmType.TREE
    other_algos: AlgorithmType = AlgorithmType.RING


@dataclass
class Recommendation:
    """推荐结果"""
    workload_desc: str
    recommended_network: NetworkConfig
    recommended_algorithm: AlgorithmConfig
    estimated_time_ms: float
    confidence: float  # 置信度（0-1）
    rationale: List[str]  # 推荐理由
    alternatives: List[Dict] = field(default_factory=list)  # 备选方案
    performance_prediction: Dict = field(default_factory=dict)


class SimAIConfigRecommender:
    """SimAI智能配置推荐器"""
    
    def __init__(self):
        self.rules = self._init_rules()
        self.performance_models = self._init_performance_models()
    
    def _init_rules(self) -> Dict:
        """初始化推荐规则"""
        return {
            "small_scale_rules": {
                "max_gpus": 8,
                "max_msg_mb": 128,
                "recommendations": {
                    "network": {
                        "nvlink_bandwidth_gbps": 25.0,
                        "nvlink_latency_us": 2.0,
                        "topology": "single-node"
                    },
                    "algorithm": {
                        "all_reduce_algo": AlgorithmType.RING,
                        "broadcast_algo": AlgorithmType.TREE
                    },
                    "rationale": [
                        "小规模场景，通信开销小",
                        "Ring算法在小规模下效率高",
                        "单节点拓扑降低延迟"
                    ]
                }
            },
            "medium_scale_rules": {
                "min_gpus": 8,
                "max_gpus": 64,
                "max_msg_mb": 512,
                "recommendations": {
                    "network": {
                        "nvlink_bandwidth_gbps": 25.0,
                        "nvlink_latency_us": 2.0,
                        "nic_bandwidth_gbps": 25.0,
                        "nic_latency_us": 1.5,
                        "topology": "fat-tree"
                    },
                    "algorithm": {
                        "all_reduce_algo": AlgorithmType.HIERARCHICAL,
                        "all_to_all_algo": AlgorithmType.RING,
                        "broadcast_algo": AlgorithmType.TREE
                    },
                    "rationale": [
                        "中等规模，需要层次化优化",
                        "Hierarchical算法平衡跨节点通信",
                        "Fat-tree拓扑提供均衡带宽"
                    ]
                }
            },
            "large_scale_rules": {
                "min_gpus": 64,
                "recommendations": {
                    "network": {
                        "nvlink_bandwidth_gbps": 50.0,  # NVLink 2.0
                        "nvlink_latency_us": 1.5,
                        "nic_bandwidth_gbps": 50.0,
                        "nic_latency_us": 1.0,
                        "topology": "dragonfly"
                    },
                    "algorithm": {
                        "all_reduce_algo": AlgorithmType.HIERARCHICAL,
                        "all_to_all_algo": AlgorithmType.HIERARCHICAL,
                        "broadcast_algo": AlgorithmType.TREE
                    },
                    "rationale": [
                        "大规模场景，需要最大带宽",
                        "Hierarchical算法最小化跨节点流量",
                        "Dragonfly拓扑降低跳数"
                    ]
                }
            },
            "high_bandwidth_rules": {
                "msg_mb_threshold": 1024,  # >1GB消息
                "recommendations": {
                    "network": {
                        "nvlink_bandwidth_gbps": 50.0,
                        "nic_bandwidth_gbps": 100.0,
                        "topology": "hybrid"
                    },
                    "algorithm": {
                        "all_reduce_algo": AlgorithmType.TREE,  # Tree在大消息下更好
                        "all_to_all_algo": AlgorithmType.HIERARCHICAL
                    },
                    "rationale": [
                        "大消息需要高带宽",
                        "Tree算法减少大消息的通信步数",
                        "混合拓扑优化成本和性能"
                    ]
                }
            },
            "low_latency_rules": {
                "msg_mb_threshold": 16,  # <16MB消息
                "recommendations": {
                    "algorithm": {
                        "all_reduce_algo": AlgorithmType.RING,
                        "broadcast_algo": AlgorithmType.TREE
                    },
                    "rationale": [
                        "小消息优化延迟",
                        "Ring算法在小消息下延迟最低"
                    ]
                }
            },
            "moe_rules": {
                "workload_types": [WorkloadType.MOE_TRAINING, WorkloadType.MOE_INFERENCE],
                "recommendations": {
                    "algorithm": {
                        "all_reduce_algo": AlgorithmType.HIERARCHICAL,
                        "all_to_all_algo": AlgorithmType.HIERARCHICAL  # MoE依赖AllToAll
                    },
                    "rationale": [
                        "MoE模型需要大量AllToAll通信",
                        "Hierarchical AllToAll优化跨节点通信",
                        "需要特别注意AllToAll性能"
                    ]
                }
            }
        }
    
    def _init_performance_models(self) -> Dict:
        """初始化性能预测模型"""
        return {
            "all_reduce_time": lambda n_gpus, msg_mb, bw_gbps: self._calc_all_reduce_time(n_gpus, msg_mb, bw_gbps),
            "all_to_all_time": lambda n_gpus, msg_mb, bw_gbps: self._calc_all_to_all_time(n_gpus, msg_mb, bw_gbps),
            "broadcast_time": lambda n_gpus, msg_mb, bw_gbps, lat_us: self._calc_broadcast_time(n_gpus, msg_mb, bw_gbps, lat_us),
        }
    
    def _calc_all_reduce_time(self, n_gpus: int, msg_mb: float, bw_gbps: float) -> float:
        """计算AllReduce时间（简化模型）"""
        # Ring: 2 * (n-1) * msg_size / bandwidth
        # Tree: 2 * log2(n) * msg_size / bandwidth
        # Hierarchical: 结合两者
        
        if n_gpus <= 8:
            # Ring算法
            return 2 * (n_gpus - 1) * msg_mb * 8 / bw_gbps
        elif n_gpus <= 64:
            # Hierarchical算法
            intra_time = 2 * (8 - 1) * msg_mb * 8 / bw_gbps
            inter_time = 2 * (n_gpus // 8) * msg_mb * 8 / bw_gbps
            return intra_time + inter_time
        else:
            # 完全Hierarchical
            intra_time = 2 * (8 - 1) * msg_mb * 8 / bw_gbps
            inter_time = 2 * (n_gpus // 8) * msg_mb * 8 / bw_gbps
            return intra_time + inter_time
    
    def _calc_all_to_all_time(self, n_gpus: int, msg_mb: float, bw_gbps: float) -> float:
        """计算AllToAll时间"""
        # AllToAll: (n-1) * msg_size / bandwidth
        return (n_gpus - 1) * msg_mb * 8 / bw_gbps
    
    def _calc_broadcast_time(self, n_gpus: int, msg_mb: float, bw_gbps: float, lat_us: float) -> float:
        """计算Broadcast时间"""
        # Tree: log2(n) * (msg_size / bandwidth + latency)
        import math
        steps = math.log2(n_gpus)
        return steps * (msg_mb * 8 / bw_gbps + lat_us / 1000)
    
    def analyze_workload(self, workload_path: str) -> WorkloadCharacteristics:
        """分析workload文件并提取特征"""
        collective_ops_set = set()
        total_msg_size = 0
        op_count = 0
        num_gpus = 8  # 默认值
        
        with open(workload_path, 'r') as f:
            for line in f:
                line = line.strip()
                
                # 跳过注释和空行
                if not line or line.startswith('#'):
                    continue
                
                # 解析GPU数量（从workload头）
                if 'all_gpus:' in line:
                    import re
                    gpu_match = re.search(r'all_gpus:\s*(\d+)', line)
                    if gpu_match:
                        num_gpus = int(gpu_match.group(1))
                
                # 解析操作数量行
                if line.isdigit():
                    continue
                
                # 解析集合通信操作（SimAI格式）
                # 格式: operation_name -1 100000 OP_TYPE msg_size 1 NONE 0 1 NONE 0 1
                parts = line.split()
                if len(parts) >= 5:
                    op_type = parts[3].upper()
                    
                    # 识别操作类型
                    for op in CollectiveOp:
                        if op.value.upper() == op_type or op.value.replace('_', '').upper() == op_type.replace('_', ''):
                            collective_ops_set.add(op)
                            break
                    
                    # 提取消息大小（第5列，字节转换为MB）
                    try:
                        msg_size_bytes = int(parts[4])
                        total_msg_size += msg_size_bytes / (1024 * 1024)  # 转换为MB
                        op_count += 1
                    except (ValueError, IndexError):
                        continue
        
        # 如果没有找到任何操作，尝试从文件名推断
        if not collective_ops_set:
            import re
            filename = workload_path.lower()
            if 'allreduce' in filename or 'all_reduce' in filename:
                collective_ops_set.add(CollectiveOp.ALL_REDUCE)
            if 'alltoall' in filename or 'all_to_all' in filename:
                collective_ops_set.add(CollectiveOp.ALL_TO_ALL)
            if 'broadcast' in filename:
                collective_ops_set.add(CollectiveOp.BROADCAST)
            if 'allgather' in filename or 'all_gather' in filename:
                collective_ops_set.add(CollectiveOp.ALL_GATHER)
        
        # 如果还是没有，使用默认值
        if not collective_ops_set:
            collective_ops_set.add(CollectiveOp.ALL_REDUCE)
        
        # 推断workload类型
        workload_type = WorkloadType.TRAINING
        if CollectiveOp.ALL_TO_ALL in collective_ops_set:
            workload_type = WorkloadType.MOE_TRAINING
        elif 'inference' in workload_path.lower():
            workload_type = WorkloadType.INFERENCE
        
        # 计算平均消息大小
        avg_msg_size = total_msg_size / op_count if op_count > 0 else 100
        
        # 从文件名推断GPU数量（如果还没找到）
        if num_gpus == 8:
            import re
            gpu_match = re.search(r'(\d+)gpu', workload_path, re.IGNORECASE)
            if gpu_match:
                num_gpus = int(gpu_match.group(1))
        
        return WorkloadCharacteristics(
            num_gpus=num_gpus,
            msg_size_mb=avg_msg_size,
            collective_ops=list(collective_ops_set),
            workload_type=workload_type,
            iteration_count=1,  # 默认1次迭代
            compute_intensity=1.0  # 默认值
        )
    
    def recommend(self, workload_chars: WorkloadCharacteristics) -> Recommendation:
        """基于workload特征推荐配置"""
        recommendations = []
        rationale = []
        confidence = 0.8
        alternatives = []
        
        # 1. 确定规模类别
        scale_category = self._classify_scale(workload_chars)
        
        # 2. 应用规模规则
        scale_rule = self.rules.get(f"{scale_category}_scale_rules")
        if scale_rule:
            recommendations.append(scale_rule["recommendations"])
            rationale.extend(scale_rule["recommendations"].get("rationale", []))
        
        # 3. 应用消息大小规则
        if workload_chars.msg_size_mb > self.rules["high_bandwidth_rules"]["msg_mb_threshold"]:
            recommendations.append(self.rules["high_bandwidth_rules"]["recommendations"])
            rationale.extend(self.rules["high_bandwidth_rules"]["recommendations"]["rationale"])
            confidence += 0.1
        elif workload_chars.msg_size_mb < self.rules["low_latency_rules"]["msg_mb_threshold"]:
            recommendations.append(self.rules["low_latency_rules"]["recommendations"])
            rationale.extend(self.rules["low_latency_rules"]["recommendations"]["rationale"])
        
        # 4. 应用Workload类型规则
        if workload_chars.workload_type in self.rules["moe_rules"]["workload_types"]:
            recommendations.append(self.rules["moe_rules"]["recommendations"])
            rationale.extend(self.rules["moe_rules"]["recommendations"]["rationale"])
            confidence += 0.1
        
        # 5. 合并推荐
        network_config = NetworkConfig()
        algorithm_config = AlgorithmConfig()
        
        for rec in recommendations:
            if "network" in rec:
                for key, value in rec["network"].items():
                    setattr(network_config, key, value)
            if "algorithm" in rec:
                for key, value in rec["algorithm"].items():
                    setattr(algorithm_config, key, value)
        
        # 6. 预测性能
        performance_prediction = self._predict_performance(
            workload_chars, network_config, algorithm_config
        )
        
        # 7. 生成备选方案
        alternatives = self._generate_alternatives(
            workload_chars, network_config, algorithm_config
        )
        
        # 8. 生成workload描述
        workload_desc = self._generate_workload_description(workload_chars)
        
        # 9. 限制置信度范围
        confidence = min(1.0, confidence)
        
        return Recommendation(
            workload_desc=workload_desc,
            recommended_network=network_config,
            recommended_algorithm=algorithm_config,
            estimated_time_ms=performance_prediction.get("total_time_ms", 0),
            confidence=confidence,
            rationale=list(set(rationale)),  # 去重
            alternatives=alternatives,
            performance_prediction=performance_prediction
        )
    
    def _classify_scale(self, chars: WorkloadCharacteristics) -> str:
        """分类workload规模"""
        if chars.num_gpus <= self.rules["small_scale_rules"]["max_gpus"]:
            return "small"
        elif chars.num_gpus <= self.rules["medium_scale_rules"]["max_gpus"]:
            return "medium"
        else:
            return "large"
    
    def _predict_performance(
        self, 
        chars: WorkloadCharacteristics,
        network: NetworkConfig,
        algorithm: AlgorithmConfig
    ) -> Dict:
        """预测性能"""
        total_time = 0.0
        op_times = {}
        
        # 对每个集合通信操作预测时间
        effective_bw = network.nvlink_bandwidth_gbps  # 简化：使用NVLink带宽
        
        for op in chars.collective_ops:
            if op == CollectiveOp.ALL_REDUCE:
                time_ms = self.performance_models["all_reduce_time"](
                    chars.num_gpus, chars.msg_size_mb, effective_bw
                )
                op_times["all_reduce"] = time_ms
            elif op == CollectiveOp.ALL_TO_ALL:
                time_ms = self.performance_models["all_to_all_time"](
                    chars.num_gpus, chars.msg_size_mb, effective_bw
                )
                op_times["all_to_all"] = time_ms
            elif op == CollectiveOp.BROADCAST:
                time_ms = self.performance_models["broadcast_time"](
                    chars.num_gpus, chars.msg_size_mb, effective_bw, network.nvlink_latency_us
                )
                op_times["broadcast"] = time_ms
            
            total_time += time_ms
        
        # 乘以迭代次数
        total_time *= chars.iteration_count
        
        return {
            "total_time_ms": total_time,
            "op_times_ms": op_times,
            "per_iteration_ms": total_time / chars.iteration_count if chars.iteration_count > 0 else 0,
            "estimated_throughput_gbps": chars.msg_size_mb * chars.iteration_count * 8 / (total_time / 1000) if total_time > 0 else 0
        }
    
    def _generate_alternatives(
        self,
        chars: WorkloadCharacteristics,
        network: NetworkConfig,
        algorithm: AlgorithmConfig
    ) -> List[Dict]:
        """生成备选方案"""
        alternatives = []
        
        # 备选1：更高带宽配置
        alt_network = NetworkConfig(
            nvlink_bandwidth_gbps=network.nvlink_bandwidth_gbps * 2,
            nic_bandwidth_gbps=network.nic_bandwidth_gbps * 2,
            topology=network.topology
        )
        alt_perf = self._predict_performance(chars, alt_network, algorithm)
        alternatives.append({
            "name": "高性能配置",
            "description": "双倍带宽，更快速度",
            "network_config": alt_network.__dict__,
            "estimated_time_ms": alt_perf["total_time_ms"],
            "cost_factor": 2.0  # 成本倍数
        })
        
        # 备选2：更低成本配置
        alt_network2 = NetworkConfig(
            nvlink_bandwidth_gbps=network.nvlink_bandwidth_gbps / 2,
            nic_bandwidth_gbps=network.nic_bandwidth_gbps / 2,
            topology=network.topology
        )
        alt_perf2 = self._predict_performance(chars, alt_network2, algorithm)
        alternatives.append({
            "name": "经济配置",
            "description": "减半带宽，降低成本",
            "network_config": alt_network2.__dict__,
            "estimated_time_ms": alt_perf2["total_time_ms"],
            "cost_factor": 0.5
        })
        
        # 备选3：不同算法
        alt_algorithm = AlgorithmConfig(
            all_reduce_algo=AlgorithmType.TREE if algorithm.all_reduce_algo != AlgorithmType.TREE else AlgorithmType.RING
        )
        alt_perf3 = self._predict_performance(chars, network, alt_algorithm)
        alternatives.append({
            "name": "替代算法",
            "description": f"使用{alt_algorithm.all_reduce_algo.value}算法",
            "algorithm_config": {
                "all_reduce_algo": alt_algorithm.all_reduce_algo.value
            },
            "estimated_time_ms": alt_perf3["total_time_ms"],
            "cost_factor": 1.0
        })
        
        return alternatives
    
    def _generate_workload_description(self, chars: WorkloadCharacteristics) -> str:
        """生成workload描述"""
        type_name = {
            WorkloadType.TRAINING: "标准训练",
            WorkloadType.INFERENCE: "推理",
            WorkloadType.MOE_TRAINING: "MoE训练",
            WorkloadType.MOE_INFERENCE: "MoE推理"
        }[chars.workload_type]
        
        ops_str = ", ".join([op.value for op in chars.collective_ops])
        
        return (f"{type_name}工作负载 | "
                f"GPU数量: {chars.num_gpus} | "
                f"消息大小: {chars.msg_size_mb:.1f} MB | "
                f"集合通信: [{ops_str}] | "
                f"迭代次数: {chars.iteration_count}")
    
    def save_recommendation(self, recommendation: Recommendation, output_path: str):
        """保存推荐结果"""
        output = {
            "workload_description": recommendation.workload_desc,
            "recommended_network_config": {
                "nvlink_bandwidth_gbps": recommendation.recommended_network.nvlink_bandwidth_gbps,
                "nvlink_latency_us": recommendation.recommended_network.nvlink_latency_us,
                "nic_bandwidth_gbps": recommendation.recommended_network.nic_bandwidth_gbps,
                "nic_latency_us": recommendation.recommended_network.nic_latency_us,
                "topology": recommendation.recommended_network.topology
            },
            "recommended_algorithm_config": {
                "all_reduce_algo": recommendation.recommended_algorithm.all_reduce_algo.value,
                "all_to_all_algo": recommendation.recommended_algorithm.all_to_all_algo.value,
                "broadcast_algo": recommendation.recommended_algorithm.broadcast_algo.value
            },
            "performance_prediction": {
                "estimated_time_ms": round(recommendation.estimated_time_ms, 2),
                "details": recommendation.performance_prediction
            },
            "confidence": round(recommendation.confidence, 2),
            "rationale": recommendation.rationale,
            "alternatives": recommendation.alternatives
        }
        
        # 保存JSON
        json_path = output_path.replace('.md', '.json')
        with open(json_path, 'w') as f:
            json.dump(output, f, indent=2)
        
        # 保存Markdown报告
        with open(output_path, 'w') as f:
            f.write(f"# SimAI配置推荐报告\n\n")
            f.write(f"## Workload特征\n\n")
            f.write(f"**{recommendation.workload_desc}**\n\n")
            
            f.write(f"## 推荐配置\n\n")
            f.write(f"### 网络配置\n\n")
            f.write(f"- **NVLink带宽**: {recommendation.recommended_network.nvlink_bandwidth_gbps} Gbps\n")
            f.write(f"- **NVLink延迟**: {recommendation.recommended_network.nvlink_latency_us} μs\n")
            f.write(f"- **NIC带宽**: {recommendation.recommended_network.nic_bandwidth_gbps} Gbps\n")
            f.write(f"- **NIC延迟**: {recommendation.recommended_network.nic_latency_us} μs\n")
            f.write(f"- **网络拓扑**: {recommendation.recommended_network.topology}\n\n")
            
            f.write(f"### 算法配置\n\n")
            f.write(f"- **AllReduce算法**: {recommendation.recommended_algorithm.all_reduce_algo.value}\n")
            f.write(f"- **AllToAll算法**: {recommendation.recommended_algorithm.all_to_all_algo.value}\n")
            f.write(f"- **Broadcast算法**: {recommendation.recommended_algorithm.broadcast_algo.value}\n\n")
            
            f.write(f"## 性能预测\n\n")
            f.write(f"- **预估时间**: {recommendation.estimated_time_ms:.2f} ms\n")
            f.write(f"- **每次迭代**: {recommendation.performance_prediction.get('per_iteration_ms', 0):.2f} ms\n")
            f.write(f"- **预估吞吐**: {recommendation.performance_prediction.get('estimated_throughput_gbps', 0):.2f} Gbps\n\n")
            
            f.write(f"## 推荐理由\n\n")
            for i, reason in enumerate(recommendation.rationale, 1):
                f.write(f"{i}. {reason}\n")
            f.write("\n")
            
            f.write(f"## 置信度\n\n")
            confidence_bar = "█" * int(recommendation.confidence * 10)
            f.write(f"{confidence_bar} {recommendation.confidence:.0%}\n\n")
            
            f.write(f"## 备选方案\n\n")
            for alt in recommendation.alternatives:
                f.write(f"### {alt['name']}\n\n")
                f.write(f"**描述**: {alt['description']}\n\n")
                f.write(f"**预估时间**: {alt['estimated_time_ms']:.2f} ms\n")
                f.write(f"**成本系数**: {alt['cost_factor']}x\n\n")
        
        print(f"✅ 推荐报告已保存:")
        print(f"   - {json_path} (JSON)")
        print(f"   - {output_path} (Markdown)")


def main():
    """主函数"""
    import sys
    
    print("🤖 SimAI智能配置推荐器 v1.0")
    print("=" * 60)
    
    recommender = SimAIConfigRecommender()
    
    # 检查命令行参数
    if len(sys.argv) < 2:
        print("\n使用方法:")
        print(f"  {sys.argv[0]} <workload_file> [output_prefix]")
        print("\n示例:")
        print(f"  {sys.argv[0]} example/gpt_1024gpu.workload")
        print(f"  {sys.argv[0]} priority1_workloads/allreduce_128mb.workload gpt_128")
        print("\n如果未指定workload文件，将使用演示模式...")
        
        # 演示模式：创建示例workload特征
        print("\n📊 演示模式：展示不同规模的推荐")
        print("-" * 60)
        
        demo_cases = [
            WorkloadCharacteristics(
                num_gpus=4,
                msg_size_mb=32,
                collective_ops=[CollectiveOp.ALL_REDUCE],
                workload_type=WorkloadType.TRAINING,
                iteration_count=100
            ),
            WorkloadCharacteristics(
                num_gpus=64,
                msg_size_mb=256,
                collective_ops=[CollectiveOp.ALL_REDUCE, CollectiveOp.ALL_TO_ALL],
                workload_type=WorkloadType.MOE_TRAINING,
                iteration_count=1000
            ),
            WorkloadCharacteristics(
                num_gpus=1024,
                msg_size_mb=1024,
                collective_ops=[CollectiveOp.ALL_REDUCE, CollectiveOp.BROADCAST],
                workload_type=WorkloadType.TRAINING,
                iteration_count=10000
            )
        ]
        
        for i, chars in enumerate(demo_cases, 1):
            print(f"\n【案例 {i}】")
            rec = recommender.recommend(chars)
            print(f"Workload: {rec.workload_desc}")
            print(f"推荐拓扑: {rec.recommended_network.topology}")
            print(f"推荐算法: {rec.recommended_algorithm.all_reduce_algo.value}")
            print(f"预估时间: {rec.estimated_time_ms:.2f} ms")
            print(f"置信度: {rec.confidence:.0%}")
        
        print("\n" + "=" * 60)
        print("✅ 演示完成！")
        return
    
    workload_path = sys.argv[1]
    output_prefix = sys.argv[2] if len(sys.argv) > 2 else "recommendation"
    
    # 检查文件是否存在
    if not os.path.exists(workload_path):
        print(f"❌ 错误: 文件不存在: {workload_path}")
        return
    
    # 分析workload
    print(f"\n📂 分析workload: {workload_path}")
    chars = recommender.analyze_workload(workload_path)
    
    # 生成推荐
    print("🔍 生成推荐配置...")
    recommendation = recommender.recommend(chars)
    
    # 保存结果
    output_dir = "simai_recommendations"
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = f"{output_dir}/{output_prefix}_recommendation.md"
    recommender.save_recommendation(recommendation, output_path)
    
    # 打印摘要
    print("\n" + "=" * 60)
    print("📋 推荐摘要")
    print("=" * 60)
    print(f"Workload: {recommendation.workload_desc}")
    print(f"\n推荐配置:")
    print(f"  - 网络拓扑: {recommendation.recommended_network.topology}")
    print(f"  - NVLink带宽: {recommendation.recommended_network.nvlink_bandwidth_gbps} Gbps")
    print(f"  - AllReduce算法: {recommendation.recommended_algorithm.all_reduce_algo.value}")
    print(f"\n性能预测:")
    print(f"  - 预估时间: {recommendation.estimated_time_ms:.2f} ms")
    print(f"  - 置信度: {recommendation.confidence:.0%}")
    print(f"\n推荐理由:")
    for i, reason in enumerate(recommendation.rationale[:3], 1):
        print(f"  {i}. {reason}")
    print("=" * 60)


if __name__ == "__main__":
    main()

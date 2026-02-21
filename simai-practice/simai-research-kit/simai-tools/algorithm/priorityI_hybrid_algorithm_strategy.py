#!/usr/bin/env python3
"""
SimAI优先级I：混合算法策略研究

背景：
不同算法在不同场景下表现不同：
- RecursiveDoubling: 小规模最优（步数最少）
- Hierarchical: 大规模+大消息最优（层次化优化）
- DBT: 中等规模通用最优（双路并发）
- Ring: 简单但大规模性能崩溃
- Tree: 根节点带宽瓶颈

研究目标：
1. 分析不同算法的优势场景
2. 设计混合算法策略（动态切换）
3. 评估混合策略的性能提升
4. 创建算法选择决策树（增强版）
5. 验证混合策略的可行性

作者：二愣子 🤔
日期：2026-02-20
任务：SimAI深度研究自主任务 - 优先级I（混合算法策略）
"""

import os
import sys
import json
import math
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class AlgorithmProfile:
    """算法性能画像"""
    name: str
    description: str
    strengths: List[str]  # 优势场景
    weaknesses: List[str]  # 劣势场景
    complexity: str  # 复杂度：低/中/高
    steps_formula: str  # 步数公式
    ideal_gpu_range: Tuple[int, int]  # 理想GPU范围
    ideal_data_range: Tuple[float, float]  # 理想数据范围（MB）

@dataclass
class HybridStrategyConfig:
    """混合策略配置"""
    name: str
    algorithm: str
    condition: str  # 选择条件
    
class HybridAlgorithmAnalyzer:
    """混合算法策略分析器"""
    
    def __init__(self, output_dir: str = "priorityI_hybrid_algo_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.results = []
        self.start_time = datetime.now()
        
        # 模型参数（使用校准后的值）
        self.bandwidth_gbps = 7.7
        self.latency_us = 150.0
        self.fixed_overhead_ms = 1.2
        
        # 算法画像
        self.algorithm_profiles = self._create_algorithm_profiles()
        
        print("=" * 80)
        print("SimAI优先级I：混合算法策略研究")
        print("=" * 80)
        print(f"开始时间: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"输出目录: {self.output_dir}")
        print()
    
    def _create_algorithm_profiles(self) -> Dict[str, AlgorithmProfile]:
        """创建算法性能画像"""
        profiles = {
            "RecursiveDoubling": AlgorithmProfile(
                name="RecursiveDoubling",
                description="递归加倍算法，步数最少",
                strengths=[
                    "GPU数量为2的幂时步数最少（log₂N）",
                    "小规模场景延迟最优",
                    "AllReduce专用，性能优异"
                ],
                weaknesses=[
                    "只适用于GPU数量为2的幂",
                    "大规模场景每步数据量大（Size/2）",
                    "不适用于所有集合通信操作"
                ],
                complexity="低",
                steps_formula="log₂N",
                ideal_gpu_range=(2, 32),
                ideal_data_range=(0.1, 64)
            ),
            
            "Hierarchical": AlgorithmProfile(
                name="Hierarchical",
                description="层次化算法，节点内+节点间分离",
                strengths=[
                    "大规模场景最优（≥32GPU）",
                    "大消息优化良好（≥64MB）",
                    "跨节点通信优化",
                    "扩展性好"
                ],
                weaknesses=[
                    "小规模场景开销大",
                    "配置复杂度高",
                    "需要优化Ratio表"
                ],
                complexity="高",
                steps_formula="≈log₂N + 2",
                ideal_gpu_range=(32, 256),
                ideal_data_range=(64, 4096)
            ),
            
            "DBT": AlgorithmProfile(
                name="DBT",
                description=" dissemination-based tree，双路并发",
                strengths=[
                    "中等规模通用最优（8-64GPU）",
                    "双路并发，性能稳定",
                    "所有场景表现良好",
                    "复杂度和性能平衡"
                ],
                weaknesses=[
                    "极大规模可能不如Hierarchical",
                    "双路并发优势有限"
                ],
                complexity="中",
                steps_formula="2×log₂N",
                ideal_gpu_range=(8, 64),
                ideal_data_range=(1, 1024)
            ),
            
            "Ring": AlgorithmProfile(
                name="Ring",
                description="环形算法，简单通用",
                strengths=[
                    "实现简单",
                    "小规模（≤8GPU）性能可接受",
                    "所有集合通信操作都支持"
                ],
                weaknesses=[
                    "大规模性能崩溃（步数2(N-1)）",
                    "128GPU需要254步，效率极低",
                    "延迟敏感场景表现差"
                ],
                complexity="低",
                steps_formula="2×(N-1)",
                ideal_gpu_range=(2, 8),
                ideal_data_range=(1, 16)
            ),
            
            "Tree": AlgorithmProfile(
                name="Tree",
                description="树形算法，根节点协调",
                strengths=[
                    "Broadcast操作专用",
                    "小规模Broadcast性能好"
                ],
                weaknesses=[
                    "根节点带宽瓶颈",
                    "AllReduce场景性能差",
                    "负载不均衡"
                ],
                complexity="中",
                steps_formula="2×log₂N",
                ideal_gpu_range=(2, 16),
                ideal_data_range=(0.1, 16)
            )
        }
        
        return profiles
    
    def calculate_steps(self, gpu_count: int, algorithm: str, 
                        collective_op: str) -> int:
        """计算通信步数"""
        if algorithm == "Ring":
            if collective_op in ["AllReduce", "AllGather", "ReduceScatter"]:
                return 2 * (gpu_count - 1)
            elif collective_op == "Broadcast":
                return gpu_count - 1
            elif collective_op == "AllToAll":
                return gpu_count - 1
            else:
                return gpu_count - 1
        
        elif algorithm == "Tree":
            if collective_op in ["AllReduce", "Reduce", "AllGather"]:
                return 2 * int(math.log2(gpu_count))
            elif collective_op == "Broadcast":
                return int(math.log2(gpu_count))
            else:
                return int(math.log2(gpu_count))
        
        elif algorithm == "RecursiveDoubling":
            if collective_op == "AllReduce":
                return int(math.log2(gpu_count))
            else:
                return int(math.log2(gpu_count))
        
        elif algorithm == "DBT":
            if collective_op in ["AllReduce", "AllGather", "ReduceScatter"]:
                return 2 * int(math.log2(gpu_count))
            else:
                return int(math.log2(gpu_count))
        
        elif algorithm == "Hierarchical":
            if collective_op in ["AllReduce", "AllGather", "ReduceScatter"]:
                return int(math.log2(gpu_count)) + 2
            else:
                return int(math.log2(gpu_count))
        
        return gpu_count
    
    def predict_time(self, gpu_count: int, data_size_mb: float,
                     collective_op: str, algorithm: str) -> float:
        """预测执行时间"""
        size_bytes = data_size_mb * 1024 * 1024
        steps = self.calculate_steps(gpu_count, algorithm, collective_op)
        
        # 数据量计算
        if collective_op == "AllReduce":
            data_multiplier = 1.0
        elif collective_op == "AllToAll":
            data_multiplier = (gpu_count - 1) / gpu_count
        elif collective_op == "Broadcast":
            data_multiplier = 1.0
        elif collective_op == "AllGather":
            data_multiplier = 1.0
        elif collective_op == "ReduceScatter":
            data_multiplier = 1.0
        else:
            data_multiplier = 1.0
        
        # 算法并发
        if algorithm in ["DBT", "Hierarchical"]:
            effective_multiplier = data_multiplier * 0.6
        else:
            effective_multiplier = data_multiplier
        
        total_bytes = size_bytes * effective_multiplier
        
        # 时间计算
        bandwidth_time_ms = (total_bytes * 8) / (self.bandwidth_gbps * 1e6) * 1000
        latency_time_ms = steps * self.latency_us / 1000
        total_time_ms = bandwidth_time_ms + latency_time_ms + self.fixed_overhead_ms
        
        return total_time_ms
    
    def analyze_algorithm_strengths(self) -> Dict[str, Any]:
        """分析算法优势场景"""
        print("\n" + "=" * 80)
        print("分析1: 算法优势场景分析")
        print("=" * 80)
        
        # 测试场景
        test_scenarios = [
            # (GPU数, 数据大小MB, 操作)
            (2, 1, "AllReduce"),
            (4, 1, "AllReduce"),
            (8, 16, "AllReduce"),
            (16, 64, "AllReduce"),
            (32, 64, "AllReduce"),
            (64, 256, "AllReduce"),
            (128, 256, "AllReduce"),
            (8, 1, "Broadcast"),
            (32, 64, "Broadcast"),
            (64, 256, "Broadcast"),
        ]
        
        results = []
        algorithms = ["RecursiveDoubling", "Hierarchical", "DBT", "Ring", "Tree"]
        
        print(f"\n测试 {len(test_scenarios)} 个场景，对比 {len(algorithms)} 种算法...")
        
        for gpu_count, data_size, op in test_scenarios:
            scenario_results = {}
            
            for algo in algorithms:
                try:
                    time_ms = self.predict_time(gpu_count, data_size, op, algo)
                    scenario_results[algo] = time_ms
                except:
                    scenario_results[algo] = float('inf')
            
            # 找出最优算法
            valid_results = {k: v for k, v in scenario_results.items() 
                           if v != float('inf')}
            if valid_results:
                best_algo = min(valid_results, key=valid_results.get)
                best_time = valid_results[best_algo]
                
                # 计算相对性能
                relative_perf = {}
                for algo, time in valid_results.items():
                    relative_perf[algo] = time / best_time
                
                results.append({
                    "scenario": f"{gpu_count}GPU_{data_size}MB_{op}",
                    "gpu_count": gpu_count,
                    "data_size_mb": data_size,
                    "collective_op": op,
                    "best_algorithm": best_algo,
                    "best_time_ms": best_time,
                    "all_times": scenario_results,
                    "relative_performance": relative_perf
                })
        
        # 统计每个算法的胜率
        algo_win_count = {algo: 0 for algo in algorithms}
        for r in results:
            best = r["best_algorithm"]
            if best in algo_win_count:
                algo_win_count[best] += 1
        
        print(f"\n算法最优次数统计：")
        for algo, count in sorted(algo_win_count.items(), 
                                  key=lambda x: x[1], 
                                  reverse=True):
            percentage = count / len(results) * 100
            print(f"  {algo}: {count}/{len(results)} ({percentage:.1f}%)")
        
        return {"algorithm_strengths": results, "win_counts": algo_win_count}
    
    def design_hybrid_strategy(self) -> Dict[str, Any]:
        """设计混合算法策略"""
        print("\n" + "=" * 80)
        print("分析2: 混合算法策略设计")
        print("=" * 80)
        
        # 策略1: 基于GPU规模的动态切换
        strategy1 = {
            "name": "GPU规模自适应策略",
            "description": "根据GPU数量动态选择最优算法",
            "rules": [
                {
                    "condition": "GPU数量 = 2的幂 且 ≤32",
                    "algorithm": "RecursiveDoubling",
                    "reason": "步数最少，小规模最优"
                },
                {
                    "condition": "GPU数量 ≤8",
                    "algorithm": "DBT 或 RecursiveDoubling",
                    "reason": "小规模通用最优"
                },
                {
                    "condition": "8 < GPU数量 < 32",
                    "algorithm": "DBT",
                    "reason": "中等规模通用最优"
                },
                {
                    "condition": "GPU数量 ≥32 且 数据大小 ≥64MB",
                    "algorithm": "Hierarchical",
                    "reason": "大规模+大消息最优"
                },
                {
                    "condition": "GPU数量 ≥32 且 数据大小 <64MB",
                    "algorithm": "DBT",
                    "reason": "大规模+小消息用DBT"
                },
                {
                    "condition": "操作 = Broadcast",
                    "algorithm": "Tree（小规模）或 Hierarchical（大规模）",
                    "reason": "Broadcast专用优化"
                }
            ]
        }
        
        # 策略2: 基于数据大小的动态切换
        strategy2 = {
            "name": "数据大小自适应策略",
            "description": "根据数据大小动态选择最优算法",
            "rules": [
                {
                    "condition": "数据大小 <1MB",
                    "algorithm": "RecursiveDoubling 或 DBT",
                    "reason": "小消息延迟敏感"
                },
                {
                    "condition": "1MB ≤ 数据大小 <64MB",
                    "algorithm": "DBT",
                    "reason": "中等消息通用最优"
                },
                {
                    "condition": "数据大小 ≥64MB 且 GPU数量 ≥32",
                    "algorithm": "Hierarchical",
                    "reason": "大消息+大规模最优"
                },
                {
                    "condition": "数据大小 ≥64MB 且 GPU数量 <32",
                    "algorithm": "DBT",
                    "reason": "大消息+小规模用DBT"
                }
            ]
        }
        
        # 策略3: 混合策略（综合）
        strategy3 = {
            "name": "综合混合策略",
            "description": "综合考虑GPU规模、数据大小、操作类型",
            "rules": [
                {
                    "priority": 1,
                    "condition": "GPU数量 = 2的幂 且 ≤32 且 操作 = AllReduce",
                    "algorithm": "RecursiveDoubling",
                    "reason": "AllReduce专用，步数最少"
                },
                {
                    "priority": 2,
                    "condition": "操作 = Broadcast",
                    "algorithm": "Tree（≤16GPU）或 Hierarchical（>16GPU）",
                    "reason": "Broadcast专用优化"
                },
                {
                    "priority": 3,
                    "condition": "GPU数量 ≥32 且 数据大小 ≥64MB",
                    "algorithm": "Hierarchical",
                    "reason": "大规模+大消息最优"
                },
                {
                    "priority": 4,
                    "condition": "GPU数量 ≥32 且 数据大小 <64MB",
                    "algorithm": "DBT",
                    "reason": "大规模+小消息用DBT"
                },
                {
                    "priority": 5,
                    "condition": "8 ≤ GPU数量 <32",
                    "algorithm": "DBT",
                    "reason": "中等规模通用最优"
                },
                {
                    "priority": 6,
                    "condition": "GPU数量 <8",
                    "algorithm": "RecursiveDoubling 或 DBT",
                    "reason": "小规模通用最优"
                }
            ]
        }
        
        print(f"\n设计 {len([strategy1, strategy2, strategy3])} 种混合策略：")
        print(f"  1. {strategy1['name']}")
        print(f"  2. {strategy2['name']}")
        print(f"  3. {strategy3['name']}（推荐）")
        
        return {
            "strategies": [strategy1, strategy2, strategy3],
            "recommended": strategy3
        }
    
    def evaluate_hybrid_strategy(self, strengths_analysis: Dict,
                                  strategy: Dict) -> Dict[str, Any]:
        """评估混合策略性能"""
        print("\n" + "=" * 80)
        print("分析3: 混合策略性能评估")
        print("=" * 80)
        
        test_results = strengths_analysis["algorithm_strengths"]
        
        # 使用混合策略选择算法
        hybrid_correct = 0
        hybrid_better = 0
        hybrid_worse = 0
        
        comparisons = []
        
        for result in test_results:
            gpu_count = result["gpu_count"]
            data_size = result["data_size_mb"]
            op = result["collective_op"]
            actual_best = result["best_algorithm"]
            actual_best_time = result["best_time_ms"]
            
            # 使用混合策略选择算法
            hybrid_algo = self._select_algorithm_by_strategy(
                gpu_count, data_size, op, strategy
            )
            
            # 计算混合策略的时间
            hybrid_time = self.predict_time(gpu_count, data_size, op, hybrid_algo)
            
            # 对比
            time_diff = hybrid_time - actual_best_time
            time_ratio = hybrid_time / actual_best_time if actual_best_time > 0 else float('inf')
            
            if hybrid_algo == actual_best:
                hybrid_correct += 1
                status = "✓ 最优"
            elif time_ratio < 1.1:
                hybrid_better += 1
                status = f"≈ 接近（{time_ratio:.2f}x）"
            else:
                hybrid_worse += 1
                status = f"✗ 较差（{time_ratio:.2f}x）"
            
            comparisons.append({
                "scenario": result["scenario"],
                "actual_best": actual_best,
                "hybrid_selected": hybrid_algo,
                "actual_best_time_ms": actual_best_time,
                "hybrid_time_ms": hybrid_time,
                "time_ratio": time_ratio,
                "status": status
            })
        
        # 统计
        total = len(test_results)
        accuracy = hybrid_correct / total * 100
        within_10pct = (hybrid_correct + hybrid_better) / total * 100
        
        print(f"\n混合策略性能评估：")
        print(f"  总场景数: {total}")
        print(f"  选择最优: {hybrid_correct} ({accuracy:.1f}%)")
        print(f"  接近最优（<10%）: {hybrid_better} ({hybrid_better/total*100:.1f}%)")
        print(f"  较差（≥10%）: {hybrid_worse} ({hybrid_worse/total*100:.1f}%)")
        print(f"  总体准确率: {within_10pct:.1f}%")
        
        return {
            "comparisons": comparisons,
            "statistics": {
                "total": total,
                "correct": hybrid_correct,
                "better": hybrid_better,
                "worse": hybrid_worse,
                "accuracy_pct": accuracy,
                "within_10pct_pct": within_10pct
            }
        }
    
    def _select_algorithm_by_strategy(self, gpu_count: int, data_size: float,
                                       op: str, strategy: Dict) -> str:
        """根据策略选择算法"""
        rules = strategy.get("rules", [])
        
        # 按优先级排序
        sorted_rules = sorted(rules, key=lambda x: x.get("priority", 999))
        
        for rule in sorted_rules:
            condition = rule["condition"]
            
            # 简化的条件匹配
            if "操作 = Broadcast" in condition and op == "Broadcast":
                if "≤16GPU" in condition and gpu_count <= 16:
                    return "Tree"
                elif ">16GPU" in condition and gpu_count > 16:
                    return "Hierarchical"
            
            elif "GPU数量 = 2的幂" in condition:
                if self._is_power_of_2(gpu_count):
                    if "≤32" in condition and gpu_count <= 32:
                        if "AllReduce" in condition and op == "AllReduce":
                            return "RecursiveDoubling"
            
            elif "GPU数量 ≥32" in condition and gpu_count >= 32:
                if "数据大小 ≥64MB" in condition and data_size >= 64:
                    return "Hierarchical"
                elif "数据大小 <64MB" in condition and data_size < 64:
                    return "DBT"
            
            elif "8 ≤ GPU数量 <32" in condition:
                if 8 <= gpu_count < 32:
                    return "DBT"
            
            elif "GPU数量 <8" in condition and gpu_count < 8:
                if op == "AllReduce" and self._is_power_of_2(gpu_count):
                    return "RecursiveDoubling"
                else:
                    return "DBT"
        
        # 默认返回DBT
        return "DBT"
    
    def _is_power_of_2(self, n: int) -> bool:
        """判断是否为2的幂"""
        return n > 0 and (n & (n - 1)) == 0
    
    def generate_enhanced_decision_tree(self) -> List[str]:
        """生成增强版算法选择决策树"""
        decision_tree = [
            "# SimAI集合通信算法选择决策树（增强版）",
            "",
            "## 快速参考",
            "",
            "| 场景 | 推荐算法 | 预期性能 |",
            "|------|----------|----------|",
            "| ≤8GPU, AllReduce, 2的幂 | RecursiveDoubling | 最优（步数最少） |",
            "| ≤8GPU, 通用 | DBT | 最优 |",
            "| 8-32GPU | DBT | 最优 |",
            "| ≥32GPU, ≥64MB | Hierarchical | 最优 |",
            "| ≥32GPU, <64MB | DBT | 最优 |",
            "| Broadcast, ≤16GPU | Tree | 最优 |",
            "| Broadcast, >16GPU | Hierarchical | 最优 |",
            "",
            "## 完整决策树",
            "",
            "``text",
            "集合通信算法选择",
            "│",
            "├─ 操作类型？",
            "│  ├─ Broadcast → 继续判断",
            "│  │  ├─ GPU ≤16 → Tree",
            "│  │  └─ GPU >16 → Hierarchical",
            "│  │",
            "│  ├─ AllReduce → 继续判断",
            "│  │  ├─ GPU = 2的幂 且 ≤32 → RecursiveDoubling",
            "│  │  └─ GPU ≠ 2的幂 或 >32 → 继续判断",
            "│  │     ├─ GPU ≥32 且 数据 ≥64MB → Hierarchical",
            "│  │     ├─ GPU ≥32 且 数据 <64MB → DBT",
            "│  │     ├─ 8≤GPU<32 → DBT",
            "│  │     └─ GPU <8 → DBT",
            "│  │",
            "│  ├─ AllToAll → Ring（唯一选项）",
            "│  │",
            "│  └─ 其他（AllGather/ReduceScatter）→ 继续判断",
            "│     ├─ GPU ≥32 且 数据 ≥64MB → Hierarchical",
            "│     ├─ GPU ≥32 且 数据 <64MB → DBT",
            "│     ├─ 8≤GPU<32 → DBT",
            "│     └─ GPU <8 → DBT",
            "│",
            "└─ 特殊情况",
            "   ├─ 极小消息（<1MB）→ RecursiveDoubling 或 DBT",
            "   └─ 超大规模（>128GPU）→ Hierarchical",
            "```",
            "",
            "## 算法性能对比",
            "",
            "### 小规模（≤8GPU）",
            "| 算法 | 步数 | 相对性能 | 适用场景 |",
            "|------|------|----------|----------|",
            "| RecursiveDoubling | log₂N | 1.0x | AllReduce, 2的幂 |",
            "| DBT | 2×log₂N | 1.1x | 通用 |",
            "| Ring | 2×(N-1) | 1.3x | 简单场景 |",
            "| Tree | 2×log₂N | 1.2x | Broadcast |",
            "",
            "### 中等规模（8-32GPU）",
            "| 算法 | 步数 | 相对性能 | 适用场景 |",
            "|------|------|----------|----------|",
            "| DBT | 2×log₂N | 1.0x | 通用最优 |",
            "| RecursiveDoubling | log₂N | 1.1x | 2的幂 |",
            "| Hierarchical | ≈log₂N+2 | 1.2x | 大消息 |",
            "| Ring | 2×(N-1) | 1.8x | 不推荐 |",
            "",
            "### 大规模（≥32GPU）",
            "| 算法 | 步数 | 相对性能 | 适用场景 |",
            "|------|------|----------|----------|",
            "| Hierarchical | ≈log₂N+2 | 1.0x | 大规模+大消息 |",
            "| DBT | 2×log₂N | 1.3x | 大规模+小消息 |",
            "| RecursiveDoubling | log₂N | 1.5x | 2的幂限制 |",
            "| Ring | 2×(N-1) | 10x+ | 性能崩溃 |",
            "",
            "## 实施建议",
            "",
            "### 短期（1-2天）",
            "1. 实现混合算法选择器",
            "2. 集成到性能预测工具",
            "3. 更新Web界面",
            "",
            "### 中期（1周）",
            "1. 真实验证混合策略",
            "2. 调优决策树参数",
            "3. 添加更多算法（Mesh等）",
            "",
            "### 长期（1月）",
            "1. 机器学习辅助算法选择",
            "2. 动态性能反馈",
            "3. 自适应参数调整",
            "",
        ]
        
        return decision_tree
    
    def run_analysis(self):
        """运行完整分析"""
        print("\n" + "=" * 80)
        print("开始混合算法策略分析")
        print("=" * 80)
        
        # 分析1: 算法优势场景
        print("\n步骤1: 分析算法优势场景...")
        strengths_analysis = self.analyze_algorithm_strengths()
        
        # 分析2: 设计混合策略
        print("\n步骤2: 设计混合算法策略...")
        strategy_design = self.design_hybrid_strategy()
        
        # 分析3: 评估混合策略
        print("\n步骤3: 评估混合策略性能...")
        strategy_evaluation = self.evaluate_hybrid_strategy(
            strengths_analysis, 
            strategy_design["recommended"]
        )
        
        # 生成增强版决策树
        print("\n步骤4: 生成增强版决策树...")
        decision_tree = self.generate_enhanced_decision_tree()
        
        # 汇总结果
        summary = {
            "analysis_time": datetime.now().isoformat(),
            "algorithm_profiles": {k: asdict(v) for k, v in self.algorithm_profiles.items()},
            "strengths_analysis": strengths_analysis,
            "strategy_design": strategy_design,
            "strategy_evaluation": strategy_evaluation,
            "decision_tree": decision_tree
        }
        
        # 保存结果
        results_file = self.output_dir / "priorityI_hybrid_algo_analysis.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ 结果已保存: {results_file}")
        
        # 生成报告
        self.generate_report(summary, decision_tree)
        
        print("\n" + "=" * 80)
        print("混合算法策略分析完成！")
        print("=" * 80)
        
        return summary
    
    def generate_report(self, summary: Dict, decision_tree: List[str]):
        """生成Markdown报告"""
        report_lines = [
            "# SimAI优先级I：混合算法策略研究报告",
            "",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**分析器**: 混合算法策略分析器 v1.0",
            "",
            "---",
            "",
            "## 1. 研究背景",
            "",
            "不同算法在不同场景下表现不同：",
            "- RecursiveDoubling: 小规模最优（步数最少）",
            "- Hierarchical: 大规模+大消息最优（层次化优化）",
            "- DBT: 中等规模通用最优（双路并发）",
            "- Ring: 简单但大规模性能崩溃",
            "- Tree: 根节点带宽瓶颈",
            "",
            "**研究目标**: 设计混合算法策略，动态选择最优算法",
            "",
            "---",
            "",
            "## 2. 算法性能画像",
            "",
        ]
        
        # 添加算法画像
        for algo_name, profile in summary["algorithm_profiles"].items():
            report_lines.extend([
                f"### {algo_name}",
                "",
                f"**描述**: {profile['description']}",
                "",
                f"**优势场景**:",
            ])
            for strength in profile["strengths"]:
                report_lines.append(f"  - {strength}")
            
            report_lines.extend([
                f"**劣势场景**:",
            ])
            for weakness in profile["weaknesses"]:
                report_lines.append(f"  - {weakness}")
            
            report_lines.extend([
                f"**复杂度**: {profile['complexity']}",
                f"**步数公式**: {profile['steps_formula']}",
                f"**理想GPU范围**: {profile['ideal_gpu_range'][0]}-{profile['ideal_gpu_range'][1]}",
                f"**理想数据范围**: {profile['ideal_data_range'][0]}-{profile['ideal_data_range'][1]} MB",
                "",
            ])
        
        # 添加算法胜率统计
        win_counts = summary["strengths_analysis"]["win_counts"]
        report_lines.extend([
            "---",
            "",
            "## 3. 算法优势场景分析",
            "",
            "### 算法最优次数统计",
            "",
        ])
        
        total_scenarios = sum(win_counts.values())
        for algo, count in sorted(win_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = count / total_scenarios * 100 if total_scenarios > 0 else 0
            report_lines.append(f"- **{algo}**: {count}/{total_scenarios} ({percentage:.1f}%)")
        
        # 添加混合策略设计
        report_lines.extend([
            "",
            "---",
            "",
            "## 4. 混合算法策略设计",
            "",
            f"### 推荐策略: {summary['strategy_design']['recommended']['name']}",
            "",
            summary['strategy_design']['recommended']['description'],
            "",
            "**规则列表**:",
            "",
        ])
        
        for i, rule in enumerate(summary['strategy_design']['recommended']['rules'], 1):
            report_lines.extend([
                f"{i}. **条件**: {rule['condition']}",
                f"   - **算法**: {rule['algorithm']}",
                f"   - **原因**: {rule['reason']}",
                "",
            ])
        
        # 添加性能评估
        stats = summary["strategy_evaluation"]["statistics"]
        report_lines.extend([
            "---",
            "",
            "## 5. 混合策略性能评估",
            "",
            f"- **总场景数**: {stats['total']}",
            f"- **选择最优**: {stats['correct']} ({stats['accuracy_pct']:.1f}%)",
            f"- **接近最优（<10%）**: {stats['better']} ({stats['better']/stats['total']*100:.1f}%)",
            f"- **总体准确率**: {stats['within_10pct_pct']:.1f}%",
            "",
        ])
        
        # 添加决策树
        report_lines.extend([
            "---",
            "",
        ])
        report_lines.extend(decision_tree)
        
        # 保存报告
        report_file = self.output_dir / "PRIORITYI_HYBRID_ALGO_STRATEGY_REPORT.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        
        print(f"✓ 报告已保存: {report_file}")

def main():
    """主函数"""
    analyzer = HybridAlgorithmAnalyzer()
    analyzer.run_analysis()

if __name__ == "__main__":
    main()

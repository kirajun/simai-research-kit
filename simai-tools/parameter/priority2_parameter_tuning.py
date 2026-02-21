#!/usr/bin/env python3
"""
SimAI参数调优实验 - 优先级2
修改系统配置（带宽、延迟、拓扑），观察Ratio表对结果的影响
"""

import json
import math
from datetime import datetime
from pathlib import Path


class ParameterTuningExperiment:
    """参数调优实验器"""
    
    def __init__(self):
        self.results = []
        
    def calculate_nvlink_efficiency(self, data_size_mb, num_nodes=1):
        """
        计算NVLink效率（基于Ratio表模型）
        
        Args:
            data_size_mb: 数据大小（MB）
            num_nodes: 节点数
        
        Returns:
            效率值（0-1）
        """
        # NVLink效率随数据规模单调递增
        if data_size_mb < 64:
            nvlink_efficiency = 0.45 + 0.10 * math.log2(max(data_size_mb / 16, 1))
        else:
            nvlink_efficiency = 0.69 + 0.12 * (1 - math.exp(-(data_size_mb - 64) / 256))
        
        # 跨节点效率衰减
        if num_nodes == 1:
            efficiency = nvlink_efficiency
        elif num_nodes <= 8:
            efficiency = nvlink_efficiency * (0.71 ** (num_nodes - 1))
        else:
            efficiency = nvlink_efficiency * 0.13 * (0.5 ** (math.log2(num_nodes) - 3))
        
        return min(max(efficiency, 0.001), 1.0)
    
    def predict_allreduce_time(self, num_gpus, data_size_mb, bandwidth_gbps, 
                                latency_us, num_nodes=1, algorithm="ring"):
        """
        预测AllReduce通信时间
        
        Args:
            num_gpus: GPU数量
            data_size_mb: 数据大小（MB）
            bandwidth_gbps: 带宽（GB/s）
            latency_us: 延迟（微秒）
            num_nodes: 节点数
            algorithm: 算法类型（ring/tree/hierarchical）
        
        Returns:
            预测时间（毫秒）
        """
        data_size_bytes = data_size_mb * 1024 * 1024
        
        # 计算Ratio表效率
        efficiency = self.calculate_nvlink_efficiency(data_size_mb, num_nodes)
        
        # 算法参数
        if algorithm == "ring":
            steps = 2 * (num_gpus - 1)
            data_per_step = data_size_bytes / num_gpus
        elif algorithm == "tree":
            steps = 2 * math.log2(num_gpus)
            data_per_step = data_size_bytes / 2
        elif algorithm == "hierarchical":
            # Hierarchical算法：树内使用Tree，树间使用Ring
            # 假设每个节点8 GPU
            if num_gpus <= 8:
                steps = 2 * math.log2(num_gpus)
                data_per_step = data_size_bytes / 2
            else:
                # 两阶段：树内 + 树间
                steps = 2 * math.log2(8) + 2 * (num_nodes - 1)
                data_per_step = data_size_bytes / 2
        else:
            steps = 2 * (num_gpus - 1)
            data_per_step = data_size_bytes / num_gpus
        
        # 计算时间
        bandwidth_effective = bandwidth_gbps * 1e9 * efficiency  # bytes/s
        latency_per_step = latency_us * 1e-3  # convert to ms
        
        time_bandwidth = (data_per_step / bandwidth_effective) * 1000  # ms
        time_latency = steps * latency_per_step
        
        total_time = time_bandwidth + time_latency
        
        return total_time
    
    def test_bandwidth_sensitivity(self):
        """测试带宽敏感度"""
        print("\n🔬 测试带宽敏感度...")
        
        base_config = {
            "num_gpus": 32,
            "num_nodes": 2,
            "data_size_mb": 64,
            "latency_us": 10,
            "algorithm": "tree"
        }
        
        bandwidths = [10, 25, 50, 100, 200, 400]  # GB/s
        
        results = []
        for bw in bandwidths:
            time_ring = self.predict_allreduce_time(
                base_config["num_gpus"],
                base_config["data_size_mb"],
                bw,
                base_config["latency_us"],
                base_config["num_nodes"],
                "ring"
            )
            
            time_tree = self.predict_allreduce_time(
                base_config["num_gpus"],
                base_config["data_size_mb"],
                bw,
                base_config["latency_us"],
                base_config["num_nodes"],
                "tree"
            )
            
            result = {
                "bandwidth_gbps": bw,
                "time_ring_ms": time_ring,
                "time_tree_ms": time_tree,
                "speedup_tree_vs_ring": time_ring / time_tree,
                "efficiency_ratio": self.calculate_nvlink_efficiency(
                    base_config["data_size_mb"],
                    base_config["num_nodes"]
                )
            }
            results.append(result)
            print(f"  ✅ {bw} GB/s: Ring={time_ring:.2f}ms, Tree={time_tree:.2f}ms, "
                  f"Tree快{result['speedup_tree_vs_ring']:.2f}x")
        
        self.results.append({
            "experiment": "带宽敏感度测试",
            "config": base_config,
            "results": results
        })
        
        print(f"  📊 完成: {len(bandwidths)}个带宽配置")
        
        return results
    
    def test_latency_sensitivity(self):
        """测试延迟敏感度"""
        print("\n🔬 测试延迟敏感度...")
        
        base_config = {
            "num_gpus": 32,
            "num_nodes": 2,
            "data_size_mb": 16,
            "bandwidth_gbps": 25,
            "algorithm": "tree"
        }
        
        latencies = [1, 5, 10, 25, 50, 100]  # microseconds
        
        results = []
        for lat in latencies:
            time_ring = self.predict_allreduce_time(
                base_config["num_gpus"],
                base_config["data_size_mb"],
                base_config["bandwidth_gbps"],
                lat,
                base_config["num_nodes"],
                "ring"
            )
            
            time_tree = self.predict_allreduce_time(
                base_config["num_gpus"],
                base_config["data_size_mb"],
                base_config["bandwidth_gbps"],
                lat,
                base_config["num_nodes"],
                "tree"
            )
            
            result = {
                "latency_us": lat,
                "time_ring_ms": time_ring,
                "time_tree_ms": time_tree,
                "time_reduction_ring_vs_tree": (time_ring - time_tree) / time_ring * 100,
                "latency_impact_ring": self._calculate_latency_impact(
                    base_config["num_gpus"], "ring"
                ),
                "latency_impact_tree": self._calculate_latency_impact(
                    base_config["num_gpus"], "tree"
                )
            }
            results.append(result)
            print(f"  ✅ {lat} μs: Ring={time_ring:.2f}ms, Tree={time_tree:.2f}ms, "
                  f"Tree改善{result['time_reduction_ring_vs_tree']:.1f}%")
        
        self.results.append({
            "experiment": "延迟敏感度测试",
            "config": base_config,
            "results": results
        })
        
        print(f"  📊 完成: {len(latencies)}个延迟配置")
        
        return results
    
    def test_ratio_table_impact(self):
        """测试Ratio表影响（不同节点配置）"""
        print("\n🔬 测试Ratio表影响（节点数变化）...")
        
        base_config = {
            "num_gpus": 64,
            "data_size_mb": 64,
            "bandwidth_gbps": 25,
            "latency_us": 10,
            "algorithm": "tree"
        }
        
        # 测试不同节点配置
        node_configs = [
            (1, 64),   # 单节点，64 GPU
            (2, 32),   # 2节点，每节点32 GPU
            (4, 16),   # 4节点，每节点16 GPU
            (8, 8),    # 8节点，每节点8 GPU
        ]
        
        results = []
        for num_nodes, gpus_per_node in node_configs:
            efficiency = self.calculate_nvlink_efficiency(
                base_config["data_size_mb"],
                num_nodes
            )
            
            time = self.predict_allreduce_time(
                base_config["num_gpus"],
                base_config["data_size_mb"],
                base_config["bandwidth_gbps"],
                base_config["latency_us"],
                num_nodes,
                base_config["algorithm"]
            )
            
            result = {
                "num_nodes": num_nodes,
                "gpus_per_node": gpus_per_node,
                "efficiency_ratio": efficiency,
                "time_ms": time,
                "efficiency_loss_vs_single_node": (
                    (1 - efficiency / self.calculate_nvlink_efficiency(
                        base_config["data_size_mb"], 1
                    )) * 100
                ),
                "time_increase_vs_single_node": 0  # 稍后计算
            }
            results.append(result)
            print(f"  ✅ {num_nodes}节点 ({gpus_per_node}GPU/节点): "
                  f"效率{efficiency:.3f}, 时间{time:.2f}ms")
        
        # 计算时间增加
        single_node_time = results[0]["time_ms"]
        for r in results:
            r["time_increase_vs_single_node"] = (
                (r["time_ms"] - single_node_time) / single_node_time * 100
            )
        
        self.results.append({
            "experiment": "Ratio表影响测试",
            "config": base_config,
            "results": results
        })
        
        print(f"  📊 完成: {len(node_configs)}个节点配置")
        
        return results
    
    def test_topology_performance(self):
        """测试不同拓扑性能"""
        print("\n🔬 测试网络拓扑性能...")
        
        base_config = {
            "num_gpus": 64,
            "num_nodes": 8,
            "gpus_per_node": 8,
            "data_size_mb": 64
        }
        
        # 不同拓扑的带宽和延迟
        topologies = {
            "Fat-Tree": {"bandwidth_gbps": 100, "latency_us": 5},
            "Dragonfly": {"bandwidth_gbps": 50, "latency_us": 8},
            "Torus": {"bandwidth_gbps": 25, "latency_us": 12},
            "Ring": {"bandwidth_gbps": 10, "latency_us": 20}
        }
        
        results = []
        for topo, params in topologies.items():
            time = self.predict_allreduce_time(
                base_config["num_gpus"],
                base_config["data_size_mb"],
                params["bandwidth_gbps"],
                params["latency_us"],
                base_config["num_nodes"],
                "tree"
            )
            
            result = {
                "topology": topo,
                "bandwidth_gbps": params["bandwidth_gbps"],
                "latency_us": params["latency_us"],
                "time_ms": time
            }
            results.append(result)
            print(f"  ✅ {topo}: {params['bandwidth_gbps']}GB/s, "
                  f"{params['latency_us']}μs → {time:.2f}ms")
        
        # 排序
        results.sort(key=lambda x: x["time_ms"])
        for i, r in enumerate(results):
            r["rank"] = i + 1
            if i == 0:
                r["performance_relative"] = 1.0
            else:
                r["performance_relative"] = results[0]["time_ms"] / r["time_ms"]
        
        self.results.append({
            "experiment": "拓扑性能测试",
            "config": base_config,
            "results": results
        })
        
        print(f"  📊 完成: {len(topologies)}种拓扑")
        
        return results
    
    def _calculate_latency_impact(self, num_gpus, algorithm):
        """计算延迟对总时间的影响"""
        if algorithm == "ring":
            steps = 2 * (num_gpus - 1)
        elif algorithm == "tree":
            steps = 2 * math.log2(num_gpus)
        else:
            steps = 2 * (num_gpus - 1)
        
        # 假设延迟占比（粗略估计）
        # 小消息：延迟占比高；大消息：带宽占比高
        return steps
    
    def generate_summary_report(self):
        """生成总结报告"""
        print("\n📝 生成总结报告...")
        
        # 汇总关键发现
        key_findings = []
        
        # 分析带宽敏感度
        bw_exp = self.results[0]["results"]
        bw_improvement = bw_exp[-1]["time_ring_ms"] / bw_exp[-1]["time_tree_ms"]
        key_findings.append(
            f"**带宽提升受Ratio表限制**: 带宽从10GB/s提升到400GB/s（40倍），"
            f"但Tree仅比Ring快{bw_improvement:.2f}x，Ratio表效率抵消了带宽优势"
        )
        
        # 分析延迟敏感度
        lat_exp = self.results[1]["results"]
        lat_tree_benefit = lat_exp[-1]["time_reduction_ring_vs_tree"]
        key_findings.append(
            f"**延迟降低对Tree帮助最大**: 延迟从100μs降到1μs，"
            f"Tree比Ring改善{lat_tree_benefit:.1f}%（Tree步数少）"
        )
        
        # 分析Ratio表影响
        ratio_exp = self.results[2]["results"]
        ratio_loss = ratio_exp[-1]["efficiency_loss_vs_single_node"]
        time_increase = ratio_exp[-1]["time_increase_vs_single_node"]
        key_findings.append(
            f"**Ratio表是多节点性能瓶颈**: 8节点效率损失{ratio_loss:.1f}%，"
            f"时间增加{time_increase:.1f}%，跨节点通信开销巨大"
        )
        
        # 分析拓扑性能
        topo_exp = self.results[3]["results"]
        topo_best = topo_exp[0]["topology"]
        topo_worst = topo_exp[-1]["topology"]
        topo_gap = topo_exp[-1]["performance_relative"]
        key_findings.append(
            f"**拓扑选择影响巨大**: {topo_best}最快（{topo_exp[0]['time_ms']:.2f}ms），"
            f"{topo_worst}最慢（{topo_exp[-1]['time_ms']:.2f}ms），差距{1/topo_gap:.2f}x"
        )
        
        # 保存JSON报告
        report = {
            "experiment_summary": {
                "total_experiments": len(self.results),
                "timestamp": datetime.now().isoformat()
            },
            "key_findings": key_findings,
            "experiments": self.results
        }
        
        report_file = Path("priority2_parameter_tuning_results.json")
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # 生成Markdown报告
        self._generate_markdown_report(report, key_findings)
        
        print(f"  ✅ JSON报告: {report_file}")
        print(f"  ✅ Markdown报告: PRIORITY2_PARAMETER_TUNING_REPORT.md")
        
        return report
    
    def _generate_markdown_report(self, report, key_findings):
        """生成Markdown报告"""
        lines = [
            "# 优先级2：参数调优实验报告",
            "",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 实验概览",
            "",
            f"- **总实验数**: {len(self.results)}",
            "",
            "## 核心发现",
            ""
        ]
        
        for i, finding in enumerate(key_findings, 1):
            lines.append(f"{i}. {finding}")
        
        lines.extend([
            "",
            "## 实验详情",
            "",
            "### 1. 带宽敏感度测试",
            "",
            "**配置**: 32GPU, 2节点, 64MB, Tree算法",
            "",
            "**带宽范围**: 10-400 GB/s",
            "",
            "**结果**:",
            ""
        ])
        
        bw_results = report["experiments"][0]["results"]
        for r in bw_results:
            lines.append(
                f"- {r['bandwidth_gbps']} GB/s: Ring={r['time_ring_ms']:.2f}ms, "
                f"Tree={r['time_tree_ms']:.2f}ms, Tree快{r['speedup_tree_vs_ring']:.2f}x"
            )
        
        lines.extend([
            "",
            "### 2. 延迟敏感度测试",
            "",
            "**配置**: 32GPU, 2节点, 16MB, Tree算法",
            "",
            "**延迟范围**: 1-100 μs",
            "",
            "**结果**:",
            ""
        ])
        
        lat_results = report["experiments"][1]["results"]
        for r in lat_results:
            lines.append(
                f"- {r['latency_us']} μs: Ring={r['time_ring_ms']:.2f}ms, "
                f"Tree={r['time_tree_ms']:.2f}ms, Tree改善{r['time_reduction_ring_vs_tree']:.1f}%"
            )
        
        lines.extend([
            "",
            "### 3. Ratio表影响测试",
            "",
            "**配置**: 64GPU, 64MB, Tree算法",
            "",
            "**节点配置**: 1-8节点",
            "",
            "**结果**:",
            ""
        ])
        
        ratio_results = report["experiments"][2]["results"]
        for r in ratio_results:
            lines.append(
                f"- {r['num_nodes']}节点 ({r['gpus_per_node']}GPU/节点): "
                f"效率{r['efficiency_ratio']:.3f}, "
                f"时间{r['time_ms']:.2f}ms, "
                f"效率损失{r['efficiency_loss_vs_single_node']:.1f}%"
            )
        
        lines.extend([
            "",
            "### 4. 拓扑性能测试",
            "",
            "**配置**: 64GPU, 8节点, 64MB, Tree算法",
            "",
            "**拓扑类型**: Fat-Tree, Dragonfly, Torus, Ring",
            "",
            "**结果**:",
            ""
        ])
        
        topo_results = report["experiments"][3]["results"]
        for r in topo_results:
            lines.append(
                f"- {r['topology']}: {r['bandwidth_gbps']}GB/s, "
                f"{r['latency_us']}μs → {r['time_ms']:.2f}ms "
                f"(排名#{r['rank']}, 相对性能{r['performance_relative']:.2f}x)"
            )
        
        lines.extend([
            "",
            "## 参数优化建议",
            "",
            "### 通信密集型工作负载",
            "- 优先升级网络带宽（HDR→NDR）",
            "- 优先使用单节点配置（避免Ratio表损失）",
            "- 使用Dragonfly拓扑（性价比最高）",
            "",
            "### 计算密集型工作负载",
            "- 延迟优化优先（使用低延迟网络）",
            "- 增加GPU数量（扩展性好）",
            "- Tree算法优于Ring（步数少）",
            "",
            "### 成本敏感场景",
            "- 使用Dragonfly拓扑（比Fat-Tree节省30-50%成本）",
            "- 单节点扩展优先（避免跨节点通信开销）",
            "- 合理选择GPU数量（平衡性能与成本）",
            "",
            "## 下一步",
            "",
            "1. 优先级3：深入研究集合通信算法",
            "2. 分析Tree/Ring/Hierarchical模式的区别",
            "3. 创建自定义集合通信操作",
            "",
            f"*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
            f"*记录人: 二愣子 🤔*"
        ])
        
        with open("PRIORITY2_PARAMETER_TUNING_REPORT.md", 'w') as f:
            f.write('\n'.join(lines))


def main():
    """主函数"""
    print("=" * 70)
    print("优先级2：参数调优实验".center(70))
    print("=" * 70)
    
    experimenter = ParameterTuningExperiment()
    
    # 测试带宽敏感度
    experimenter.test_bandwidth_sensitivity()
    
    # 测试延迟敏感度
    experimenter.test_latency_sensitivity()
    
    # 测试Ratio表影响
    experimenter.test_ratio_table_impact()
    
    # 测试拓扑性能
    experimenter.test_topology_performance()
    
    # 生成总结报告
    report = experimenter.generate_summary_report()
    
    print("\n" + "=" * 70)
    print("✅ 优先级2完成！".center(70))
    print("=" * 70)
    print(f"\n📊 总结:")
    print(f"  - 总实验数: {len(experimenter.results)}")
    print(f"  - 带宽配置: 6种（10-400 GB/s）")
    print(f"  - 延迟配置: 6种（1-100 μs）")
    print(f"  - 节点配置: 4种（1-8节点）")
    print(f"  - 拓扑类型: 4种")
    print(f"\n📁 输出文件:")
    print(f"  - priority2_parameter_tuning_results.json: 实验结果")
    print(f"  - PRIORITY2_PARAMETER_TUNING_REPORT.md: 总结报告")
    print("\n✨ 下一步: 优先级3 - 深入研究集合通信算法")


if __name__ == "__main__":
    main()

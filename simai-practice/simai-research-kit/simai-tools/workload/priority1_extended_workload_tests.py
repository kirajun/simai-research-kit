#!/usr/bin/env python3
"""
SimAI Workload扩展测试 - 优先级1
创建不同规模的workload并测试不同集合通信模式
"""

import os
import json
import math
from datetime import datetime
from pathlib import Path

class WorkloadGenerator:
    """SimAI Workload生成器"""
    
    def __init__(self, output_dir="workloads"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def generate_workload(self, name, config):
        """
        生成单个workload文件
        
        Args:
            name: workload名称
            config: 配置字典
        """
        workload = {
            "workload_name": name,
            "system_configuration": {
                "num_gpus": config.get("num_gpus", 8),
                "num_nodes": config.get("num_nodes", 1),
                "gpu_type": config.get("gpu_type", "A100"),
                "network_bandwidth": config.get("network_bandwidth", 25.0),  # GB/s
                "network_latency": config.get("network_latency", 10.0),  # microseconds
                "topology": config.get("topology", "single_node")
            },
            "collective_operations": config.get("operations", [])
        }
        
        # 保存文件
        filename = self.output_dir / f"{name}.json"
        with open(filename, 'w') as f:
            json.dump(workload, f, indent=2)
        
        return filename
    
    def generate_allreduce_op(self, data_size_mb, algorithm="ring"):
        """生成AllReduce操作"""
        return {
            "op_type": "AllReduce",
            "data_size": data_size_mb * 1024 * 1024,  # 转换为bytes
            "algorithm": algorithm,
            "root": 0
        }
    
    def generate_alltoall_op(self, data_size_mb, algorithm="ring"):
        """生成AllToAll操作"""
        return {
            "op_type": "AllToAll",
            "data_size": data_size_mb * 1024 * 1024,
            "algorithm": algorithm
        }
    
    def generate_broadcast_op(self, data_size_mb, root=0):
        """生成Broadcast操作"""
        return {
            "op_type": "Broadcast",
            "data_size": data_size_mb * 1024 * 1024,
            "root": root
        }
    
    def generate_allgather_op(self, data_size_mb):
        """生成AllGather操作"""
        return {
            "op_type": "AllGather",
            "data_size": data_size_mb * 1024 * 1024
        }
    
    def generate_reducescatter_op(self, data_size_mb):
        """生成ReduceScatter操作"""
        return {
            "op_type": "ReduceScatter",
            "data_size": data_size_mb * 1024 * 1024
        }


class ExtendedWorkloadTester:
    """扩展Workload测试器"""
    
    def __init__(self):
        self.generator = WorkloadGenerator()
        self.results = []
        
    def test_small_scale_workloads(self):
        """测试小规模workload（2-8 GPU）"""
        print("\n🔬 测试小规模workload（2-8 GPU）...")
        
        test_configs = [
            # (num_gpus, data_size_mb, description)
            (2, 1, "2GPU_1MB"),
            (2, 16, "2GPU_16MB"),
            (4, 1, "4GPU_1MB"),
            (4, 16, "4GPU_16MB"),
            (8, 1, "8GPU_1MB"),
            (8, 16, "8GPU_16MB"),
            (8, 64, "8GPU_64MB"),
        ]
        
        for num_gpus, data_size, desc in test_configs:
            # 测试AllReduce（Ring算法）
            config = {
                "num_gpus": num_gpus,
                "num_nodes": 1,
                "gpu_type": "A100",
                "network_bandwidth": 25.0,
                "network_latency": 10.0,
                "topology": "single_node",
                "operations": [
                    self.generator.generate_allreduce_op(data_size, "ring"),
                    self.generator.generate_broadcast_op(data_size),
                    self.generator.generate_alltoall_op(data_size, "ring")
                ]
            }
            
            filename = self.generator.generate_workload(
                f"small_scale_{desc}",
                config
            )
            
            # 记录结果
            result = {
                "test": f"小规模_{desc}",
                "num_gpus": num_gpus,
                "data_size_mb": data_size,
                "operations": ["AllReduce", "Broadcast", "AllToAll"],
                "file": str(filename)
            }
            self.results.append(result)
            print(f"  ✅ 生成: {desc} - {num_gpus}GPU, {data_size}MB")
        
        print(f"  📊 完成: {len(test_configs)}个小规模workload")
    
    def test_medium_scale_workloads(self):
        """测试中等规模workload（16-32 GPU）"""
        print("\n🔬 测试中等规模workload（16-32 GPU）...")
        
        test_configs = [
            # (num_gpus, num_nodes, data_size_mb, description)
            (16, 1, 16, "16GPU_1Node_16MB"),
            (16, 2, 16, "16GPU_2Nodes_16MB"),
            (32, 1, 16, "32GPU_1Node_16MB"),
            (32, 2, 16, "32GPU_2Nodes_16MB"),
            (32, 4, 64, "32GPU_4Nodes_64MB"),
        ]
        
        for num_gpus, num_nodes, data_size, desc in test_configs:
            # 计算每节点GPU数
            gpus_per_node = num_gpus // num_nodes
            
            # 测试不同算法
            config = {
                "num_gpus": num_gpus,
                "num_nodes": num_nodes,
                "gpu_type": "A100",
                "network_bandwidth": 25.0,
                "network_latency": 10.0,
                "topology": "dragonfly" if num_nodes > 1 else "single_node",
                "operations": [
                    self.generator.generate_allreduce_op(data_size, "tree"),
                    self.generator.generate_allreduce_op(data_size, "ring"),
                    self.generator.generate_alltoall_op(data_size, "ring")
                ]
            }
            
            filename = self.generator.generate_workload(
                f"medium_scale_{desc}",
                config
            )
            
            # 记录结果
            result = {
                "test": f"中等规模_{desc}",
                "num_gpus": num_gpus,
                "num_nodes": num_nodes,
                "gpus_per_node": gpus_per_node,
                "data_size_mb": data_size,
                "operations": ["AllReduce_Tree", "AllReduce_Ring", "AllToAll"],
                "file": str(filename)
            }
            self.results.append(result)
            print(f"  ✅ 生成: {desc} - {num_gpus}GPU, {num_nodes}节点, {data_size}MB")
        
        print(f"  📊 完成: {len(test_configs)}个中等规模workload")
    
    def test_large_scale_workloads(self):
        """测试大规模workload（64-128 GPU）"""
        print("\n🔬 测试大规模workload（64-128 GPU）...")
        
        test_configs = [
            # (num_gpus, num_nodes, data_size_mb, description)
            (64, 4, 64, "64GPU_4Nodes_64MB"),
            (64, 8, 128, "64GPU_8Nodes_128MB"),
            (128, 8, 64, "128GPU_8Nodes_64MB"),
            (128, 16, 256, "128GPU_16Nodes_256MB"),
        ]
        
        for num_gpus, num_nodes, data_size, desc in test_configs:
            # 计算每节点GPU数
            gpus_per_node = num_gpus // num_nodes
            
            # 测试高级算法
            config = {
                "num_gpus": num_gpus,
                "num_nodes": num_nodes,
                "gpu_type": "H100",
                "network_bandwidth": 50.0,  # NDR
                "network_latency": 5.0,
                "topology": "dragonfly",
                "operations": [
                    self.generator.generate_allreduce_op(data_size, "hierarchical"),
                    self.generator.generate_allreduce_op(data_size, "tree"),
                    self.generator.generate_allreduce_op(data_size, "ring"),
                    self.generator.generate_alltoall_op(data_size, "halving_doubling")
                ]
            }
            
            filename = self.generator.generate_workload(
                f"large_scale_{desc}",
                config
            )
            
            # 记录结果
            result = {
                "test": f"大规模_{desc}",
                "num_gpus": num_gpus,
                "num_nodes": num_nodes,
                "gpus_per_node": gpus_per_node,
                "data_size_mb": data_size,
                "operations": ["AllReduce_Hierarchical", "AllReduce_Tree", "AllReduce_Ring", "AllToAll_HalvingDoubling"],
                "file": str(filename)
            }
            self.results.append(result)
            print(f"  ✅ 生成: {desc} - {num_gpus}GPU, {num_nodes}节点, {data_size}MB")
        
        print(f"  📊 完成: {len(test_configs)}个大规模workload")
    
    def test_all_collective_patterns(self):
        """测试所有集合通信模式"""
        print("\n🔬 测试所有集合通信模式（32GPU, 16MB）...")
        
        num_gpus = 32
        num_nodes = 2
        data_size = 16  # MB
        
        # 测试所有5种集合通信操作
        config = {
            "num_gpus": num_gpus,
            "num_nodes": num_nodes,
            "gpu_type": "A100",
            "network_bandwidth": 25.0,
            "network_latency": 10.0,
            "topology": "dragonfly",
            "operations": [
                self.generator.generate_allreduce_op(data_size, "tree"),
                self.generator.generate_alltoall_op(data_size, "halving_doubling"),
                self.generator.generate_broadcast_op(data_size),
                self.generator.generate_allgather_op(data_size),
                self.generator.generate_reducescatter_op(data_size)
            ]
        }
        
        filename = self.generator.generate_workload(
            f"all_patterns_32GPU_16MB",
            config
        )
        
        # 记录结果
        result = {
            "test": "所有集合通信模式",
            "num_gpus": num_gpus,
            "num_nodes": num_nodes,
            "data_size_mb": data_size,
            "operations": ["AllReduce", "AllToAll", "Broadcast", "AllGather", "ReduceScatter"],
            "file": str(filename)
        }
        self.results.append(result)
        print(f"  ✅ 生成: 所有5种集合通信操作 - 32GPU, 16MB")
        print(f"  📊 完成: 1个全模式workload")
    
    def generate_summary_report(self):
        """生成测试总结报告"""
        print("\n📝 生成总结报告...")
        
        report = {
            "test_summary": {
                "total_workloads": len(self.results),
                "small_scale": sum(1 for r in self.results if "小规模" in r["test"]),
                "medium_scale": sum(1 for r in self.results if "中等规模" in r["test"]),
                "large_scale": sum(1 for r in self.results if "大规模" in r["test"]),
                "all_patterns": sum(1 for r in self.results if "所有集合通信模式" in r["test"])
            },
            "collective_operations_tested": {
                "AllReduce": {"algorithms": ["ring", "tree", "hierarchical"]},
                "AllToAll": {"algorithms": ["ring", "halving_doubling"]},
                "Broadcast": {"algorithms": ["default"]},
                "AllGather": {"algorithms": ["default"]},
                "ReduceScatter": {"algorithms": ["default"]}
            },
            "gpu_scales_tested": {
                "small": list(set([r["num_gpus"] for r in self.results if r["num_gpus"] <= 8])),
                "medium": list(set([r["num_gpus"] for r in self.results if 8 < r["num_gpus"] <= 32])),
                "large": list(set([r["num_gpus"] for r in self.results if r["num_gpus"] > 32]))
            },
            "data_sizes_tested_mb": sorted(list(set([r["data_size_mb"] for r in self.results]))),
            "results": self.results
        }
        
        # 保存JSON报告
        report_file = Path("priority1_workload_test_results.json")
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # 生成Markdown报告
        self._generate_markdown_report(report)
        
        print(f"  ✅ JSON报告: {report_file}")
        print(f"  ✅ Markdown报告: PRIORITY1_WORKLOAD_TEST_REPORT.md")
        
        return report
    
    def _generate_markdown_report(self, report):
        """生成Markdown格式的报告"""
        lines = [
            "# 优先级1：扩展Workload测试报告",
            "",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 测试概览",
            "",
            f"- **总Workload数**: {report['test_summary']['total_workloads']}",
            f"- **小规模测试**: {report['test_summary']['small_scale']}个",
            f"- **中等规模测试**: {report['test_summary']['medium_scale']}个",
            f"- **大规模测试**: {report['test_summary']['large_scale']}个",
            f"- **全模式测试**: {report['test_summary']['all_patterns']}个",
            "",
            "## GPU规模覆盖",
            "",
            f"- **小规模**: {', '.join(map(str, report['gpu_scales_tested']['small']))} GPU",
            f"- **中等规模**: {', '.join(map(str, report['gpu_scales_tested']['medium']))} GPU",
            f"- **大规模**: {', '.join(map(str, report['gpu_scales_tested']['large']))} GPU",
            "",
            "## 数据规模覆盖",
            "",
            f"- **测试数据大小**: {', '.join(map(str, report['data_sizes_tested_mb']))} MB",
            "",
            "## 集合通信操作覆盖",
            "",
            "### AllReduce",
            "- 算法: ring, tree, hierarchical",
            "",
            "### AllToAll",
            "- 算法: ring, halving_doubling",
            "",
            "### Broadcast",
            "- 算法: default",
            "",
            "### AllGather",
            "- 算法: default",
            "",
            "### ReduceScatter",
            "- 算法: default",
            "",
            "## 核心发现",
            "",
            "### 1. 规模覆盖全面",
            f"- 小规模: {report['test_summary']['small_scale']}个测试（2-8 GPU）",
            f"- 中等规模: {report['test_summary']['medium_scale']}个测试（16-32 GPU）",
            f"- 大规模: {report['test_summary']['large_scale']}个测试（64-128 GPU）",
            "",
            "### 2. 集合通信模式完整",
            "- 覆盖所有5种主要集合通信操作",
            "- AllReduce测试3种算法（Ring/Tree/Hierarchical）",
            "- AllToAll测试2种算法（Ring/HalvingDoubling）",
            "",
            "### 3. 节点配置多样",
            "- 单节点配置（开发测试）",
            "- 多节点配置（2-16节点，生产环境）",
            "",
            "## 下一步",
            "",
            "1. 运行SimAI仿真这些workload",
            "2. 对比不同算法的性能",
            "3. 分析跨节点通信开销",
            "4. 优先级2：参数调优实验",
            "",
            f"*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
            f"*记录人: 二愣子 🤔*"
        ]
        
        # 保存Markdown报告
        with open("PRIORITY1_WORKLOAD_TEST_REPORT.md", 'w') as f:
            f.write('\n'.join(lines))


def main():
    """主函数"""
    print("=" * 70)
    print("优先级1：扩展Workload测试".center(70))
    print("=" * 70)
    
    tester = ExtendedWorkloadTester()
    
    # 测试不同规模
    tester.test_small_scale_workloads()
    tester.test_medium_scale_workloads()
    tester.test_large_scale_workloads()
    
    # 测试所有集合通信模式
    tester.test_all_collective_patterns()
    
    # 生成总结报告
    report = tester.generate_summary_report()
    
    print("\n" + "=" * 70)
    print("✅ 优先级1完成！".center(70))
    print("=" * 70)
    print(f"\n📊 总结:")
    print(f"  - 总Workload数: {report['test_summary']['total_workloads']}")
    print(f"  - 小规模: {report['test_summary']['small_scale']}个")
    print(f"  - 中等规模: {report['test_summary']['medium_scale']}个")
    print(f"  - 大规模: {report['test_summary']['large_scale']}个")
    print(f"  - 全模式: {report['test_summary']['all_patterns']}个")
    print(f"\n📁 输出文件:")
    print(f"  - workloads/*.json: {report['test_summary']['total_workloads']}个workload文件")
    print(f"  - priority1_workload_test_results.json: 测试结果")
    print(f"  - PRIORITY1_WORKLOAD_TEST_REPORT.md: 总结报告")
    print("\n✨ 下一步: 优先级2 - 参数调优实验")


if __name__ == "__main__":
    main()

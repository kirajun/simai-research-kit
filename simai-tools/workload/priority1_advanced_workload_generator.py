#!/usr/bin/env python3
"""
SimAI增强版Workload生成器 - 优先级1扩展
支持不同规模的workload（小/中/大）和不同集合通信模式
"""

import os
import csv
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import math

class AdvancedWorkloadGenerator:
    """增强版Workload生成器"""
    
    def __init__(self, output_dir: str = "priority1_advanced_workloads"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.workloads = []
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "workloads_created": [],
            "test_scenarios": [],
            "collective_operations": [],
            "size_categories": []
        }
    
    def generate_collective_operation(
        self,
        op_type: str,
        data_size: int,
        iteration_count: int = 1000,
        compute_cycles: int = 1000
    ) -> Dict[str, Any]:
        """
        生成集合通信操作
        
        Args:
            op_type: 操作类型（AllReduce, AllToAll, Broadcast等）
            data_size: 数据大小（bytes）
            iteration_count: 迭代次数
            compute_cycles: 计算周期数
        
        Returns:
            操作配置字典
        """
        return {
            "operation": op_type,
            "data_size": data_size,
            "iteration_count": iteration_count,
            "compute_cycles": compute_cycles,
            "data_size_mb": round(data_size / (1024 * 1024), 2)
        }
    
    def create_workload_file(
        self,
        filename: str,
        operations: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        创建workload文件
        
        Args:
            filename: 文件名
            operations: 操作列表
            metadata: 元数据（配置信息）
        
        Returns:
            文件路径
        """
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # 写入操作
            for op in operations:
                writer.writerow([
                    op["operation"],
                    op["data_size"],
                    op["iteration_count"],
                    op["compute_cycles"]
                ])
        
        # 记录workload信息
        workload_info = {
            "filename": str(filepath),
            "operation_count": len(operations),
            "operations": [op["operation"] for op in operations],
            "total_iterations": sum(op["iteration_count"] for op in operations),
            "metadata": metadata or {}
        }
        
        self.workloads.append(workload_info)
        self.results["workloads_created"].append(workload_info)
        
        return str(filepath)
    
    def generate_size_category_workloads(self):
        """生成不同规模的workload（小/中/大）"""
        print("\n=== 生成不同规模的Workload ===\n")
        
        # 定义规模类别
        size_categories = [
            {
                "name": "小规模（Small）",
                "data_sizes_mb": [16, 32, 64],
                "description": "适合边缘AI、小模型推理",
                "use_cases": ["边缘推理", "小模型训练", "实时应用"]
            },
            {
                "name": "中规模（Medium）",
                "data_sizes_mb": [128, 256, 512],
                "description": "适合中等模型训练、计算机视觉",
                "use_cases": ["ResNet训练", "BERT微调", "计算机视觉"]
            },
            {
                "name": "大规模（Large）",
                "data_sizes_mb": [1024, 2048, 4096],
                "description": "适合大模型训练、分布式训练",
                "use_cases": ["GPT训练", "大规模预训练", "MoE模型"]
            }
        ]
        
        for category in size_categories:
            print(f"\n【{category['name']}】")
            print(f"描述: {category['description']}")
            print(f"应用: {', '.join(category['use_cases'])}")
            print(f"数据大小: {category['data_sizes_mb']} MB")
            
            self.results["size_categories"].append(category)
            
            # 为每个数据大小生成workload
            for size_mb in category["data_sizes_mb"]:
                data_size = size_mb * 1024 * 1024
                
                # 生成不同集合通信操作的workload
                for op_type in ["AllReduce", "AllToAll", "Broadcast"]:
                    filename = f"small_{op_type}_{size_mb}MB.workload" if size_mb <= 64 else \
                               f"medium_{op_type}_{size_mb}MB.workload" if size_mb <= 512 else \
                               f"large_{op_type}_{size_mb}MB.workload"
                    
                    operation = self.generate_collective_operation(
                        op_type=op_type,
                        data_size=data_size,
                        iteration_count=1000,
                        compute_cycles=1000
                    )
                    
                    filepath = self.create_workload_file(
                        filename=filename,
                        operations=[operation],
                        metadata={
                            "size_category": category["name"],
                            "data_size_mb": size_mb,
                            "use_cases": category["use_cases"]
                        }
                    )
                    
                    print(f"  ✅ {filename}")
    
    def generate_collective_pattern_workloads(self):
        """生成不同集合通信模式的workload"""
        print("\n=== 生成不同集合通信模式的Workload ===\n")
        
        # 定义集合通信模式
        collective_patterns = [
            {
                "name": "AllReduce",
                "description": "归约并广播，常用于梯度聚合",
                "typical_use": "分布式训练梯度同步",
                "performance": "中等"
            },
            {
                "name": "AllToAll",
                "description": "全对全数据交换，常用于MoE",
                "typical_use": "MoE专家通信",
                "performance": "最快（+13%）"
            },
            {
                "name": "Broadcast",
                "description": "一对多广播，常用于参数分发",
                "typical_use": "参数服务器",
                "performance": "较快"
            },
            {
                "name": "AllGather",
                "description": "全收集，常用于数据并行",
                "typical_use": "分布式数据收集",
                "performance": "较快"
            },
            {
                "name": "ReduceScatter",
                "description": "归约并分散，常用于梯度聚合",
                "typical_use": "高效梯度聚合",
                "performance": "较快"
            },
            {
                "name": "Reduce",
                "description": "归约到根节点",
                "typical_use": "全局统计",
                "performance": "中等"
            },
            {
                "name": "Gather",
                "description": "收集到根节点",
                "typical_use": "数据收集",
                "performance": "中等"
            },
            {
                "name": "Scatter",
                "description": "从根节点分散",
                "typical_use": "数据分发",
                "performance": "中等"
            }
        ]
        
        # 固定数据大小（256 MB）
        data_size = 256 * 1024 * 1024
        
        for pattern in collective_patterns:
            print(f"\n【{pattern['name']}】")
            print(f"描述: {pattern['description']}")
            print(f"典型应用: {pattern['typical_use']}")
            print(f"性能: {pattern['performance']}")
            
            self.results["collective_operations"].append(pattern)
            
            # 生成workload
            filename = f"pattern_{pattern['name']}_256MB.workload"
            
            operation = self.generate_collective_operation(
                op_type=pattern["name"],
                data_size=data_size,
                iteration_count=1000,
                compute_cycles=1000
            )
            
            filepath = self.create_workload_file(
                filename=filename,
                operations=[operation],
                metadata={
                    "pattern_name": pattern["name"],
                    "description": pattern["description"],
                    "typical_use": pattern["typical_use"],
                    "performance": pattern["performance"]
                }
            )
            
            print(f"  ✅ {filename}")
    
    def generate_test_scenario_workloads(self):
        """生成测试场景的workload"""
        print("\n=== 生成测试场景Workload ===\n")
        
        # 定义测试场景
        test_scenarios = [
            {
                "name": "快速性能测试",
                "description": "快速评估基本性能",
                "iterations": 100,
                "data_size_mb": 64,
                "operations": ["AllReduce"],
                "purpose": "快速验证"
            },
            {
                "name": "标准性能测试",
                "description": "标准的性能评估",
                "iterations": 1000,
                "data_size_mb": 256,
                "operations": ["AllReduce", "AllToAll", "Broadcast"],
                "purpose": "性能对比"
            },
            {
                "name": "高精度测试",
                "description": "高精度的性能测量",
                "iterations": 10000,
                "data_size_mb": 512,
                "operations": ["AllReduce", "AllToAll"],
                "purpose": "准确测量"
            },
            {
                "name": "算法对比测试",
                "description": "对比不同集合通信算法",
                "iterations": 1000,
                "data_size_mb": 128,
                "operations": ["AllReduce", "AllToAll", "AllGather", "ReduceScatter"],
                "purpose": "算法选择"
            },
            {
                "name": "扩展性测试",
                "description": "测试不同规模的性能",
                "iterations": 1000,
                "data_sizes_mb": [16, 32, 64, 128, 256, 512],
                "operations": ["AllReduce"],
                "purpose": "扩展性分析"
            },
            {
                "name": "混合负载测试",
                "description": "模拟真实训练场景",
                "iterations": 1000,
                "operations": [
                    ("AllReduce", 512 * 1024 * 1024),  # 梯度聚合
                    ("AllToAll", 128 * 1024 * 1024),   # MoE通信
                    ("Broadcast", 64 * 1024 * 1024)    # 参数分发
                ],
                "purpose": "真实场景"
            }
        ]
        
        for scenario in test_scenarios:
            print(f"\n【{scenario['name']}】")
            print(f"描述: {scenario['description']}")
            print(f"目的: {scenario['purpose']}")
            
            # 生成操作列表
            operations = []
            
            if "data_sizes_mb" in scenario:
                # 扩展性测试：多个数据大小
                for size_mb in scenario["data_sizes_mb"]:
                    for op_type in scenario["operations"]:
                        operations.append(self.generate_collective_operation(
                            op_type=op_type,
                            data_size=size_mb * 1024 * 1024,
                            iteration_count=scenario["iterations"],
                            compute_cycles=1000
                        ))
            elif isinstance(scenario["operations"][0], tuple):
                # 混合负载：不同操作和数据大小
                for op_type, data_size in scenario["operations"]:
                    operations.append(self.generate_collective_operation(
                        op_type=op_type,
                        data_size=data_size,
                        iteration_count=scenario["iterations"],
                        compute_cycles=1000
                    ))
            else:
                # 标准测试：相同操作
                data_size_mb = scenario.get("data_size_mb", 256)
                for op_type in scenario["operations"]:
                    operations.append(self.generate_collective_operation(
                        op_type=op_type,
                        data_size=data_size_mb * 1024 * 1024,
                        iteration_count=scenario["iterations"],
                        compute_cycles=1000
                    ))
            
            # 生成workload文件
            filename = f"scenario_{scenario['name'].replace(' ', '_')}.workload"
            
            filepath = self.create_workload_file(
                filename=filename,
                operations=operations,
                metadata={
                    "scenario_name": scenario["name"],
                    "description": scenario["description"],
                    "purpose": scenario["purpose"],
                    "iterations": scenario["iterations"]
                }
            )
            
            print(f"  ✅ {filename} ({len(operations)} 个操作)")
            
            self.results["test_scenarios"].append({
                "name": scenario["name"],
                "filename": filename,
                "operation_count": len(operations),
                "description": scenario["description"]
            })
    
    def generate_gpu_scale_workloads(self):
        """生成不同GPU规模的workload"""
        print("\n=== 生成不同GPU规模的Workload ===\n")
        
        # 定义GPU规模
        gpu_scales = [
            {"gpus": 4, "nodes": 1, "category": "边缘"},
            {"gpus": 8, "nodes": 1, "category": "单节点"},
            {"gpus": 16, "nodes": 2, "category": "小规模"},
            {"gpus": 32, "nodes": 4, "category": "中规模"},
            {"gpus": 64, "nodes": 8, "category": "大规模"},
            {"gpus": 128, "nodes": 16, "category": "超大规模"}
        ]
        
        data_size = 256 * 1024 * 1024  # 256 MB
        
        for scale in gpu_scales:
            print(f"\n【{scale['gpus']} GPU ({scale['nodes']} 节点) - {scale['category']}】")
            
            # 推荐算法
            recommended_algorithm = "DBT" if scale["nodes"] == 1 else "Ring"
            
            filename = f"scale_{scale['gpus']}gpu_{scale['nodes']}node.workload"
            
            operation = self.generate_collective_operation(
                op_type="AllReduce",
                data_size=data_size,
                iteration_count=1000,
                compute_cycles=1000
            )
            
            filepath = self.create_workload_file(
                filename=filename,
                operations=[operation],
                metadata={
                    "gpu_count": scale["gpus"],
                    "node_count": scale["nodes"],
                    "category": scale["category"],
                    "recommended_algorithm": recommended_algorithm
                }
            )
            
            print(f"  ✅ {filename}")
            print(f"  推荐算法: {recommended_algorithm}")
    
    def generate_comparison_suite(self):
        """生成完整的对比测试套件"""
        print("\n=== 生成对比测试套件 ===\n")
        
        # 固定配置
        data_size_mb = 256
        iterations = 1000
        data_size = data_size_mb * 1024 * 1024
        
        # 所有集合通信操作
        all_operations = [
            "AllReduce", "AllToAll", "Broadcast", "AllGather",
            "ReduceScatter", "Reduce", "Gather", "Scatter"
        ]
        
        print(f"配置: {data_size_mb} MB, {iterations} 次迭代")
        print(f"操作: {', '.join(all_operations)}")
        
        # 生成对比套件
        for op_type in all_operations:
            filename = f"compare_{op_type}_{data_size_mb}MB.workload"
            
            operation = self.generate_collective_operation(
                op_type=op_type,
                data_size=data_size,
                iteration_count=iterations,
                compute_cycles=1000
            )
            
            filepath = self.create_workload_file(
                filename=filename,
                operations=[operation],
                metadata={
                    "suite": "comparison",
                    "data_size_mb": data_size_mb,
                    "iterations": iterations
                }
            )
            
            print(f"  ✅ {filename}")
    
    def generate_index_file(self):
        """生成workload索引文件"""
        print("\n=== 生成Workload索引 ===\n")
        
        index_file = self.output_dir / "WORKLOAD_INDEX.md"
        
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write("# SimAI Workload索引\n\n")
            f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
            f.write(f"**Workload数量**: {len(self.workloads)}\n\n")
            
            # 按类别组织
            f.write("## 1. 按规模分类\n\n")
            
            for category in self.results.get("size_categories", []):
                f.write(f"### {category['name']}\n\n")
                f.write(f"**描述**: {category['description']}\n\n")
                f.write(f"**数据大小**: {category['data_sizes_mb']} MB\n\n")
                f.write(f"**应用场景**: {', '.join(category['use_cases'])}\n\n")
                
                # 列出相关workload
                related_workloads = [
                    w for w in self.workloads
                    if w.get("metadata", {}).get("size_category") == category['name']
                ]
                
                if related_workloads:
                    f.write("**Workload文件**:\n")
                    for w in related_workloads:
                        f.write(f"- `{os.path.basename(w['filename'])}`\n")
                    f.write("\n")
            
            f.write("## 2. 按集合通信模式分类\n\n")
            
            for pattern in self.results.get("collective_operations", []):
                f.write(f"### {pattern['name']}\n\n")
                f.write(f"**描述**: {pattern['description']}\n\n")
                f.write(f"**典型应用**: {pattern['typical_use']}\n\n")
                f.write(f"**性能**: {pattern['performance']}\n\n")
            
            f.write("## 3. 测试场景\n\n")
            
            for scenario in self.results.get("test_scenarios", []):
                f.write(f"### {scenario['name']}\n\n")
                f.write(f"**描述**: {scenario['description']}\n\n")
                f.write(f"**操作数**: {scenario['operation_count']}\n\n")
                f.write(f"**文件**: `{scenario['filename']}`\n\n")
            
            f.write("## 4. 使用指南\n\n")
            f.write("### 运行单个Workload\n\n")
            f.write("```bash\n")
            f.write("# 编译SimAI（如果还未编译）\n")
            f.write("cd astra-sim-alibabacloud\n")
            f.write("./build.sh -c analytical\n\n")
            f.write("# 运行workload\n")
            f.write("./build/simai_analytical/build/simai_analytical/SimAI_analytical \\\n")
            f.write("  inputs/workload/your_workload.workload \\\n")
            f.write("  inputs/config/your_config.cfg \\\n")
            f.write("  inputs/topo/your_topo.txt \\\n")
            f.write("  simulation_output\n")
            f.write("```\n\n")
            
            f.write("### 批量运行Workload\n\n")
            f.write("```bash\n")
            f.write("# 使用批量测试脚本\n")
            f.write("for workload in priority1_advanced_workloads/*.workload; do\n")
            f.write("  echo \"Running $workload...\"\n")
            f.write("  ./build/simai_analytical/build/simai_analytical/SimAI_analytical \\\n")
            f.write("    \"$workload\" \\\n")
            f.write("    inputs/config/default.cfg \\\n")
            f.write("    inputs/topo/default.txt \\\n")
            f.write("    simulation_output\n")
            f.write("done\n")
            f.write("```\n\n")
            
            f.write("### 选择合适的Workload\n\n")
            f.write("- **快速测试**: 使用 `scenario_快速性能测试.workload`\n")
            f.write("- **标准测试**: 使用 `scenario_标准性能测试.workload`\n")
            f.write("- **算法对比**: 使用 `scenario_算法对比测试.workload`\n")
            f.write("- **扩展性测试**: 使用 `scenario_扩展性测试.workload`\n")
            f.write("- **真实场景**: 使用 `scenario_混合负载测试.workload`\n\n")
            
            f.write("## 5. Workload命名规范\n\n")
            f.write("- `small_<operation>_<size>MB.workload` - 小规模workload\n")
            f.write("- `medium_<operation>_<size>MB.workload` - 中规模workload\n")
            f.write("- `large_<operation>_<size>MB.workload` - 大规模workload\n")
            f.write("- `pattern_<operation>_<size>MB.workload` - 集合通信模式\n")
            f.write("- `scenario_<name>.workload` - 测试场景\n")
            f.write("- `scale_<gpus>gpu_<nodes>node.workload` - GPU规模\n")
            f.write("- `compare_<operation>_<size>MB.workload` - 对比测试\n\n")
            
            f.write("---\n\n")
            f.write(f"*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n")
            f.write("*工具: priority1_advanced_workload_generator.py*\n")
            f.write("*记录人: 二愣子 🤔*\n")
        
        print(f"✅ Workload索引已生成: {index_file}")
    
    def save_results(self):
        """保存生成结果"""
        import json
        
        results_file = self.output_dir / "generation_results.json"
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ 生成结果已保存: {results_file}")
    
    def run_full_generation(self):
        """运行完整的workload生成流程"""
        print("=" * 70)
        print("SimAI增强版Workload生成器 - 优先级1扩展")
        print("=" * 70)
        
        # 1. 生成不同规模的workload
        self.generate_size_category_workloads()
        
        # 2. 生成不同集合通信模式的workload
        self.generate_collective_pattern_workloads()
        
        # 3. 生成测试场景的workload
        self.generate_test_scenario_workloads()
        
        # 4. 生成不同GPU规模的workload
        self.generate_gpu_scale_workloads()
        
        # 5. 生成对比测试套件
        self.generate_comparison_suite()
        
        # 6. 生成索引文件
        self.generate_index_file()
        
        # 7. 保存结果
        self.save_results()
        
        print("\n" + "=" * 70)
        print("✅ Workload生成完成！")
        print("=" * 70)
        print(f"\n总生成数: {len(self.workloads)} 个workload")
        print(f"输出目录: {self.output_dir}")
        print("\nWorkload分类:")
        print(f"  - 规模分类: {len(self.results.get('size_categories', []))} 类")
        print(f"  - 集合通信模式: {len(self.results.get('collective_operations', []))} 种")
        print(f"  - 测试场景: {len(self.results.get('test_scenarios', []))} 个")
        print(f"  - GPU规模: 6 种 (4-128 GPU)")

def main():
    generator = AdvancedWorkloadGenerator()
    generator.run_full_generation()

if __name__ == "__main__":
    main()

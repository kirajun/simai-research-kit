#!/usr/bin/env python3
"""
SimAI高级Workload生成器 - 扩展版

用途：生成全面的workload测试集
特性：
- 不同规模（小/中/大）
- 所有集合通信操作
- 混合并行策略（TP+PP+DP）
- 自动批量测试脚本

作者：SimAI深度研究项目
日期：2026-02-17
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict

@dataclass
class WorkloadConfig:
    """Workload配置"""
    name: str
    description: str
    gpu_count: int
    tp: int = 1
    pp: int = 1
    dp: int = 1
    ep: int = 1
    layers: int = 32
    compute_time_ns: int = 10000000  # 默认10ms
    comm_op: str = "ALLREDUCE"
    data_size_mb: float = 16.0
    num_ops: int = 1  # 每层通信操作数量

class AdvancedWorkloadGenerator:
    """高级Workload生成器"""
    
    def __init__(self, output_dir: str = "advanced_workloads"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.test_metadata = []
    
    def generate_workload(self, config: WorkloadConfig) -> str:
        """
        生成单个workload
        
        Args:
            config: Workload配置
        
        Returns:
            生成的文件路径
        """
        lines = []
        lines.append(f"# {config.description}")
        lines.append(f"# 配置: {config.gpu_count} GPU, TP={config.tp}, PP={config.pp}, DP={config.dp}, EP={config.ep}")
        lines.append(f"# 通信: {config.comm_op}, 数据大小: {config.data_size_mb}MB/操作")
        lines.append("")
        
        # DATA行
        total_parallel = config.tp * config.pp * config.dp * config.ep
        assert total_parallel == config.gpu_count, f"并行配置错误: {total_parallel} != {config.gpu_count}"
        
        data_line = (f"DATA model_parallel_NPU_group: {config.tp} "
                    f"ep: {config.ep} "
                    f"pp: {config.pp} "
                    f"vpp: {config.layers} "
                    f"ga: 1 "
                    f"all_gpus: {config.gpu_count} "
                    f"checkpoints: 0 "
                    f"checkpoint_initiates: 0")
        lines.append(data_line)
        lines.append(str(config.layers))
        
        # 生成层配置
        data_size_bytes = int(config.data_size_mb * 1024 * 1024)
        
        for layer in range(1, config.layers + 1):
            layer_name = f"layer{layer:02d}"
            
            # 构建workload行
            # 格式: 层名 层ID 计算时间 操作1 数据1 通道1 操作2 数据2 通道2 ...
            parts = [layer_name, "-1", str(config.compute_time_ns)]
            
            # 添加通信操作
            for op_idx in range(config.num_ops):
                if config.num_ops == 1:
                    # 单操作
                    parts.extend([config.comm_op, str(data_size_bytes), "1"])
                    parts.extend(["NONE", "0", "1"])
                else:
                    # 多操作（混合）
                    ops = ["ALLREDUCE", "ALLGATHER", "REDUCESCATTER", "ALLTOALL", "BROADCAST"]
                    op = ops[op_idx % len(ops)]
                    parts.extend([op, str(data_size_bytes), "1"])
            
            # 确保有NONE操作填充
            if len(parts) < 9:
                parts.extend(["NONE", "0", "1"])
            
            lines.append("    ".join(parts))
        
        # 写入文件
        content = "\n".join(lines)
        filename = f"{config.name}.workload"
        output_path = self.output_dir / filename
        
        with open(output_path, 'w') as f:
            f.write(content)
        
        # 记录元数据
        self.test_metadata.append({
            "name": config.name,
            "config": asdict(config),
            "file": str(output_path)
        })
        
        print(f"✓ 生成: {filename}")
        print(f"  描述: {config.description}")
        print(f"  配置: {config.gpu_count}GPU, TP={config.tp}, PP={config.pp}, DP={config.dp}, EP={config.ep}")
        print(f"  通信: {config.comm_op} x{config.num_ops}, {config.data_size_mb}MB/操作")
        
        return str(output_path)
    
    def generate_scale_test_suite(self):
        """生成规模测试套件（小/中/大）"""
        print("\n" + "="*60)
        print("生成规模测试套件")
        print("="*60 + "\n")
        
        # 小规模测试
        print("【小规模】快速验证测试")
        self.generate_workload(WorkloadConfig(
            name="scale_small_4gpu",
            description="小规模测试 - 4 GPU (单节点)",
            gpu_count=4,
            tp=2,
            pp=1,
            dp=2,
            layers=16,
            data_size_mb=8.0,
            comm_op="ALLREDUCE"
        ))
        
        print()
        
        # 中规模测试
        print("【中规模】标准训练测试")
        self.generate_workload(WorkloadConfig(
            name="scale_medium_8gpu",
            description="中规模测试 - 8 GPU (单节点)",
            gpu_count=8,
            tp=2,
            pp=1,
            dp=4,
            layers=32,
            data_size_mb=16.0,
            comm_op="ALLREDUCE"
        ))
        
        print()
        
        # 大规模测试
        print("【大规模】分布式训练测试")
        self.generate_workload(WorkloadConfig(
            name="scale_large_32gpu",
            description="大规模测试 - 32 GPU (4节点)",
            gpu_count=32,
            tp=4,
            pp=2,
            dp=4,
            layers=32,
            data_size_mb=32.0,
            comm_op="ALLREDUCE"
        ))
        
        print()
    
    def generate_comm_pattern_suite(self):
        """生成通信模式测试套件"""
        print("\n" + "="*60)
        print("生成通信模式测试套件")
        print("="*60 + "\n")
        
        comm_ops = [
            ("ALLREDUCE", "梯度同步（最常用）"),
            ("ALLGATHER", "参数收集（TP常用）"),
            ("REDUCESCATTER", "梯度分散"),
            ("ALLTOALL", "MoE路由、EP通信"),
            ("BROADCAST", "参数广播")
        ]
        
        base_config = WorkloadConfig(
            name="base",
            description="base",
            gpu_count=8,
            tp=2,
            pp=1,
            dp=4,
            layers=16,
            data_size_mb=16.0
        )
        
        for op, desc in comm_ops:
            config = base_config
            config.name = f"pattern_{op.lower()}_8gpu"
            config.description = f"{desc} - 8 GPU测试"
            config.comm_op = op
            self.generate_workload(config)
            print()
    
    def generate_parallelism_suite(self):
        """生并行策略测试套件"""
        print("\n" + "="*60)
        print("生成并行策略测试套件")
        print("="*60 + "\n")
        
        # 纯TP
        print("【张量并行】高通信带宽需求")
        self.generate_workload(WorkloadConfig(
            name="parallel_tp_only",
            description="纯TP - 8 GPU, 高带宽",
            gpu_count=8,
            tp=8,
            pp=1,
            dp=1,
            layers=16,
            data_size_mb=32.0,  # TP需要大带宽
            comm_op="ALLGATHER"
        ))
        
        print()
        
        # 纯DP
        print("【数据并行】低通信频率")
        self.generate_workload(WorkloadConfig(
            name="parallel_dp_only",
            description="纯DP - 8 GPU, 低频率",
            gpu_count=8,
            tp=1,
            pp=1,
            dp=8,
            layers=16,
            data_size_mb=16.0,
            comm_op="ALLREDUCE"
        ))
        
        print()
        
        # TP+DP混合
        print("【混合并行】TP+DP")
        self.generate_workload(WorkloadConfig(
            name="parallel_tp_dp",
            description="混合TP+DP - 8 GPU",
            gpu_count=8,
            tp=2,
            pp=1,
            dp=4,
            layers=16,
            data_size_mb=16.0,
            comm_op="ALLREDUCE"
        ))
        
        print()
        
        # TP+PP+DP
        print("【3D并行】TP+PP+DP")
        self.generate_workload(WorkloadConfig(
            name="parallel_3d",
            description="3D并行 TP+PP+DP - 8 GPU",
            gpu_count=8,
            tp=2,
            pp=2,
            dp=2,
            layers=32,
            data_size_mb=12.0,
            comm_op="ALLREDUCE"
        ))
        
        print()
        
        # EP（MoE）
        print("【专家并行】MoE训练")
        self.generate_workload(WorkloadConfig(
            name="parallel_ep_moe",
            description="专家并行 - 8 GPU",
            gpu_count=8,
            tp=1,
            pp=1,
            dp=1,
            ep=8,
            layers=16,
            data_size_mb=24.0,
            comm_op="ALLTOALL"  # MoE用ALLTOALL
        ))
        
        print()
    
    def generate_data_size_suite(self):
        """生成数据大小测试套件"""
        print("\n" + "="*60)
        print("生成数据大小测试套件")
        print("="*60 + "\n")
        
        data_sizes = [1.0, 4.0, 16.0, 64.0, 256.0]  # MB
        
        for size_mb in data_sizes:
            self.generate_workload(WorkloadConfig(
                name=f"datasize_{int(size_mb)}mb",
                description=f"数据大小测试 - {size_mb}MB",
                gpu_count=8,
                tp=2,
                dp=4,
                layers=16,
                data_size_mb=size_mb,
                comm_op="ALLREDUCE"
            ))
            print()
    
    def generate_hybrid_suite(self):
        """生成混合通信模式测试套件"""
        print("\n" + "="*60)
        print("生成混合通信模式测试套件")
        print("="*60 + "\n")
        
        # TP+DP混合通信
        print("【TP+DP混合】ALLGATHER + ALLREDUCE")
        config = WorkloadConfig(
            name="hybrid_tp_dp",
            description="TP通信(ALLGATHER) + DP通信(ALLREDUCE)",
            gpu_count=8,
            tp=2,
            dp=4,
            layers=16,
            data_size_mb=16.0,
            num_ops=2  # 两个通信操作
        )
        
        # 手动生成特殊格式
        lines = []
        lines.append(f"# {config.description}")
        lines.append(f"# 配置: {config.gpu_count} GPU, TP={config.tp}, DP={config.dp}")
        lines.append("")
        lines.append(f"DATA model_parallel_NPU_group: {config.tp} ep: {config.ep} pp: {config.pp} vpp: {config.layers} ga: 1 all_gpus: {config.gpu_count} checkpoints: 0 checkpoint_initiates: 0")
        lines.append(str(config.layers))
        
        data_size = int(config.data_size_mb * 1024 * 1024)
        
        for layer in range(1, config.layers + 1):
            layer_name = f"layer{layer:02d}"
            # TP通信（ALLGATHER）+ DP通信（ALLREDUCE）
            line = f"{layer_name}    -1   {config.compute_time_ns}   ALLGATHER    {data_size}   1   ALLREDUCE    {data_size}   1"
            lines.append(line)
        
        content = "\n".join(lines)
        output_path = self.output_dir / f"{config.name}.workload"
        
        with open(output_path, 'w') as f:
            f.write(content)
        
        print(f"✓ 生成: {config.name}.workload")
        print(f"  描述: {config.description}")
        print(f"  操作: ALLGATHER(TP) + ALLREDUCE(DP)")
        print()
    
    def save_metadata(self):
        """保存测试元数据"""
        metadata_path = self.output_dir / "test_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(self.test_metadata, f, indent=2)
        print(f"✓ 元数据已保存: {metadata_path}")
    
    def generate_bash_runner(self):
        """生成bash测试脚本"""
        script_path = self.output_dir / "run_all_tests.sh"
        
        with open(script_path, 'w') as f:
            f.write("""#!/bin/bash
# SimAI Workload批量测试脚本
# 自动生成: advanced_workload_generator.py

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SIMAI_DIR="$SCRIPT_DIR/../SimAI"

echo "========================================="
echo "SimAI批量测试 - 共""" + str(len(self.test_metadata)) + """个workload"
echo "========================================="
echo ""

# 检查SimAI是否已编译
if [ ! -f "$SIMAI_DIR/astra-sim-alibabacloud/build/analytical/astra_analytical" ]; then
    echo "错误: SimAI未编译，请先运行:"
    echo "  cd $SIMAI_DIR/astra-sim-alibabacloud && ./build.sh -c analytical"
    exit 1
fi

# 运行每个测试
passed=0
failed=0

for workload in *.workload; do
    if [ -f "$workload" ]; then
        echo "----------------------------------------"
        echo "测试: $workload"
        echo "----------------------------------------"
        
        if bash "$SIMAI_DIR/aicb/scripts/run_workload.sh" "$workload"; then
            echo "✓ $workload: 通过"
            ((passed++))
        else
            echo "✗ $workload: 失败"
            ((failed++))
        fi
        echo ""
    fi
done

echo "========================================="
echo "测试完成: 通过=$passed, 失败=$failed"
echo "========================================="
""")
        
        os.chmod(script_path, 0o755)
        print(f"✓ 测试脚本已生成: {script_path}")

def main():
    """主函数"""
    print("="*60)
    print("SimAI高级Workload生成器")
    print("="*60)
    print()
    
    # 创建生成器
    generator = AdvancedWorkloadGenerator()
    
    # 生成所有测试套件
    generator.generate_scale_test_suite()
    generator.generate_comm_pattern_suite()
    generator.generate_parallelism_suite()
    generator.generate_data_size_suite()
    generator.generate_hybrid_suite()
    
    # 保存元数据和脚本
    generator.save_metadata()
    generator.generate_bash_runner()
    
    print("\n" + "="*60)
    print(f"✓ 全部完成! 共生成 {len(generator.test_metadata)} 个workload")
    print(f"  输出目录: {generator.output_dir}")
    print(f"  测试脚本: {generator.output_dir}/run_all_tests.sh")
    print("="*60)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
基础示例：生成和分析workload
"""

from simai_tools.workload.advanced_workload_generator import AdvancedWorkloadGenerator
from simai_tools.analysis.performance_analyzer import PerformanceAnalyzer

def main():
    # 1. 生成workload
    print("生成workload...")
    generator = AdvancedWorkloadGenerator()
    workload = generator.generate_workload(
        num_gpus=16,
        data_size_mb=64,
        collective_op="allreduce"
    )
    workload.save("examples/basic/my_workload.workload")

    # 2. 分析性能
    print("\n分析性能...")
    analyzer = PerformanceAnalyzer()

    # 模拟结果（实际应从SimAI获取）
    import pandas as pd
    results = pd.DataFrame({{
        "num_gpus": [2, 4, 8, 16],
        "time_ms": [0.5, 0.8, 1.5, 3.2],
        "throughput_gb_s": [32.0, 64.0, 85.3, 128.0]
    }})

    # 3. 绘制扩展性曲线
    analyzer.plot_scaling_efficiency(results, save_path="examples/basic/scaling.png")
    print("\n✅ 完成！查看 scaling.png")

if __name__ == "__main__":
    main()

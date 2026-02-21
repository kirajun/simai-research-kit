#!/usr/bin/env python3
"""
高级示例：参数优化
"""

from simai_tools.optimization.priorityG_intelligent_parameter_optimization import PriorityGIntelligentParameterOptimization

def main():
    print("智能参数优化...")

    optimizer = PriorityGIntelligentParameterOptimization()

    # 使用随机搜索优化参数
    best_params = optimizer.optimize(
        target_data="examples/data/pytorch_ddp_sample.csv",
        method="random_search",
        n_iterations=100
    )

    print(f"\n最优参数:")
    print(f"  带宽: {{best_params['bandwidth']}} Gbps")
    print(f"  延迟: {{best_params['latency']}} μs")
    print(f"  MAPE: {{best_params['mape']}}%")

    # 对比优化前后
    optimizer.plot_optimization_history(save_path="examples/advanced/optimization_history.png")

if __name__ == "__main__":
    main()

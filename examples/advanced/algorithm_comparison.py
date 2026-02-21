#!/usr/bin/env python3
"""
高级示例：算法对比分析
"""

from simai_tools.algorithm.algorithm_comparison_analysis import AlgorithmComparisonAnalysis

def main():
    print("算法对比分析...")

    comparison = AlgorithmComparisonAnalysis()

    # 对比多种算法
    algorithms = ["ring", "tree", "dbt", "recursive_doubling", "hierarchical"]
    num_gpus = [16, 32, 64, 128]

    results = comparison.compare_algorithms(
        algorithms=algorithms,
        num_gpus=num_gpus,
        data_sizes=[64, 128, 256]
    )

    # 绘制对比图
    comparison.plot_performance_comparison(results, save_path="examples/advanced/algorithm_comparison.png")
    comparison.plot_algorithm_selection(results, save_path="examples/advanced/algorithm_selection.png")

    print("\n✅ 完成！查看对比图")

    # 显示最优算法
    for gpu_count in num_gpus:
        best = comparison.find_best_algorithm(results, gpu_count)
        print(f"  {{gpu_count}} GPU: {{best}}")

if __name__ == "__main__":
    main()

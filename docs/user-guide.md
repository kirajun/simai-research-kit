# SimAI Research Kit - 用户指南

## 目录

1. [快速开始](#快速开始)
2. [工具详解](#工具详解)
3. [常见问题](#常见问题)
4. [最佳实践](#最佳实践)
5. [进阶使用](#进阶使用)

## 快速开始

### 环境要求

- Python 3.8 或更高版本
- NumPy
- Pandas
- Matplotlib

### 安装

```bash
pip install -r requirements.txt
```

### 第一个示例

生成一个简单的AllReduce workload：

```python
from simai_tools.workload.advanced_workload_generator import AdvancedWorkloadGenerator

# 创建生成器
generator = AdvancedWorkloadGenerator()

# 生成workload
workload = generator.generate_workload(
    num_gpus=16,
    data_size_mb=64,
    collective_op="allreduce",
    algorithm="dbt"
)

# 保存
workload.save("my_first_workload.workload")
```

## 工具详解

### 1. Workload生成工具

#### AdvancedWorkloadGenerator

高级workload生成器，支持多种训练场景。

**参数**:
- `num_gpus`: GPU数量
- `data_size_mb`: 数据大小（MB）
- `collective_op`: 集合操作类型
- `algorithm`: 算法类型

**示例**:

```python
# GPT-3训练workload
gpt3_workload = generator.generate_training_workload(
    num_gpus=1024,
    model_size_gb=1750,
    batch_size=32,
    seq_length=2048
)
```

#### InferenceWorkloadGenerator

推理workload生成器。

**示例**:

```python
from simai_tools.workload.inference_workload_generator import InferenceWorkloadGenerator

inference_gen = InferenceWorkloadGenerator()
bert_inference = inference_gen.generate_bert_inference(
    num_gpus=8,
    batch_size=32,
    seq_length=512
)
```

### 2. 性能分析工具

#### PerformanceAnalyzer

性能分析器，分析仿真结果。

**功能**:
- 扩展性分析
- 瓶颈识别
- 优化建议

**示例**:

```python
from simai_tools.analysis.performance_analyzer import PerformanceAnalyzer

analyzer = PerformanceAnalyzer()

# 分析结果
results = analyzer.analyze_results("results.csv")

# 绘制扩展性曲线
analyzer.plot_scaling_efficiency(results, save_path="scaling.png")

# 生成优化建议
suggestions = analyzer.generate_suggestions(results)
print(suggestions)
```

#### GPUScalingEfficiencyDeepAnalysis

GPU扩展效率深度分析。

**功能**:
- 效率异常检测
- 多维度对比
- 趋势预测

**示例**:

```python
from simai_tools.analysis.gpu_scaling_efficiency_deep_analysis import GPUScalingEfficiencyDeepAnalysis

deep_analysis = GPUScalingEfficiencyDeepAnalysis()
report = deep_analysis.analyze_scaling_efficiency(
    results_df,
    dimensions=["gpu_count", "data_size"]
)
deep_analysis.save_report("efficiency_report.md")
```

### 3. 算法研究工具

#### AlgorithmComparisonAnalysis

算法对比分析工具。

**支持算法**:
- Ring
- Tree
- DBT (Double Binary Tree)
- RecursiveDoubling
- HalvingDoubling
- Hierarchical

**示例**:

```python
from simai_tools.algorithm.algorithm_comparison_analysis import AlgorithmComparisonAnalysis

comparison = AlgorithmComparisonAnalysis()

# 对比多种算法
results = comparison.compare_algorithms(
    algorithms=["ring", "tree", "dbt", "recursive_doubling"],
    num_gpus=[16, 32, 64, 128],
    data_sizes=[16, 64, 256]
)

# 绘制对比图
comparison.plot_performance_comparison(results)
comparison.plot_algorithm_selection(results)
```

#### CollectiveAlgorithmDeepAnalysis

集合通信算法深度分析。

**功能**:
- 算法原理分析
- 步数计算
- 性能预测

**示例**:

```python
from simai_tools.algorithm.collective_algorithm_deep_analysis import CollectiveAlgorithmDeepAnalysis

deep_analyzer = CollectiveAlgorithmDeepAnalysis()

# 分析特定算法
analysis = deep_analyzer.analyze_algorithm(
    algorithm="recursive_doubling",
    num_gpus=32,
    data_size_mb=128
)

print(f"步数: {analysis['steps']}")
print(f"预估时间: {analysis['time_ms']} ms")
```

### 4. 参数调优工具

#### ParameterTuningExperiments

参数调优实验工具。

**可调参数**:
- 带宽 (Bandwidth)
- 延迟 (Latency)
- Ratio表
- 拓扑类型

**示例**:

```python
from simai_tools.parameter.parameter_tuning_experiments import ParameterTuningExperiments

tuner = ParameterTuningExperiments()

# 带宽敏感度测试
bandwidth_results = tuner.test_bandwidth_sensitivity(
    bandwidths=[10, 25, 50, 100, 200],
    num_gpus=32,
    data_size_mb=64
)

# 寻找最优参数
optimal = tuner.find_optimal_parameters(
    target_metric="time_ms",
    optimization="minimize"
)
```

#### PriorityGIntelligentParameterOptimization

智能参数优化工具。

**优化算法**:
- 网格搜索
- 随机搜索
- 模拟退火

**示例**:

```python
from simai_tools.optimization.priorityG_intelligent_parameter_optimization import PriorityGIntelligentParameterOptimization

optimizer = PriorityGIntelligentParameterOptimization()

# 自动优化参数
best_params = optimizer.optimize(
    target_data="pytorch_ddp_results.csv",
    method="random_search",  # or "grid_search", "simulated_annealing"
    n_iterations=100
)

print(f"最优带宽: {best_params['bandwidth']} Gbps")
print(f"最优延迟: {best_params['latency']} μs")
```

### 5. 可视化工具

#### AdvancedVisualizationDashboard

高级可视化仪表板。

**功能**:
- 交互式图表
- 多维度对比
- 实时更新

**示例**:

```python
from simai_tools.visualization.advanced_visualization_dashboard import AdvancedVisualizationDashboard

dashboard = AdvancedVisualizationDashboard()

# 创建仪表板
dashboard.create_dashboard(
    data_df,
    metrics=["time_ms", "throughput_gb_s"],
    dimensions=["gpu_count", "algorithm"]
)

# 启动Web界面
dashboard.launch(port=8080)
```

#### SimAIVisualizationDashboard

SimAI专用可视化仪表板。

**示例**:

```python
from simai_tools.visualization.simai_visualization_dashboard import SimAIVisualizationDashboard

simai_dashboard = SimAIVisualizationDashboard()
simai_dashboard.load_results("simai_results.csv")
simai_dashboard.plot_all(save_dir="plots/")
```

### 6. 集成实践工具

#### Priority5IntegrationPractice

端到端集成实践框架。

**工作流**:
1. 需求分析
2. Workload生成
3. 仿真执行
4. 结果分析
5. 优化建议
6. 验证测试

**示例**:

```python
from simai_tools.integration.priority5_integration_practice import Priority5IntegrationPractice

framework = Priority5IntegrationPractice()

# 端到端仿真
workflow_result = framework.run_end_to_end_workflow(
    scenario="gpt3_training",
    num_gpus=1024,
    model_size_gb=1750
)

# 查看结果
print(workflow_result["summary"])
```

### 7. 性能优化工具

#### PriorityKModelImprovements

模型改进工具。

**优化类型**:
- Ratio表优化（算法感知、拓扑感知）
- 小消息优化
- 算法模型改进

**示例**:

```python
from simai_tools.optimization.priorityK_model_improvements import PriorityKModelImprovements

improver = PriorityKModelImprovements()

# 应用改进
improved_model = improver.apply_improvements(
    base_model="default",
    improvements=["ratio_optimization", "small_message", "algorithm"]
)

# 对比改进前后
comparison = improver.compare_models(
    original_model="default",
    improved_model=improved_model
)
```

#### PriorityQRatioOptimizationImplementation

Ratio表优化实现。

**功能**:
- 拓扑感知Ratio表
- 算法感知Ratio表
- 自适应优化

**示例**:

```python
from simai_tools.optimization.priorityQ_ratio_optimization_implementation import OptimizedRatioTable

# 创建优化的Ratio表
ratio_table = OptimizedRatioTable(mode="topology_aware")

# 获取效率
efficiency = ratio_table.get_efficiency(
    num_nodes=8,
    topology="fat-tree",
    algorithm="recursive_doubling"
)

print(f"效率: {efficiency * 100}%")
```

### 8. 框架和工具链

#### PriorityMAutomatedWorkflowV2

自动化工作流引擎v2.0。

**工作流阶段**:
1. 需求分析
2. Workload生成
3. 仿真执行
4. 结果分析
5. 优化建议
6. 报告生成

**示例**:

```python
from simai_tools.framework.priorityM_automated_workflow_v2 import PriorityMAutomatedWorkflowV2

workflow = PriorityMAutomatedWorkflowV2()

# 运行单个工作流
result = workflow.run_workflow(
    num_gpus=32,
    data_size_mb=128,
    collective_op="allreduce"
)

# 批量运行
batch_results = workflow.run_batch_workflow(
    scenarios=["small", "medium", "large"]
)
```

## 常见问题

### Q1: SimAI是什么？

SimAI是一个GPU集群集合通信性能仿真工具，可以预测分布式训练的性能，无需真实硬件。

### Q2: 如何选择算法？

根据GPU规模选择：
- ≤4 GPU: Ring或RecursiveDoubling
- 8-16 GPU: DBT
- ≥32 GPU: Hierarchical

### Q3: Ratio表是什么？

Ratio表是SimAI用于估算多节点效率的表格。单节点效率约80%，8节点约30%，是性能的主要瓶颈。

### Q4: 如何提高仿真准确性？

1. 使用实测数据校准参数
2. 选择合适的拓扑类型
3. 应用Ratio表优化
4. 使用算法感知模型

### Q5: 支持哪些集合操作？

AllReduce、AllToAll、Broadcast、Reduce、ReduceScatter、AllGather

## 最佳实践

### 1. 从小规模开始

先在小规模GPU（2-8个）上验证，再扩展到大规模。

### 2. 使用真实数据

使用真实训练场景的数据大小和模型参数。

### 3. 对比多种算法

不要只依赖一种算法，对比多种算法选择最优。

### 4. 记录实验结果

保存每次仿真的参数和结果，便于后续分析。

### 5. 验证仿真准确性

在真实硬件上运行小规模测试，验证仿真的准确性。

## 进阶使用

### 自定义Workload

```python
# 创建自定义workload
custom_workload = generator.create_custom_workload(
    ops=[
        {"op": "allreduce", "size_mb": 128, "count": 10},
        {"op": "alltoall", "size_mb": 64, "count": 5},
        {"op": "broadcast", "size_mb": 256, "count": 2}
    ]
)
```

### 批量实验

```python
# 批量测试多种配置
configs = [
    {"num_gpus": 16, "data_size": 64},
    {"num_gpus": 32, "data_size": 128},
    {"num_gpus": 64, "data_size": 256}
]

for config in configs:
    result = run_simulation(config)
    save_result(result)
```

### 结果分析

```python
# 深度分析结果
analyzer = PerformanceAnalyzer()

# 瓶颈分析
bottlenecks = analyzer.identify_bottlenecks(results)

# 扩展性分析
scaling = analyzer.analyze_scaling(results)

# 优化建议
suggestions = analyzer.generate_suggestions(results)
```

## 参考资料

- [SimAI GitHub](https://github.com/aliyun/SimAI)
- [集合通信算法详解](docs/collective-algorithms.md)
- [性能优化指南](docs/performance-optimization.md)
- [API文档](docs/api/api-reference.md)

---

有问题？查看[常见问题](#常见问题)或提[Issue](https://github.com/yourusername/simai-research-kit/issues)。

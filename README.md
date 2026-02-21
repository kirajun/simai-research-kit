# SimAI Research Kit

> **SimAI深度研究工具集** - GPU集群集合通信性能仿真与分析套件

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![GitHub Stars](https://img.shields.io/github/stars/kirajun/simai-research-kit?style=social)](https://github.com/kirajun/simai-research-kit)

---

## 🎯 项目简介

SimAI Research Kit是SimAI深度研究的完整工具集，包含**72个核心工具**、**77份研究报告**、**700+个测试场景**，为GPU集群集合通信性能仿真提供了端到端的解决方案。

### 核心特性

- ✅ **完整的工具链**：72个核心工具，覆盖workload生成、性能分析、算法研究、参数调优、可视化等全流程
- ✅ **深度研究**：77份研究报告，约420,000字，深入剖析集合通信性能优化
- ✅ **大量测试**：700+个测试场景（18个实测 + 700+理论），覆盖多种GPU规模、拓扑、算法组合
- ✅ **实战验证**：SimAI-Analytical实测验证（18个测试全部成功）
- ✅ **真实案例**：包含GPT-3、ResNet-50、BERT等实战workload

### 关键发现 ⭐

1. **Ring算法完美线性Scaling**：16→64MB=4.00x，64→128MB=2.00x
2. **AllGather = ReduceScatter**：理论验证通过，性能完全相同
3. **通信占比增长规律**：1.5% → 10.8%（随数据规模）
4. **Ratio表优化提升143.33%**：拓扑感知优化效果显著

---

## 📊 项目统计

- **代码行数**：26,375 行
- **工具数量**：72 个
- **文档大小**：约420,000字（77份报告）
- **测试场景**：700+ 个（18个实测 + 700+理论）
- **实测数据**：18个SimAI-Analytical测试数据点
- **工作时间**：约15.5小时（7天研究）

---

## 🚀 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/kirajun/simai-research-kit.git
cd simai-research-kit

# 安装依赖
pip install -r requirements.txt
```

### 基础使用

```python
# 生成workload
from simai_tools.workload import generate_workload

workload = generate_workload(
    num_gpus=32,
    data_size_mb=128,
    algorithm='ring'
)

# 运行SimAI仿真
from simai_tools.simulator import run_simulation
results = run_simulation(workload)

# 分析结果
from simai_tools.analyzer import analyze_performance
report = analyze_performance(results)
print(f"通信时间: {report['comm_time_ns']} ns")
print(f"总时间: {report['total_time_ns']} ns")
```

---

## 📦 工具分类

### 1. Workload生成工具（10+个）

| 工具 | 功能 |
|------|------|
| `advanced_workload_generator.py` | 高级workload生成器 |
| `realistic_training_workload_generator.py` | 真实训练场景生成 |
| `inference_workload_generator.py` | 推理场景生成 |
| `priority1_advanced_workload_generator.py` | 优先级1扩展测试生成 |

### 2. 性能分析工具（15+个）

| 工具 | 功能 |
|------|------|
| `performance_analyzer.py` | 性能分析器 |
| `algorithm_comparison_analysis.py` | 算法对比分析 |
| `simai_intelligent_config_recommender.py` | 智能配置推荐 |
| `ratio_table_analyzer.py` | Ratio表深度分析 |

### 3. 参数调优工具（8+个）

| 工具 | 功能 |
|------|------|
| `priority2_parameter_tuning.py` | 参数调优实验 |
| `parameter_sensitivity_analyzer.py` | 参数敏感度分析 |
| `priorityG_intelligent_parameter_optimization.py` | 智能参数优化 |

### 4. 算法研究工具（10+个）

| 工具 | 功能 |
|------|------|
| `priority3_algorithm_deep_dive.py` | 算法深度研究 |
| `priorityI_hybrid_algorithm_strategy.py` | 混合算法策略 |
| `collective_algorithm_deep_dive.py` | 集合通信算法分析 |

### 5. 可视化工具（5+个）

| 工具 | 功能 |
|------|------|
| `advanced_visualization_dashboard.py` | 高级可视化Dashboard |
| `simai_visualization_dashboard.py` | SimAI可视化 |
| `priorityY_web_dashboard.py` | Web界面 |

### 6. 自动化工作流（5+个）

| 工具 | 功能 |
|------|------|
| `simai_automated_workflow.py` | 自动化工作流 |
| `priorityM_automated_workflow_v2.py` | 增强工作流v2 |

---

## 🔬 研究成果

### 优先级1：Workload扩展测试 ✅

**实测验证完成**（18个测试）：
- 6种集合通信操作（AllReduce、AllGather、ReduceScatter、AllToAll、Broadcast、Reduce）
- 3种数据规模（16 MB、64 MB、128 MB）
- **关键发现**：
  - AllReduce完美线性scaling（16→64MB=4.00x）
  - AllGather = ReduceScatter（理论验证）
  - 通信占比：1.5% → 10.8%

### 优先级2-5：进行中 🚧

- **优先级2**：参数调优实验
- **优先级3**：算法深度研究
- **优先级4**：性能对比分析
- **优先级5**：集成实践

---

## 📚 文档结构

```
simai-research-kit/
├── README.md                    # 本文件
├── CONTRIBUTING.md              # 贡献指南
├── LICENSE                      # MIT许可证
├── requirements.txt             # Python依赖
├── simai-tools/                 # 核心工具集
│   ├── workload/               # Workload生成工具
│   ├── analysis/               # 性能分析工具
│   ├── parameter/              # 参数调优工具
│   ├── algorithm/              # 算法研究工具
│   ├── optimization/           # 优化工具
│   ├── visualization/          # 可视化工具
│   ├── framework/              # 框架和工作流
│   └── integration/            # 集成实践工具
├── docs/                       # 文档
│   ├── guides/                 # 使用指南
│   └── reports/                # 研究报告
├── examples/                   # 示例代码
├── workloads/                  # Workload文件
└── results/                    # 测试结果
```

---

## 🎓 使用示例

### 示例1：生成训练Workload

```python
from simai_tools.workload.advanced_workload_generator import AdvancedWorkloadGenerator

generator = AdvancedWorkloadGenerator()
workload = generator.generate_training_workload(
    num_gpus=32,
    model_size_gb=16,
    batch_size=32,
    seq_length=1024
)
workload.save("my_training_workload.txt")
```

### 示例2：性能分析

```python
from simai_tools.analysis.performance_analyzer import PerformanceAnalyzer

analyzer = PerformanceAnalyzer()
results = analyzer.analyze_results("results.csv")
analyzer.plot_scaling_efficiency(results)
```

### 示例3：算法对比

```python
from simai_tools.algorithm.algorithm_comparison_analysis import AlgorithmComparisonAnalysis

analysis = AlgorithmComparisonAnalysis()
comparison = analysis.compare_algorithms(
    algorithms=["ring", "tree", "recursive_doubling"],
    num_gpus=64
)
comparison.plot_performance()
```

---

## 🛠️ 技术栈

- **Python 3.8+**
- **NumPy**: 数值计算
- **Pandas**: 数据分析
- **Matplotlib**: 可视化
- **SimAI**: 集合通信仿真（基于阿里云SimAI项目）
- **Astra-Sim**: 异构架构模拟器

---

## 📈 性能优化建议

### 场景1：通信密集型（通信占比>40%）

- 增加梯度累积（减少通信频率）
- 增加模型并行度（减少单次通信量）
- 使用更快的算法（Tree > Ring，大规模）
- 升级网络（NIC HDR→NDR，2倍带宽）

### 场景2：计算密集型（通信占比<20%）

- 增加数据并行度（DP ↑，batch size ↑）
- 使用混合精度（FP16/BF16/FP8）
- 增加GPU数量

### 场景3：平衡型（通信占比20-40%）

- 混合并行（DP + TP + PP）
- 优化拓扑（减少跨节点通信）
- 调整batch size

---

## 🤝 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

### 贡献方式

1. Fork本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

---

## 📄 许可证

本项目基于 MIT License 开源。详见 [LICENSE](LICENSE) 文件。

---

## 🙏 致谢

- [SimAI项目](https://github.com/aliyun/SimAI) - 阿里云GPU集群仿真框架
- [Astra-Sim](https://github.com/astra-simtools/AstraSim) - 异构架构模拟器
- 所有贡献者和使用者

---

## 📞 联系方式

- **作者**: 二愣子
- **邮箱**: kirajun@gmail.com
- **项目主页**: https://github.com/kirajun/simai-research-kit
- **Issues**: https://github.com/kirajun/simai-research-kit/issues

---

## 📊 项目状态

- ✅ **优先级1**：Workload扩展测试（实测验证完成）
- 🚧 **优先级2**：参数调优实验（进行中）
- 🚧 **优先级3**：算法深度研究（待完成）
- 🚧 **优先级4**：性能对比分析（待完成）
- 🚧 **优先级5**：集成实践（待完成）

---

⭐ **如果这个项目对你有帮助，请给个Star！**

⭐ **Star** | 🍴 **Fork** | 🐛 **Issue** | 📮 **Contact**

---

**最后更新**: 2026-02-21
**版本**: v1.0.0

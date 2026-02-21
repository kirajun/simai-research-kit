# 贡献指南

感谢你有兴趣为SimAI Research Kit做出贡献！

## 如何贡献

### 报告Bug

请在GitHub Issues中报告bug，包含：
- 问题描述
- 复现步骤
- 预期行为
- 实际行为
- 环境信息（Python版本、操作系统等）

### 提出新功能

在GitHub Issues中提出新功能建议前，请先检查：
- 是否已有类似建议
- 该功能是否符合项目目标
- 你是否愿意实现该功能

### 提交代码

1. Fork项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

### 代码规范

- 使用Python类型提示
- 添加docstring
- 遵循PEP 8规范
- 添加单元测试

### 提交信息格式

```
类型(范围): 简短描述

详细描述（可选）

关闭的Issue（可选）
```

类型：
- feat: 新功能
- fix: 修复bug
- docs: 文档更新
- style: 代码格式调整
- refactor: 重构
- test: 测试相关
- chore: 构建/工具链相关

示例：
```
feat(algorithm): 添加Mesh算法支持

- 实现Mesh算法性能模型
- 添加步数计算
- 添加单元测试

Closes #123
```

## 开发环境

### 设置开发环境

```bash
git clone https://github.com/yourusername/simai-research-kit.git
cd simai-research-kit
pip install -e .
pip install -r requirements-dev.txt
```

### 运行测试

```bash
pytest tests/
```

### 代码格式化

```bash
black simai-tools/
flake8 simai-tools/
```

## 项目结构

```
simai-research-kit/
├── simai-tools/          # 工具代码
│   ├── workload/         # Workload生成
│   ├── analysis/         # 性能分析
│   ├── algorithm/        # 算法研究
│   ├── parameter/        # 参数调优
│   ├── visualization/    # 可视化
│   ├── integration/      # 集成实践
│   ├── optimization/     # 性能优化
│   └── framework/        # 框架工具
├── docs/                 # 文档
├── examples/             # 示例
├── tests/                # 测试
└── notebooks/            # Jupyter笔记本
```

## 审核流程

所有PR都需要经过：
1. 代码审查
2. CI检查（测试、格式化）
3. 至少一位维护者批准

## 行为准则

- 尊重所有贡献者
- 欢迎不同观点
- 专注于项目改进
- 建设性反馈

## 获取帮助

- GitHub Issues: 技术问题
- GitHub Discussions: 一般讨论
- Email: your.email@example.com

---

再次感谢你的贡献！

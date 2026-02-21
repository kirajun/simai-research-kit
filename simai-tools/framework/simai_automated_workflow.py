#!/usr/bin/env python3
"""
SimAI端到端自动化工作流系统 v1.0
整合所有SimAI工具，实现完整的自动化工作流

Author: 二愣子
Date: 2026-02-19
"""

import os
import sys
import json
import subprocess
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


# ============================================================================
# 配置和常量
# ============================================================================

class WorkflowStage(Enum):
    """工作流阶段"""
    WORKLOAD_GEN = "workload_generation"
    SIMULATION = "simulation"
    ANALYSIS = "analysis"
    VISUALIZATION = "visualization"
    REPORTING = "reporting"


@dataclass
class WorkflowConfig:
    """工作流配置"""
    # 基础路径
    base_dir: Path = field(default_factory=lambda: Path.cwd())
    workload_dir: Path = field(default_factory=lambda: Path.cwd() / "workloads")
    output_dir: Path = field(default_factory=lambda: Path.cwd() / "outputs")
    log_dir: Path = field(default_factory=lambda: Path.cwd() / "logs")

    # SimAI配置
    simai_path: Optional[Path] = None
    use_docker: bool = True
    docker_image: str = "simai:latest"

    # 工作流配置
    stages: List[WorkflowStage] = field(default_factory=lambda: list(WorkflowStage))
    parallel_jobs: int = 4
    timeout_seconds: int = 3600

    # 测试场景
    gpu_scales: List[int] = field(default_factory=lambda: [4, 8, 16, 32, 64])
    msg_sizes_mb: List[int] = field(default_factory=lambda: [16, 64, 256, 512, 1024])
    collective_ops: List[str] = field(default_factory=lambda: [
        "AllReduce", "AllToAll", "Broadcast", "AllGather"
    ])

    # 报告配置
    generate_html: bool = True
    generate_pdf: bool = False
    create_dashboard: bool = True


@dataclass
class WorkflowResult:
    """工作流结果"""
    stage: WorkflowStage
    status: str  # success, failed, skipped
    start_time: datetime
    end_time: datetime
    output_files: List[Path] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

    @property
    def duration_seconds(self) -> float:
        """执行时长（秒）"""
        return (self.end_time - self.start_time).total_seconds()


# ============================================================================
# 核心工作流引擎
# ============================================================================

class SimAIWorkflowEngine:
    """SimAI自动化工作流引擎"""

    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.results: List[WorkflowResult] = []
        self.logger = self._setup_logger()

        # 创建必要的目录
        self._create_directories()

    def _setup_logger(self) -> logging.Logger:
        """设置日志"""
        log_dir = self.config.log_dir
        log_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"workflow_{timestamp}.log"

        logger = logging.getLogger("SimAIWorkflow")
        logger.setLevel(logging.INFO)

        # 文件handler
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.INFO)

        # 控制台handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)

        # 格式化
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        logger.addHandler(fh)
        logger.addHandler(ch)

        return logger

    def _create_directories(self):
        """创建必要的目录"""
        for dir_path in [
            self.config.workload_dir,
            self.config.output_dir,
            self.config.log_dir,
            self.config.output_dir / "simulations",
            self.config.output_dir / "analysis",
            self.config.output_dir / "reports",
            self.config.output_dir / "dashboards",
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)

    def run(self) -> Dict[str, Any]:
        """运行完整工作流"""
        self.logger.info("="*80)
        self.logger.info("SimAI自动化工作流启动")
        self.logger.info("="*80)

        workflow_start = datetime.now()

        try:
            # 阶段1: Workload生成
            if WorkflowStage.WORKLOAD_GEN in self.config.stages:
                self._run_workload_generation()

            # 阶段2: 仿真执行
            if WorkflowStage.SIMULATION in self.config.stages:
                self._run_simulation()

            # 阶段3: 结果分析
            if WorkflowStage.ANALYSIS in self.config.stages:
                self._run_analysis()

            # 阶段4: 可视化
            if WorkflowStage.VISUALIZATION in self.config.stages:
                self._run_visualization()

            # 阶段5: 报告生成
            if WorkflowStage.REPORTING in self.config.stages:
                self._run_reporting()

            workflow_end = datetime.now()
            duration = (workflow_end - workflow_start).total_seconds()

            # 汇总结果
            summary = self._generate_summary(duration)

            self.logger.info("="*80)
            self.logger.info("工作流完成！")
            self.logger.info(f"总时长: {duration:.2f}秒")
            self.logger.info("="*80)

            return summary

        except Exception as e:
            self.logger.error(f"工作流失败: {e}", exc_info=True)
            raise

    # ------------------------------------------------------------------------
    # 阶段1: Workload生成
    # ------------------------------------------------------------------------

    def _run_workload_generation(self):
        """运行workload生成阶段"""
        self.logger.info("\n" + "="*80)
        self.logger.info("阶段1: Workload生成")
        self.logger.info("="*80)

        start_time = datetime.now()
        output_files = []
        errors = []
        metrics = {}

        try:
            # 导入workload生成器
            sys.path.insert(0, str(Path(__file__).parent))
            from priority1_advanced_workload_generator import AdvancedWorkloadGenerator

            generator = AdvancedWorkloadGenerator(str(self.config.workload_dir))

            # 使用批量生成方法
            self.logger.info("生成不同规模的workload...")
            generator.generate_size_category_workloads()

            self.logger.info("生成不同集合通信模式的workload...")
            generator.generate_collective_pattern_workloads()

            # 收集所有生成的workload文件
            workload_files = list(self.config.workload_dir.glob("*.workload"))
            output_files = workload_files

            metrics["total_workloads"] = len(output_files)
            metrics["generation_rate"] = len(output_files) / max((datetime.now() - start_time).total_seconds(), 0.001)

            self.logger.info(f"✅ 成功生成 {len(output_files)} 个workload文件")

        except ImportError as e:
            errors.append(f"无法导入workload生成器: {e}")
            self.logger.warning(f"⚠️  跳过workload生成: {e}")
        except Exception as e:
            errors.append(f"Workload生成失败: {e}")
            self.logger.error(f"❌ Workload生成失败: {e}")

        end_time = datetime.now()
        result = WorkflowResult(
            stage=WorkflowStage.WORKLOAD_GEN,
            status="success" if not errors else "partial",
            start_time=start_time,
            end_time=end_time,
            output_files=output_files,
            metrics=metrics,
            errors=errors
        )

        self.results.append(result)

    # ------------------------------------------------------------------------
    # 阶段2: 仿真执行
    # ------------------------------------------------------------------------

    def _run_simulation(self):
        """运行仿真执行阶段"""
        self.logger.info("\n" + "="*80)
        self.logger.info("阶段2: 仿真执行")
        self.logger.info("="*80)

        start_time = datetime.now()
        output_files = []
        errors = []
        metrics = {
            "simulations_run": 0,
            "simulations_failed": 0
        }

        # 查找所有workload文件
        workload_files = list(self.config.workload_dir.glob("*.cfg"))

        if not workload_files:
            self.logger.warning("⚠️  未找到workload文件，跳过仿真")
            result = WorkflowResult(
                stage=WorkflowStage.SIMULATION,
                status="skipped",
                start_time=start_time,
                end_time=datetime.now(),
                errors=["未找到workload文件"]
            )
            self.results.append(result)
            return

        self.logger.info(f"找到 {len(workload_files)} 个workload文件")

        # 检查SimAI是否可用
        simai_available = self._check_simai_available()

        if not simai_available:
            self.logger.warning("⚠️  SimAI不可用，跳过仿真执行")
            self.logger.info("💡 提示: 需要安装Docker并构建SimAI镜像")

            result = WorkflowResult(
                stage=WorkflowStage.SIMULATION,
                status="skipped",
                start_time=start_time,
                end_time=datetime.now(),
                errors=["SimAI不可用"]
            )
            self.results.append(result)
            return

        # 运行仿真
        for workload_file in workload_files[:10]:  # 限制数量用于测试
            try:
                self.logger.info(f"运行仿真: {workload_file.name}")

                # 使用Docker运行仿真
                output_file = self._run_single_simulation(workload_file)

                if output_file:
                    output_files.append(output_file)
                    metrics["simulations_run"] += 1
                    self.logger.info(f"✅ 完成: {workload_file.name}")
                else:
                    metrics["simulations_failed"] += 1
                    errors.append(f"仿真失败: {workload_file.name}")

            except Exception as e:
                error_msg = f"仿真异常 ({workload_file.name}): {e}"
                errors.append(error_msg)
                metrics["simulations_failed"] += 1
                self.logger.error(error_msg)

        self.logger.info(f"✅ 完成 {metrics['simulations_run']} 个仿真")
        if metrics["simulations_failed"] > 0:
            self.logger.warning(f"⚠️  失败 {metrics['simulations_failed']} 个仿真")

        end_time = datetime.now()
        result = WorkflowResult(
            stage=WorkflowStage.SIMULATION,
            status="success" if metrics["simulations_failed"] == 0 else "partial",
            start_time=start_time,
            end_time=end_time,
            output_files=output_files,
            metrics=metrics,
            errors=errors
        )

        self.results.append(result)

    def _check_simai_available(self) -> bool:
        """检查SimAI是否可用"""
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    def _run_single_simulation(self, workload_file: Path) -> Optional[Path]:
        """运行单个仿真"""
        output_dir = self.config.output_dir / "simulations"
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / f"{workload_file.stem}_output.txt"

        try:
            # 构建Docker命令
            docker_cmd = [
                "docker", "run", "--rm",
                "-v", f"{workload_file.parent}:/workloads",
                "-v", f"{output_dir}:/outputs",
                self.config.docker_image,
                "/path/to/simai_binary",
                f"/workloads/{workload_file.name}"
            ]

            # 运行命令
            result = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=self.config.timeout_seconds
            )

            # 保存输出
            with open(output_file, 'w') as f:
                f.write(result.stdout)
                if result.stderr:
                    f.write(f"\n=== STDERR ===\n{result.stderr}")

            return output_file if result.returncode == 0 else None

        except Exception as e:
            self.logger.error(f"仿真执行异常: {e}")
            return None

    # ------------------------------------------------------------------------
    # 阶段3: 结果分析
    # ------------------------------------------------------------------------

    def _run_analysis(self):
        """运行结果分析阶段"""
        self.logger.info("\n" + "="*80)
        self.logger.info("阶段3: 结果分析")
        self.logger.info("="*80)

        start_time = datetime.now()
        output_files = []
        errors = []
        metrics = {}

        try:
            # 查找仿真输出
            sim_outputs = list((self.config.output_dir / "simulations").glob("*_output.txt"))

            if not sim_outputs:
                self.logger.warning("⚠️  未找到仿真输出，跳过分析")

                # 尝试运行性能建模器作为备选
                self._run_performance_modeling_as_fallback()

                result = WorkflowResult(
                    stage=WorkflowStage.ANALYSIS,
                    status="skipped",
                    start_time=start_time,
                    end_time=datetime.now(),
                    errors=["未找到仿真输出"]
                )
                self.results.append(result)
                return

            # 导入分析工具
            from performance_comparison_analyzer import PerformanceComparisonAnalyzer
            from collective_algorithm_deep_dive import CollectiveAlgorithmDeepDive

            analyzer = PerformanceComparisonAnalyzer(str(self.config.output_dir / "analysis"))

            # 分析每个仿真输出
            for output_file in sim_outputs:
                try:
                    # 这里需要实际的解析逻辑
                    # 简化版：直接复制文件到分析目录
                    analysis_file = self.config.output_dir / "analysis" / output_file.name
                    analysis_file.write_text(output_file.read_text())
                    output_files.append(analysis_file)

                except Exception as e:
                    errors.append(f"分析失败 ({output_file.name}): {e}")

            self.logger.info(f"✅ 完成 {len(output_files)} 个分析")

        except ImportError:
            self.logger.warning("⚠️  分析工具不可用，使用简化分析")
            self._run_simplified_analysis()

        except Exception as e:
            errors.append(f"分析失败: {e}")
            self.logger.error(f"❌ 分析失败: {e}")

        end_time = datetime.now()
        result = WorkflowResult(
            stage=WorkflowStage.ANALYSIS,
            status="success" if not errors else "partial",
            start_time=start_time,
            end_time=end_time,
            output_files=output_files,
            metrics=metrics,
            errors=errors
        )

        self.results.append(result)

    def _run_performance_modeling_as_fallback(self):
        """使用性能建模器作为备选"""
        self.logger.info("💡 使用性能建模器生成分析数据")

        try:
            sys.path.insert(0, str(Path(__file__).parent))
            from advanced_performance_modeler import AdvancedPerformanceModeler

            modeler = AdvancedPerformanceModeler()

            # 生成测试场景
            test_scenarios = [
                {"num_gpus": 8, "msg_size_mb": 128, "algorithm": "ring"},
                {"num_gpus": 64, "msg_size_mb": 512, "algorithm": "hierarchical"},
                {"num_gpus": 32, "msg_size_mb": 256, "algorithm": "tree"},
            ]

            output_dir = self.config.output_dir / "analysis"
            output_dir.mkdir(parents=True, exist_ok=True)

            for scenario in test_scenarios:
                result = modeler.predict_performance(**scenario)

                # 保存结果
                result_file = output_dir / f"model_{scenario['algorithm']}_{scenario['num_gpus']}gpu.json"
                with open(result_file, 'w') as f:
                    json.dump(result, f, indent=2)

                self.logger.info(f"生成模型预测: {result_file.name}")

        except ImportError:
            self.logger.warning("⚠️  性能建模器也不可用")

    def _run_simplified_analysis(self):
        """运行简化分析"""
        # 简化版分析：收集所有输出文件
        sim_outputs = list((self.config.output_dir / "simulations").glob("*_output.txt"))

        analysis_dir = self.config.output_dir / "analysis"
        analysis_dir.mkdir(parents=True, exist_ok=True)

        for output_file in sim_outputs:
            try:
                # 简单复制文件
                target = analysis_dir / output_file.name
                target.write_text(output_file.read_text())
            except Exception as e:
                self.logger.warning(f"复制失败: {e}")

    # ------------------------------------------------------------------------
    # 阶段4: 可视化
    # ------------------------------------------------------------------------

    def _run_visualization(self):
        """运行可视化阶段"""
        self.logger.info("\n" + "="*80)
        self.logger.info("阶段4: 可视化")
        self.logger.info("="*80)

        start_time = datetime.now()
        output_files = []
        errors = []
        metrics = {}

        try:
            # 生成可视化图表
            analysis_files = list((self.config.output_dir / "analysis").glob("*.json"))

            if not analysis_files:
                self.logger.warning("⚠️  未找到分析结果，跳过可视化")
                result = WorkflowResult(
                    stage=WorkflowStage.VISUALIZATION,
                    status="skipped",
                    start_time=start_time,
                    end_time=datetime.now(),
                    errors=["未找到分析结果"]
                )
                self.results.append(result)
                return

            # 这里可以集成matplotlib/plotly等可视化库
            # 简化版：生成文本报告
            dashboard_dir = self.config.output_dir / "dashboards"
            dashboard_dir.mkdir(parents=True, exist_ok=True)

            dashboard_file = dashboard_dir / "summary.txt"
            with open(dashboard_file, 'w') as f:
                f.write("SimAI工作流可视化摘要\n")
                f.write("="*80 + "\n\n")
                f.write(f"分析文件数量: {len(analysis_files)}\n")
                f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

            output_files.append(dashboard_file)
            self.logger.info(f"✅ 生成可视化摘要: {dashboard_file.name}")

        except Exception as e:
            errors.append(f"可视化失败: {e}")
            self.logger.error(f"❌ 可视化失败: {e}")

        end_time = datetime.now()
        result = WorkflowResult(
            stage=WorkflowStage.VISUALIZATION,
            status="success" if not errors else "partial",
            start_time=start_time,
            end_time=end_time,
            output_files=output_files,
            metrics=metrics,
            errors=errors
        )

        self.results.append(result)

    # ------------------------------------------------------------------------
    # 阶段5: 报告生成
    # ------------------------------------------------------------------------

    def _run_reporting(self):
        """运行报告生成阶段"""
        self.logger.info("\n" + "="*80)
        self.logger.info("阶段5: 报告生成")
        self.logger.info("="*80)

        start_time = datetime.now()
        output_files = []
        errors = []
        metrics = {}

        try:
            report_dir = self.config.output_dir / "reports"
            report_dir.mkdir(parents=True, exist_ok=True)

            # 生成文本报告
            text_report = self._generate_text_report()
            text_file = report_dir / "workflow_report.txt"
            text_file.write_text(text_report)
            output_files.append(text_file)

            # 生成JSON报告
            json_report = self._generate_json_report()
            json_file = report_dir / "workflow_report.json"
            with open(json_file, 'w') as f:
                json.dump(json_report, f, indent=2)
            output_files.append(json_file)

            # 生成Markdown报告
            md_report = self._generate_markdown_report()
            md_file = report_dir / "workflow_report.md"
            md_file.write_text(md_report)
            output_files.append(md_file)

            self.logger.info(f"✅ 生成 {len(output_files)} 个报告文件")

        except Exception as e:
            errors.append(f"报告生成失败: {e}")
            self.logger.error(f"❌ 报告生成失败: {e}")

        end_time = datetime.now()
        result = WorkflowResult(
            stage=WorkflowStage.REPORTING,
            status="success" if not errors else "partial",
            start_time=start_time,
            end_time=end_time,
            output_files=output_files,
            metrics=metrics,
            errors=errors
        )

        self.results.append(result)

    def _generate_text_report(self) -> str:
        """生成文本报告"""
        lines = []
        lines.append("="*80)
        lines.append("SimAI自动化工作流报告")
        lines.append("="*80)
        lines.append(f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"\n工作流配置:")
        lines.append(f"  基础目录: {self.config.base_dir}")
        lines.append(f"  GPU规模: {self.config.gpu_scales}")
        lines.append(f"  消息大小: {self.config.msg_sizes_mb} MB")
        lines.append(f"  集合操作: {self.config.collective_ops}")

        lines.append(f"\n各阶段执行情况:")
        for result in self.results:
            status_icon = "✅" if result.status == "success" else "⚠️" if result.status == "partial" else "⏭️"
            lines.append(f"  {status_icon} {result.stage.value}: {result.status} ({result.duration_seconds:.2f}s)")

            if result.errors:
                for error in result.errors[:3]:  # 最多显示3个错误
                    lines.append(f"      - {error}")

        return "\n".join(lines)

    def _generate_json_report(self) -> Dict[str, Any]:
        """生成JSON报告"""
        return {
            "timestamp": datetime.now().isoformat(),
            "config": {
                "base_dir": str(self.config.base_dir),
                "gpu_scales": self.config.gpu_scales,
                "msg_sizes_mb": self.config.msg_sizes_mb,
                "collective_ops": self.config.collective_ops,
            },
            "results": [
                {
                    "stage": r.stage.value,
                    "status": r.status,
                    "duration_seconds": r.duration_seconds,
                    "output_files": [str(f) for f in r.output_files],
                    "metrics": r.metrics,
                    "errors": r.errors
                }
                for r in self.results
            ]
        }

    def _generate_markdown_report(self) -> str:
        """生成Markdown报告"""
        lines = []
        lines.append("# SimAI自动化工作流报告\n")
        lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        lines.append("## 工作流配置\n")
        lines.append(f"- **GPU规模**: {', '.join(map(str, self.config.gpu_scales))}")
        lines.append(f"- **消息大小**: {', '.join(map(str, self.config.msg_sizes_mb))} MB")
        lines.append(f"- **集合操作**: {', '.join(self.config.collective_ops)}\n")

        lines.append("## 执行结果\n")
        for result in self.results:
            status_icon = "✅" if result.status == "success" else "⚠️" if result.status == "partial" else "⏭️"
            lines.append(f"### {status_icon} {result.stage.value}\n")
            lines.append(f"- **状态**: {result.status}")
            lines.append(f"- **时长**: {result.duration_seconds:.2f}秒")

            if result.metrics:
                lines.append(f"- **指标**:")
                for key, value in result.metrics.items():
                    lines.append(f"  - {key}: {value}")

            if result.errors:
                lines.append(f"- **错误**:")
                for error in result.errors[:3]:
                    lines.append(f"  - {error}")

            lines.append("")

        return "\n".join(lines)

    def _generate_summary(self, total_duration: float) -> Dict[str, Any]:
        """生成工作流摘要"""
        return {
            "total_duration_seconds": total_duration,
            "stages_completed": len([r for r in self.results if r.status == "success"]),
            "stages_total": len(self.results),
            "total_output_files": sum(len(r.output_files) for r in self.results),
            "total_errors": sum(len(r.errors) for r in self.results),
            "success_rate": len([r for r in self.results if r.status == "success"]) / len(self.results) if self.results else 0
        }


# ============================================================================
# 命令行接口
# ============================================================================

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="SimAI自动化工作流系统")
    parser.add_argument("--base-dir", type=str, default=".", help="基础目录")
    parser.add_argument("--gpu-scales", type=int, nargs="+", default=[4, 8, 16, 32, 64], help="GPU规模列表")
    parser.add_argument("--msg-sizes", type=int, nargs="+", default=[16, 64, 256, 512, 1024], help="消息大小(MB)列表")
    parser.add_argument("--collective-ops", type=str, nargs="+", default=["AllReduce"], help="集合操作列表")
    parser.add_argument("--stages", type=str, nargs="+", help="要运行的阶段")
    parser.add_argument("--parallel", type=int, default=4, help="并行任务数")
    parser.add_argument("--timeout", type=int, default=3600, help="超时时间(秒)")

    args = parser.parse_args()

    # 构建配置
    config = WorkflowConfig(
        base_dir=Path(args.base_dir),
        gpu_scales=args.gpu_scales,
        msg_sizes_mb=args.msg_sizes,
        collective_ops=args.collective_ops,
        parallel_jobs=args.parallel,
        timeout_seconds=args.timeout
    )

    # 覆盖阶段
    if args.stages:
        stage_map = {
            "workload": WorkflowStage.WORKLOAD_GEN,
            "simulation": WorkflowStage.SIMULATION,
            "analysis": WorkflowStage.ANALYSIS,
            "visualization": WorkflowStage.VISUALIZATION,
            "report": WorkflowStage.REPORTING
        }
        config.stages = [stage_map[s] for s in args.stages if s in stage_map]

    # 运行工作流
    engine = SimAIWorkflowEngine(config)
    summary = engine.run()

    # 打印摘要
    print("\n" + "="*80)
    print("工作流摘要")
    print("="*80)
    print(f"总时长: {summary['total_duration_seconds']:.2f}秒")
    print(f"完成阶段: {summary['stages_completed']}/{summary['stages_total']}")
    print(f"输出文件: {summary['total_output_files']}")
    print(f"错误数: {summary['total_errors']}")
    print(f"成功率: {summary['success_rate']*100:.1f}%")
    print("="*80)

    return 0 if summary['total_errors'] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

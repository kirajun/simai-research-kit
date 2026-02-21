#!/usr/bin/env python3
"""
SimAI Results Analyzer
分析SimAI测试结果，生成性能对比报告
"""

import os
import sys
import csv
import json
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime


class SimAIResultAnalyzer:
    """SimAI结果分析器"""

    def __init__(self, results_dir: str):
        self.results_dir = Path(results_dir)
        self.results = {}

    def parse_endtoend_csv(self, csv_path: Path) -> Dict:
        """解析EndToEnd.csv文件 - 支持多种CSV格式"""
        result = {
            'name': csv_path.stem,
            'total_time': 0,
            'total_comm': 0,
            'layers': [],
            'algbw': 0.0,
            'busbw': 0.0
        }

        try:
            with open(csv_path, 'r') as f:
                lines = f.readlines()

            # 解析第一行（摘要行）
            if len(lines) > 0:
                first_line_parts = lines[0].strip().split(',')
                if len(first_line_parts) >= 10:
                    # 总时间在最后一列
                    try:
                        result['total_time'] = int(first_line_parts[-1].strip())
                    except:
                        pass

                    # 通信时间在倒数第三列
                    try:
                        result['total_comm'] = int(first_line_parts[-3].strip())
                    except:
                        pass

            # 解析layer行（从第3行开始）
            if len(lines) >= 3:
                header = lines[1].strip().split(',')
                for line in lines[2:]:
                    parts = line.strip().split(',')
                    if len(parts) < 3:
                        continue

                    layer_name = parts[0].strip()

                    # 跳过非layer行
                    if not layer_name or layer_name == 'layer_name':
                        continue

                    # 解析通信时间（fwd exposed comm在不同位置）
                    fwd_comm_idx = None
                    for idx, col in enumerate(header):
                        if 'fwd exposed comm' in col:
                            fwd_comm_idx = idx
                            break

                    fwd_comm = 0
                    if fwd_comm_idx and fwd_comm_idx < len(parts):
                        try:
                            fwd_comm = int(parts[fwd_comm_idx].strip())
                        except:
                            pass

                    # 解析算法带宽（algbw）
                    algbw_idx = None
                    for idx, col in enumerate(header):
                        if 'algbw' in col and 'fwd' in header[idx-1] if idx > 0 else False:
                            algbw_idx = idx
                            break

                    algbw = 0.0
                    if algbw_idx and algbw_idx < len(parts):
                        try:
                            algbw = float(parts[algbw_idx].strip())
                        except:
                            pass

                    layer_info = {
                        'name': layer_name,
                        'fwd_comm': fwd_comm,
                        'algbw': algbw
                    }
                    result['layers'].append(layer_info)

                    # 记录第一个层的带宽作为总体带宽
                    if result['algbw'] == 0.0 and algbw > 0:
                        result['algbw'] = algbw

        except Exception as e:
            print(f"解析错误 {csv_path}: {e}")
            import traceback
            traceback.print_exc()

        return result

    def analyze_all_results(self):
        """分析所有结果文件"""
        csv_files = list(self.results_dir.rglob("*EndToEnd.csv"))
        print(f"找到 {len(csv_files)} 个结果文件")

        for csv_file in csv_files:
            result = self.parse_endtoend_csv(csv_file)
            self.results[result['name']] = result

    def compare_gpu_scaling(self) -> Dict:
        """对比GPU扩展性"""
        gpu_results = {}

        for name, result in self.results.items():
            if 'gpu_' in name or name.startswith('gpu_'):
                # 提取GPU数量
                gpu_count = None
                if '_gpu_' in name:
                    parts = name.split('_gpu_')
                    if len(parts) > 1:
                        gpu_count_str = parts[1].split('_')[0]
                        try:
                            gpu_count = int(gpu_count_str)
                        except:
                            pass
                elif name.startswith('gpu_'):
                    parts = name.split('_')
                    if len(parts) > 1:
                        try:
                            gpu_count = int(parts[1])
                        except:
                            pass

                if gpu_count:
                    if gpu_count not in gpu_results:
                        gpu_results[gpu_count] = []
                    gpu_results[gpu_count].append(result)

        return gpu_results

    def calculate_speedup(self, baseline_time: float, current_time: float) -> float:
        """计算加速比"""
        if current_time == 0:
            return 0.0
        return baseline_time / current_time

    def calculate_efficiency(self, speedup: float, gpu_ratio: float) -> float:
        """计算并行效率"""
        if gpu_ratio == 0:
            return 0.0
        return (speedup / gpu_ratio) * 100

    def generate_markdown_report(self, output_path: str = None):
        """生成Markdown报告"""
        if not output_path:
            output_path = self.results_dir / f"analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

        report_lines = []
        report_lines.append("# SimAI 性能分析报告\n")
        report_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        report_lines.append(f"结果目录: {self.results_dir}\n")
        report_lines.append(f"测试数量: {len(self.results)}\n")
        report_lines.append("\n---\n\n")

        # GPU扩展性分析
        report_lines.append("## GPU扩展性分析\n\n")
        gpu_results = self.compare_gpu_scaling()

        if gpu_results:
            # 按GPU数量排序
            sorted_gpus = sorted(gpu_results.keys())

            report_lines.append("### 测试配置\n\n")
            report_lines.append("| GPU数量 | 测试名称 | 总时间 | 通信时间 | 算法带宽 |\n")
            report_lines.append("|---------|----------|--------|----------|----------|\n")

            for gpu_count in sorted_gpus:
                for result in gpu_results[gpu_count]:
                    algbw = result['layers'][0]['algbw'] if result['layers'] else 0.0
                    report_lines.append(
                        f"| {gpu_count} | {result['name'][:30]} | "
                        f"{result['total_time']} | {result['total_comm']} | "
                        f"{algbw:.2f} GB/s |\n"
                    )

            report_lines.append("\n### 扩展性分析\n\n")

            if len(sorted_gpus) >= 2:
                baseline_gpu = sorted_gpus[0]
                baseline_time = gpu_results[baseline_gpu][0]['total_time']

                report_lines.append("| GPU数量 | 总时间 | 加速比 | 并行效率 |\n")
                report_lines.append("|---------|--------|--------|----------|\n")

                for gpu_count in sorted_gpus:
                    if gpu_results[gpu_count]:
                        avg_time = sum(r['total_time'] for r in gpu_results[gpu_count]) / len(gpu_results[gpu_count])
                        speedup = self.calculate_speedup(baseline_time, avg_time)
                        efficiency = self.calculate_efficiency(speedup, gpu_count / baseline_gpu)

                        report_lines.append(
                            f"| {gpu_count} | {avg_time:.2f} | {speedup:.2f}x | {efficiency:.1f}% |\n"
                        )

        # 通信模式分析
        report_lines.append("\n## 通信模式分析\n\n")
        report_lines.append("### 测试详情\n\n")

        for name, result in sorted(self.results.items()):
            if result['layers']:
                report_lines.append(f"#### {name}\n\n")
                report_lines.append("| Layer | 通信时间 | 算法带宽 |\n")
                report_lines.append("|-------|----------|----------|\n")

                for layer in result['layers']:
                    report_lines.append(
                        f"| {layer['name']} | {layer['fwd_comm']} | {layer['algbw']:.2f} GB/s |\n"
                    )

                report_lines.append(f"\n**总结**: 总时间 {result['total_time']}, 通信时间 {result['total_comm']}\n\n")

        # 保存报告
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.writelines(report_lines)

        print(f"报告已生成: {output_path}")

        # 同时生成JSON数据
        json_path = output_path.with_suffix('.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        print(f"JSON数据已生成: {json_path}")

        return output_path


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python simai_results_analyzer.py <results_dir>")
        sys.exit(1)

    results_dir = sys.argv[1]
    analyzer = SimAIResultAnalyzer(results_dir)

    print("正在分析结果...")
    analyzer.analyze_all_results()

    print("正在生成报告...")
    report_path = analyzer.generate_markdown_report()

    print(f"\n分析完成!")
    print(f"报告: {report_path}")


if __name__ == "__main__":
    main()

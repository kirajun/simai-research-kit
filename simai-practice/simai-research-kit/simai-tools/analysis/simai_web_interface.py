#!/usr/bin/env python3
"""
SimAI Web界面 - MVP版本
========================

功能：
1. SimAI性能预测（基于Ratio表模型）
2. 算法推荐（智能选择最优算法）
3. 参数配置（GPU、数据大小、带宽等）
4. 结果展示（性能预测、算法对比）

技术栈：
- Flask (轻量级Web框架)
- Jinja2 (模板引擎)
- Bootstrap (响应式UI)
- Chart.js (数据可视化)

作者：二愣子 🤔
日期：2026-02-19
"""

from flask import Flask, render_template, request, jsonify
import json
import math
from dataclasses import dataclass
from typing import List, Dict, Optional


app = Flask(__name__)


@dataclass
class AlgorithmResult:
    """算法结果"""
    name: str
    time_ms: float
    steps: int
    speedup: float
    description: str


class SimAIPredictor:
    """SimAI性能预测器"""
    
    def __init__(self):
        # 算法配置
        self.algorithms = {
            'Ring': {
                'steps': lambda n: 2 * (n - 1),
                'data_per_step': 1.0 / n,
                'description': '环形算法，适合≤8 GPU'
            },
            'Tree': {
                'steps': lambda n: 2 * math.log2(n),
                'data_per_step': 0.5,
                'description': '树形算法，适合8-32 GPU'
            },
            'DBT': {
                'steps': lambda n: 2 * math.log2(n),
                'data_per_step': 0.25,
                'concurrency': 2.0,
                'description': '双路二叉树，适合2-12 GPU'
            },
            'RecursiveDoubling': {
                'steps': lambda n: math.log2(n),
                'data_per_step': 0.5,
                'description': '递归加倍，AllReduce专用'
            },
        }
        
        # Ratio表效率（简化版）
        self.nvlink_efficiency = {
            1: 0.80,
            2: 0.60,
            4: 0.45,
            8: 0.30,
        }
    
    def predict_performance(
        self,
        num_gpus: int,
        data_size_mb: float,
        bandwidth_gbps: float = 300.0,
        latency_us: float = 10.0,
        num_nodes: int = 1
    ) -> List[AlgorithmResult]:
        """预测所有算法的性能"""
        results = []
        
        for algo_name, algo_config in self.algorithms.items():
            try:
                # 计算步数
                steps = int(algo_config['steps'](num_gpus))
                
                # 计算每步数据量
                total_data_bytes = data_size_mb * 1024 * 1024
                data_per_step_bytes = total_data_bytes * algo_config['data_per_step']
                
                # 获取效率
                node_idx = min(num_nodes, sorted(self.nvlink_efficiency.keys())[-1])
                efficiency = self.nvlink_efficiency[node_idx]
                
                # 应用并发度
                concurrency = algo_config.get('concurrency', 1.0)
                effective_bandwidth = bandwidth_gbps * 1e9 * efficiency * concurrency
                
                # 计算时间
                bandwidth_time = data_per_step_bytes / effective_bandwidth
                latency_time = latency_us * 1e-6
                total_time = steps * (bandwidth_time + latency_time)
                
                results.append(AlgorithmResult(
                    name=algo_name,
                    time_ms=total_time * 1000,
                    steps=steps,
                    speedup=0.0,  # 稍后计算
                    description=algo_config['description']
                ))
            except Exception as e:
                print(f"Error calculating {algo_name}: {e}")
        
        # 按时间排序
        results.sort(key=lambda x: x.time_ms)
        
        # 计算加速比
        if results:
            fastest_time = results[0].time_ms
            for r in results:
                r.speedup = fastest_time / r.time_ms
        
        return results
    
    def recommend_algorithm(
        self,
        num_gpus: int,
        data_size_mb: float,
        num_nodes: int = 1
    ) -> Dict:
        """推荐最优算法"""
        results = self.predict_performance(num_gpus, data_size_mb, num_nodes=num_nodes)
        
        if not results:
            return {'error': 'No valid results'}
        
        optimal = results[0]
        
        # 场景分析
        scenario = []
        if num_gpus <= 8:
            scenario.append("小规模")
        elif num_gpus <= 32:
            scenario.append("中等规模")
        else:
            scenario.append("大规模")
        
        if num_nodes == 1:
            scenario.append("单节点")
        else:
            scenario.append(f"{num_nodes}节点")
        
        return {
            'optimal_algorithm': optimal.name,
            'predicted_time_ms': round(optimal.time_ms, 2),
            'steps': optimal.steps,
            'description': optimal.description,
            'scenario': ' '.join(scenario),
            'speedup_vs_second': round(results[0].time_ms / results[1].time_ms, 2) if len(results) > 1 else 1.0,
            'all_results': [
                {
                    'name': r.name,
                    'time_ms': round(r.time_ms, 2),
                    'steps': r.steps,
                    'speedup': round(r.speedup, 3),
                    'description': r.description
                }
                for r in results
            ]
        }


# 创建预测器实例
predictor = SimAIPredictor()


@app.route('/')
def index():
    """主页"""
    return render_template('index.html')


@app.route('/api/predict', methods=['POST'])
def api_predict():
    """性能预测API"""
    try:
        data = request.json
        
        # 提取参数
        num_gpus = int(data.get('num_gpus', 8))
        data_size_mb = float(data.get('data_size_mb', 64))
        bandwidth_gbps = float(data.get('bandwidth_gbps', 300.0))
        latency_us = float(data.get('latency_us', 10.0))
        num_nodes = int(data.get('num_nodes', 1))
        
        # 验证参数
        if num_gpus < 1 or num_gpus > 1024:
            return jsonify({'error': 'GPU数量必须在1-1024之间'}), 400
        
        if data_size_mb < 1 or data_size_mb > 10240:
            return jsonify({'error': '数据大小必须在1-10240 MB之间'}), 400
        
        # 预测性能
        result = predictor.recommend_algorithm(
            num_gpus, data_size_mb, num_nodes
        )
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/compare', methods=['POST'])
def api_compare():
    """算法对比API"""
    try:
        data = request.json
        
        # 提取参数
        configs = data.get('configs', [])
        
        if not configs:
            return jsonify({'error': '缺少配置'}), 400
        
        # 对比所有配置
        comparison = []
        for config in configs:
            result = predictor.recommend_algorithm(
                config.get('num_gpus', 8),
                config.get('data_size_mb', 64),
                config.get('num_nodes', 1)
            )
            comparison.append({
                'config': config,
                'result': result
            })
        
        return jsonify({'comparison': comparison})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def create_html_template():
    """创建HTML模板"""
    html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SimAI Web界面 - 性能预测与算法推荐</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        h1 {
            color: #667eea;
            font-weight: bold;
        }
        .result-card {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            margin-top: 20px;
            border-left: 4px solid #667eea;
        }
        .algorithm-table {
            margin-top: 20px;
        }
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
        }
        .btn-primary:hover {
            background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
        }
        .optimal-badge {
            background: #28a745;
            color: white;
            padding: 5px 10px;
            border-radius: 5px;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="text-center mb-4">🚀 SimAI Web界面</h1>
        <p class="text-center text-muted">AI训练网络性能预测与算法推荐</p>
        
        <div class="row">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5 class="mb-0">📊 参数配置</h5>
                    </div>
                    <div class="card-body">
                        <form id="predictForm">
                            <div class="mb-3">
                                <label class="form-label">GPU数量</label>
                                <input type="number" class="form-control" id="num_gpus" value="8" min="1" max="1024">
                            </div>
                            <div class="mb-3">
                                <label class="form-label">数据大小 (MB)</label>
                                <input type="number" class="form-control" id="data_size_mb" value="64" min="1" max="10240">
                            </div>
                            <div class="mb-3">
                                <label class="form-label">带宽 (GB/s)</label>
                                <input type="number" class="form-control" id="bandwidth_gbps" value="300" min="1" max="1000">
                            </div>
                            <div class="mb-3">
                                <label class="form-label">延迟 (微秒)</label>
                                <input type="number" class="form-control" id="latency_us" value="10" min="1" max="1000">
                            </div>
                            <div class="mb-3">
                                <label class="form-label">节点数</label>
                                <input type="number" class="form-control" id="num_nodes" value="1" min="1" max="128">
                            </div>
                            <button type="submit" class="btn btn-primary w-100">预测性能</button>
                        </form>
                    </div>
                </div>
            </div>
            
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5 class="mb-0">🎯 预测结果</h5>
                    </div>
                    <div class="card-body" id="results">
                        <p class="text-muted text-center">请配置参数并点击"预测性能"</p>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row mt-4">
            <div class="col-md-12">
                <div class="card">
                    <div class="card-header">
                        <h5 class="mb-0">📈 性能对比图表</h5>
                    </div>
                    <div class="card-body">
                        <canvas id="performanceChart"></canvas>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        let performanceChart = null;
        
        document.getElementById('predictForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const data = {
                num_gpus: parseInt(document.getElementById('num_gpus').value),
                data_size_mb: parseFloat(document.getElementById('data_size_mb').value),
                bandwidth_gbps: parseFloat(document.getElementById('bandwidth_gbps').value),
                latency_us: parseFloat(document.getElementById('latency_us').value),
                num_nodes: parseInt(document.getElementById('num_nodes').value)
            };
            
            try {
                const response = await fetch('/api/predict', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (result.error) {
                    document.getElementById('results').innerHTML = `
                        <div class="alert alert-danger">${result.error}</div>
                    `;
                    return;
                }
                
                // 显示结果
                let html = `
                    <div class="result-card">
                        <h6>推荐算法</h6>
                        <h3>${result.optimal_algorithm} <span class="optimal-badge">最优</span></h3>
                        <p class="mb-1"><strong>预计时间:</strong> ${result.predicted_time_ms} ms</p>
                        <p class="mb-1"><strong>通信步数:</strong> ${result.steps}</p>
                        <p class="mb-1"><strong>场景:</strong> ${result.scenario}</p>
                        <p class="mb-0"><strong>加速比:</strong> ${result.speedup_vs_second}x (vs 第二)</p>
                        <hr>
                        <small class="text-muted">${result.description}</small>
                    </div>
                    
                    <h6 class="mt-3">所有算法对比</h6>
                    <table class="table table-sm algorithm-table">
                        <thead>
                            <tr>
                                <th>排名</th>
                                <th>算法</th>
                                <th>时间 (ms)</th>
                                <th>步数</th>
                                <th>加速比</th>
                            </tr>
                        </thead>
                        <tbody>
                `;
                
                result.all_results.forEach((r, i) => {
                    html += `
                        <tr>
                            <td>${i + 1}</td>
                            <td>${r.name}</td>
                            <td>${r.time_ms}</td>
                            <td>${r.steps}</td>
                            <td>${r.speedup}x</td>
                        </tr>
                    `;
                });
                
                html += '</tbody></table>';
                document.getElementById('results').innerHTML = html;
                
                // 更新图表
                updateChart(result.all_results);
                
            } catch (error) {
                document.getElementById('results').innerHTML = `
                    <div class="alert alert-danger">错误: ${error.message}</div>
                `;
            }
        });
        
        function updateChart(results) {
            const ctx = document.getElementById('performanceChart').getContext('2d');
            
            if (performanceChart) {
                performanceChart.destroy();
            }
            
            performanceChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: results.map(r => r.name),
                    datasets: [{
                        label: '通信时间 (ms)',
                        data: results.map(r => r.time_ms),
                        backgroundColor: [
                            'rgba(40, 167, 69, 0.8)',
                            'rgba(102, 126, 234, 0.8)',
                            'rgba(255, 193, 7, 0.8)',
                            'rgba(220, 53, 69, 0.8)'
                        ],
                        borderColor: [
                            'rgba(40, 167, 69, 1)',
                            'rgba(102, 126, 234, 1)',
                            'rgba(255, 193, 7, 1)',
                            'rgba(220, 53, 69, 1)'
                        ],
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        title: {
                            display: true,
                            text: '算法性能对比'
                        },
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: '时间 (ms)'
                            }
                        }
                    }
                }
            });
        }
    </script>
</body>
</html>'''
    
    # 创建templates目录
    import os
    os.makedirs('/Users/erlengzi/.openclaw/workspace/simai-practice/templates', exist_ok=True)
    
    # 保存模板
    with open('/Users/erlengzi/.openclaw/workspace/simai-practice/templates/index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    print("✅ HTML模板已创建")


def main():
    """主函数"""
    print("=" * 70)
    print("SimAI Web界面 - MVP版本")
    print("=" * 70)
    
    # 创建HTML模板
    create_html_template()
    
    print("\n🚀 启动Web服务器...")
    print("📊 访问地址: http://localhost:5000")
    print("⚠️  按 Ctrl+C 停止服务器")
    print("=" * 70)
    
    # 启动Flask服务器
    app.run(host='0.0.0.0', port=5000, debug=False)


if __name__ == '__main__':
    main()

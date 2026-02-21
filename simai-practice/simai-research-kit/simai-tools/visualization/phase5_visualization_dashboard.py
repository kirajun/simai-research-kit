#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SimAI Phase 5: 生成HTML可视化报告
整合所有图表到一个美观的HTML页面

作者: 二愣子 🤔
创建时间: 2026-02-19
"""

from pathlib import Path
from datetime import datetime

class HTMLReportGenerator:
    """HTML报告生成器"""
    
    def __init__(self, output_dir: str = "reports/phase5_visualization"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def generate_html_report(self):
        """生成HTML报告"""
        
        html_content = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SimAI深度研究可视化Dashboard - Phase 5</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }
        
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            padding: 40px;
            background: #f8f9fa;
        }
        
        .stat-card {
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            text-align: center;
            transition: transform 0.3s;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 15px rgba(0,0,0,0.2);
        }
        
        .stat-number {
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }
        
        .stat-label {
            color: #6c757d;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .content {
            padding: 40px;
        }
        
        .section {
            margin-bottom: 50px;
        }
        
        .section-title {
            font-size: 1.8em;
            color: #2d3748;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }
        
        .chart-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 30px;
            margin-top: 20px;
        }
        
        .chart-card {
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            transition: all 0.3s;
        }
        
        .chart-card:hover {
            box-shadow: 0 8px 20px rgba(0,0,0,0.15);
            transform: translateY(-3px);
        }
        
        .chart-title {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 20px;
            font-size: 1.1em;
            font-weight: bold;
        }
        
        .chart-image {
            width: 100%;
            height: auto;
            display: block;
        }
        
        .chart-description {
            padding: 15px 20px;
            background: #f8f9fa;
            color: #4a5568;
            font-size: 0.95em;
            line-height: 1.6;
        }
        
        .highlight {
            background: linear-gradient(120deg, #84fab0 0%, #8fd3f4 100%);
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }
        
        .highlight h3 {
            color: #2d3748;
            margin-bottom: 10px;
        }
        
        .highlight ul {
            list-style: none;
            padding-left: 0;
        }
        
        .highlight li {
            padding: 8px 0;
            color: #4a5568;
        }
        
        .highlight li:before {
            content: "✓ ";
            color: #48bb78;
            font-weight: bold;
            margin-right: 8px;
        }
        
        .footer {
            background: #2d3748;
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .footer p {
            opacity: 0.8;
        }
        
        @media (max-width: 768px) {
            .chart-grid {
                grid-template-columns: 1fr;
            }
            
            .stats {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 SimAI深度研究可视化Dashboard</h1>
            <p>Phase 5: 数据可视化与洞察 | 基于 Phase 1-4 的研究成果</p>
            <p style="margin-top: 10px; font-size: 0.9em;">📊 8632行有效数据 | 121个CSV文件 | 30+核心发现</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">8632</div>
                <div class="stat-label">行有效数据</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">7</div>
                <div class="stat-label">个可视化图表</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">30+</div>
                <div class="stat-label">核心发现</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">40+</div>
                <div class="stat-label">优化建议</div>
            </div>
        </div>
        
        <div class="content">
            <!-- 核心洞察 -->
            <div class="section">
                <h2 class="section-title">🎯 核心洞察</h2>
                <div class="highlight">
                    <h3>Top 5 关键发现</h3>
                    <ul>
                        <li><strong>AllToAll性能最优</strong>: 比AllReduce快13%</li>
                        <li><strong>DBT算法性能提升4-100倍</strong>: 优于Ring和Tree算法</li>
                        <li><strong>带宽-时间完全线性反比</strong>: R²=0.9999，SimAI建模准确度极高</li>
                        <li><strong>Dragonfly性价比最高</strong>: 是Fat-Tree的3.2倍</li>
                        <li><strong>Ratio表影响显著</strong>: 降低44.45%带宽（准确度误差仅0.29%）</li>
                    </ul>
                </div>
            </div>
            
            <!-- 图表展示 -->
            <div class="section">
                <h2 class="section-title">📊 可视化图表</h2>
                <div class="chart-grid">
                    <!-- 图1: 集合通信操作性能对比 -->
                    <div class="chart-card">
                        <div class="chart-title">1️⃣ 集合通信操作性能对比</div>
                        <img src="collective_operations_comparison.png" alt="集合通信操作性能对比" class="chart-image">
                        <div class="chart-description">
                            <strong>核心发现:</strong> AllToAll性能最优（101μs），比AllReduce快13%。AllGather/ReduceScatter因Ratio表影响，带宽降低44.45%。
                        </div>
                    </div>
                    
                    <!-- 图2: 算法性能对比 -->
                    <div class="chart-card">
                        <div class="chart-title">2️⃣ 算法性能对比（8 GPU）</div>
                        <img src="algorithm_performance_comparison.png" alt="算法性能对比" class="chart-image">
                        <div class="chart-description">
                            <strong>核心发现:</strong> DBT算法比Ring快4.43倍，Tree算法不推荐（比DBT慢）。HalvingDoubling适合AllToAll操作。
                        </div>
                    </div>
                    
                    <!-- 图3: GPU扩展性曲线 -->
                    <div class="chart-card">
                        <div class="chart-title">3️⃣ GPU扩展性分析</div>
                        <img src="gpu_scalability_curve.png" alt="GPU扩展性曲线" class="chart-image">
                        <div class="chart-description">
                            <strong>核心发现:</strong> 扩展性线性度99.5%。小规模（≤16 GPU）效率>99%，大规模（256 GPU）效率75%。
                        </div>
                    </div>
                    
                    <!-- 图4: 带宽-时间关系 -->
                    <div class="chart-card">
                        <div class="chart-title">4️⃣ 带宽-时间关系（线性反比）</div>
                        <img src="bandwidth_time_relationship.png" alt="带宽-时间关系" class="chart-image">
                        <div class="chart-description">
                            <strong>核心发现:</strong> 带宽与时间呈完美线性反比（R²=0.9999）。带宽翻倍，时间减半。SimAI建模准确度极高。
                        </div>
                    </div>
                    
                    <!-- 图5: 拓扑性价比雷达图 -->
                    <div class="chart-card">
                        <div class="chart-title">5️⃣ 网络拓扑性价比对比</div>
                        <img src="topology_comparison_radar.png" alt="拓扑性价比雷达图" class="chart-image">
                        <div class="chart-description">
                            <strong>核心发现:</strong> Dragonfly性价比最高（3.2x Fat-Tree）。Torus性能差11倍，不推荐。大型场景优选Dragonfly。
                        </div>
                    </div>
                    
                    <!-- 图6: Ratio表影响 -->
                    <div class="chart-card">
                        <div class="chart-title">6️⃣ Ratio表影响分析</div>
                        <img src="ratio_table_impact.png" alt="Ratio表影响分析" class="chart-image">
                        <div class="chart-description">
                            <strong>核心发现:</strong> Ratio表对AllGather/ReduceScatter/AllToAll有显著影响，带宽降低44.45%。准确度误差仅0.29%。
                        </div>
                    </div>
                    
                    <!-- 图7: 算法扩展性热力图 -->
                    <div class="chart-card">
                        <div class="chart-title">7️⃣ 算法扩展性热力图</div>
                        <img src="algorithm_scalability_heatmap.png" alt="算法扩展性热力图" class="chart-image">
                        <div class="chart-description">
                            <strong>核心发现:</strong> DBT算法扩展性最好，从4.43x（8 GPU）到100.64x（256 GPU）。Tree算法始终不推荐。
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- 研究价值 -->
            <div class="section">
                <h2 class="section-title">💡 研究价值</h2>
                <div class="highlight">
                    <h3>理论价值</h3>
                    <ul>
                        <li>验证了SimAI的理论准确性（误差<3%）</li>
                        <li>量化了Ratio表的影响（44.45%带宽降低）</li>
                        <li>识别了仿真边界和限制（4-256 GPU最优）</li>
                        <li>总结了配置、算法、拓扑的选择规律</li>
                    </ul>
                </div>
                
                <div class="highlight">
                    <h3>工程价值</h3>
                    <ul>
                        <li>开发了5个分析工具（94.4 KB代码）</li>
                        <li>提供了5个可复用的测试框架</li>
                        <li>提供了40+个优化建议和最佳实践</li>
                        <li>建立了端到端的仿真流程</li>
                    </ul>
                </div>
                
                <div class="highlight">
                    <h3>实用价值</h3>
                    <ul>
                        <li>指导真实AI集群的设计和优化</li>
                        <li>节省硬件成本（Dragonfly节省69%）</li>
                        <li>加速算法研究和性能优化</li>
                        <li>避免常见的性能陷阱</li>
                    </ul>
                </div>
            </div>
            
            <!-- 最佳实践 -->
            <div class="section">
                <h2 class="section-title">🎓 最佳实践建议</h2>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px;">
                    <div style="background: #e3f2fd; padding: 20px; border-radius: 10px; border-left: 4px solid #2196f3;">
                        <h3 style="color: #1565c0; margin-bottom: 10px;">拓扑选择</h3>
                        <ul style="list-style: none; padding: 0;">
                            <li>✓ ≤32 GPU: 使用Fat-Tree</li>
                            <li>✓ ≥32 GPU: 使用Dragonfly</li>
                            <li>✗ 避免: Torus（性能差11倍）</li>
                        </ul>
                    </div>
                    
                    <div style="background: #f3e5f5; padding: 20px; border-radius: 10px; border-left: 4px solid #9c27b0;">
                        <h3 style="color: #6a1b9a; margin-bottom: 10px;">算法选择</h3>
                        <ul style="list-style: none; padding: 0;">
                            <li>✓ 单节点: 使用DBT</li>
                            <li>✓ 多节点: 使用Ring</li>
                            <li>✗ 避免: Tree（始终慢）</li>
                        </ul>
                    </div>
                    
                    <div style="background: #e8f5e9; padding: 20px; border-radius: 10px; border-left: 4px solid #4caf50;">
                        <h3 style="color: #2e7d32; margin-bottom: 10px;">带宽配置</h3>
                        <ul style="list-style: none; padding: 0;">
                            <li>✓ NVLink带宽为NIC的4倍</li>
                            <li>✓ 中型: 400 GB/s NVLink</li>
                            <li>✓ 大型: 600 GB/s NVLink</li>
                        </ul>
                    </div>
                    
                    <div style="background: #fff3e0; padding: 20px; border-radius: 10px; border-left: 4px solid #ff9800;">
                        <h3 style="color: #e65100; margin-bottom: 10px;">瓶颈优化</h3>
                        <ul style="list-style: none; padding: 0;">
                            <li>✓ 小规模: 优化延迟（收益23%）</li>
                            <li>✓ 大规模: 优化带宽</li>
                            <li>✓ 优先单节点（避免跨节点损失91-98%）</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p><strong>SimAI深度研究 - Phase 5</strong></p>
            <p>研究者: 二愣子 🤔 | 研究时间: 2026-02-18至2026-02-19</p>
            <p style="margin-top: 10px;">基于8632行有效数据、121个CSV文件的系统性研究</p>
            <p style="margin-top: 15px; font-size: 0.9em;">
                <a href="#charts" style="color: #8fd3f4; text-decoration: none;">↑ 返回图表</a>
            </p>
        </div>
    </div>
</body>
</html>"""
        
        # 保存HTML文件
        html_path = self.output_dir / "dashboard.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"\n✅ HTML报告已生成: {html_path}")
        print("\n🌐 打开方式:")
        print(f"   在浏览器中打开: file://{html_path.absolute()}")
        print("\n💡 提示: 可以直接在浏览器中查看，无需网络连接")


def main():
    """主函数"""
    generator = HTMLReportGenerator()
    generator.generate_html_report()
    print("\n🎉 Phase 5 方向1（可视化工具）完成！")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
SimAI优先级5: 集成实践工具
研究如何将SimAI用于真实场景，设计端到端的仿真流程，创建可复用的测试框架
"""

import json
import math
from datetime import datetime
from typing import Dict, List, Optional

class SimAIIntegrationFramework:
    """SimAI集成实践框架"""
    
    def __init__(self):
        self.results = []
        
        # 系统参数
        self.bandwidth = 25.0  # Gbps
        self.latency = 0.01  # ms (10 μs)
        
        # Ratio表效率
        self.ratio_table = {
            1: 0.80,
            2: 0.60,
            4: 0.45,
            8: 0.30
        }
    
    def calculate_communication_time(
        self, 
        num_gpus: int, 
        data_size_mb: float,
        algorithm: str,
        num_nodes: int = 1
    ) -> Optional[Dict]:
        """计算集合通信时间"""
        
        data_size_bytes = data_size_mb * 1024 * 1024
        
        # 算法参数
        algo_params = {
            'Ring': {
                'steps': 2 * (num_gpus - 1),
                'data_per_step': data_size_bytes / num_gpus
            },
            'Tree': {
                'steps': 2 * math.ceil(math.log2(num_gpus)),
                'data_per_step': data_size_bytes / 2
            },
            'DBT': {
                'steps': 2 * math.ceil(math.log2(num_gpus)),
                'data_per_step': data_size_bytes / 4
            },
            'RecursiveDoubling': {
                'steps': math.ceil(math.log2(num_gpus)),
                'data_per_step': data_size_bytes / 2
            },
            'Hierarchical': {
                'steps': math.ceil(math.log2(num_gpus)) + math.ceil(math.log2(num_gpus / num_nodes)),
                'data_per_step': data_size_bytes / (2 * num_nodes)
            }
        }
        
        if algorithm not in algo_params:
            return None
        
        params = algo_params[algorithm]
        ratio_efficiency = self.ratio_table.get(num_nodes, 0.30)
        
        bandwidth_per_link_gbps = self.bandwidth * ratio_efficiency
        time_per_step_ms = (params['data_per_step'] * 8 / 1000) / bandwidth_per_link_gbps + self.latency
        total_time_ms = time_per_step_ms * params['steps']
        
        return {
            'algorithm': algorithm,
            'total_time_ms': round(total_time_ms, 6),
            'steps': params['steps'],
            'ratio_efficiency': ratio_efficiency
        }
    
    def recommend_algorithm(
        self, 
        num_gpus: int, 
        data_size_mb: float,
        num_nodes: int = 1
    ) -> Dict:
        """推荐最优算法"""
        
        algorithms = ['Ring', 'Tree', 'DBT', 'RecursiveDoubling', 'Hierarchical']
        
        best_algo = None
        best_time = float('inf')
        
        all_results = {}
        for algo in algorithms:
            result = self.calculate_communication_time(num_gpus, data_size_mb, algo, num_nodes)
            if result:
                all_results[algo] = result
                if result['total_time_ms'] < best_time:
                    best_time = result['total_time_ms']
                    best_algo = algo
        
        return {
            'recommended': best_algo,
            'predicted_time_ms': best_time,
            'all_algorithms': all_results
        }
    
    def design_end_to_end_workflow(self) -> Dict:
        """设计端到端的仿真流程"""
        
        workflow = {
            'name': 'SimAI端到端仿真流程',
            'version': '1.0',
            'description': '从需求分析到结果报告的完整仿真流程',
            'steps': []
        }
        
        # 步骤1: 需求分析
        workflow['steps'].append({
            'step': 1,
            'name': '需求分析',
            'description': '明确仿真目标和参数',
            'inputs': [
                '训练任务类型（LLM、CV、推荐系统等）',
                '模型大小（参数量）',
                'batch size',
                'GPU规模',
                '网络配置'
            ],
            'outputs': [
                'workload配置文件',
                '系统参数配置'
            ],
            'tools': [
                '需求调研问卷',
                '参数配置模板'
            ],
            'best_practices': [
                '从实际训练日志获取准确的数据大小',
                '考虑梯度累积、混合精度训练的影响',
                '明确是否使用模型并行'
            ]
        })
        
        # 步骤2: Workload生成
        workflow['steps'].append({
            'step': 2,
            'name': 'Workload生成',
            'description': '根据训练任务生成SimAI workload文件',
            'inputs': [
                '模型配置',
                '训练配置',
                '集合通信操作列表'
            ],
            'outputs': [
                'workload.csv文件',
                '操作统计信息'
            ],
            'tools': [
                'workload_generator.py',
                'pytorch_profiler_parser.py'
            ],
            'best_practices': [
                '使用真实的PyTorch profiler数据',
                '包含所有集合通信操作（AllReduce, AllGather等）',
                '保留实际的数据大小和频率'
            ]
        })
        
        # 步骤3: 仿真执行
        workflow['steps'].append({
            'step': 3,
            'name': 'SimAI仿真执行',
            'description': '运行SimAI Analytical模式进行性能仿真',
            'inputs': [
                'workload.csv文件',
                '系统配置（XML）',
                '网络拓扑配置'
            ],
            'outputs': [
                '仿真结果文件',
                '性能指标日志'
            ],
            'tools': [
                'SimAI Analytical',
                'run_simai.sh'
            ],
            'best_practices': [
                '根据实际硬件调整带宽和延迟参数',
                '选择正确的网络拓扑（Fat-Tree、Dragonfly等）',
                '运行多次仿真取平均值'
            ]
        })
        
        # 步骤4: 结果分析
        workflow['steps'].append({
            'step': 4,
            'name': '结果分析',
            'description': '解析仿真结果，提取关键性能指标',
            'inputs': [
                '仿真结果文件',
                '分析需求'
            ],
            'outputs': [
                '性能报告（Markdown/JSON）',
                '性能对比图表',
                '瓶颈识别结果'
            ],
            'tools': [
                'result_parser.py',
                'performance_analyzer.py',
                'visualization_dashboard.py'
            ],
            'best_practices': [
                '关注step time和通信时间占比',
                '识别慢速集合通信操作',
                '对比不同GPU规模的扩展性'
            ]
        })
        
        # 步骤5: 优化建议
        workflow['steps'].append({
            'step': 5,
            'name': '优化建议生成',
            'description': '基于仿真结果生成性能优化建议',
            'inputs': [
                '性能分析结果',
                '优化目标（时间/成本）'
            ],
            'outputs': [
                '优化建议清单',
                '预期性能提升',
                '实施方案'
            ],
            'tools': [
                'optimizer.py',
                'algorithm_selector.py'
            ],
            'best_practices': [
                '算法选择：根据GPU规模选择最优算法',
                '参数调优：带宽、延迟、Ratio表',
                '拓扑选择：Fat-Tree vs Dragonfly vs Torus',
                '分层数据：利用节点内高带宽'
            ]
        })
        
        # 步骤6: 验证测试
        workflow['steps'].append({
            'step': 6,
            'name': '验证测试',
            'description': '在实际硬件上验证仿真预测',
            'inputs': [
                '优化建议',
                '测试脚本'
            ],
            'outputs': [
                '实际测试结果',
                '仿真vs实际对比报告',
                '模型调优参数'
            ],
            'tools': [
                'pytorch_ddp_benchmark.py',
                'nccl_tests.sh',
                'calibrate_model_parameters.py'
            ],
            'best_practices': [
                '使用相同的配置（GPU、数据大小）',
                '运行多次测试减少噪声',
                '记录实际带宽和延迟',
                '调整SimAI参数以匹配实际'
            ]
        })
        
        return workflow
    
    def create_real_world_cases(self) -> List[Dict]:
        """创建真实世界应用案例"""
        
        cases = []
        
        # 案例1: GPT-3训练（175B参数）
        cases.append({
            'id': 1,
            'name': 'GPT-3训练',
            'description': '175B参数的大语言模型训练',
            'model_size_gb': 350,  # 175B * 2 bytes (fp16)
            'num_gpus': 1024,
            'num_nodes': 128,
            'batch_size': 1536,
            'sequence_length': 2048,
            'collective_operations': [
                {'operation': 'AllReduce', 'data_size_mb': 700, 'frequency': '每步'},  # 梯度同步
                {'operation': 'AllGather', 'data_size_mb': 1.75, 'frequency': '每步'},  # embedding
            ],
            'network_config': {
                'topology': 'Fat-Tree',
                'bandwidth_gbps': 200,
                'latency_us': 10,
                'node_bandwidth': 'NVLink (300 GB/s)'
            },
            'expected_bottleneck': 'AllReduce梯度同步',
            'optimization_suggestions': [
                '使用梯度压缩',
                '使用Hierarchical算法',
                '增加模型并行度',
                '使用Flash Attention减少通信'
            ]
        })
        
        # 案例2: ResNet-50训练（ImageNet）
        cases.append({
            'id': 2,
            'name': 'ResNet-50训练',
            'description': 'ImageNet图像分类训练',
            'model_size_mb': 100,
            'num_gpus': 64,
            'num_nodes': 8,
            'batch_size': 256,
            'collective_operations': [
                {'operation': 'AllReduce', 'data_size_mb': 200, 'frequency': '每步'},
                {'operation': 'Broadcast', 'data_size_mb': 100, 'frequency': '初始化'},
            ],
            'network_config': {
                'topology': 'Dragonfly',
                'bandwidth_gbps': 100,
                'latency_us': 15
            },
            'expected_bottleneck': 'AllReduce梯度同步',
            'optimization_suggestions': [
                '使用DBT算法',
                '增加batch size减少通信频率',
                '使用混合精度训练'
            ]
        })
        
        # 案例3: 推荐系统训练（DLRM）
        cases.append({
            'id': 3,
            'name': '推荐系统训练',
            'description': '深度学习推荐模型（DLRM）',
            'model_size_mb': 500,
            'num_gpus': 32,
            'num_nodes': 4,
            'batch_size': 65536,
            'collective_operations': [
                {'operation': 'AllReduce', 'data_size_mb': 1000, 'frequency': '每步'},
                {'operation': 'AllToAll', 'data_size_mb': 64, 'frequency': '每步'},  # embedding交互
            ],
            'network_config': {
                'topology': 'Single_Node',
                'bandwidth_gbps': 25,
                'latency_us': 10
            },
            'expected_bottleneck': 'AllToAll embedding交互',
            'optimization_suggestions': [
                '使用专门的AllToAll优化',
                '考虑ZeRO优化器',
                '使用通信算子融合'
            ]
        })
        
        # 案例4: BERT推理（批量）
        cases.append({
            'id': 4,
            'name': 'BERT批量推理',
            'description': 'BERT模型批量推理服务',
            'model_size_mb': 420,
            'num_gpus': 8,
            'num_nodes': 1,
            'batch_size': 128,
            'collective_operations': [
                {'operation': 'AllGather', 'data_size_mb': 420, 'frequency': '每次请求'},  # 模型加载
            ],
            'network_config': {
                'topology': 'Single_Node',
                'bandwidth_gbps': 300,  # NVLink
                'latency_us': 1
            },
            'expected_bottleneck': '模型加载和同步',
            'optimization_suggestions': [
                '使用模型分片',
                '预加载模型到GPU内存',
                '使用TensorRT优化'
            ]
        })
        
        # 案例5: 分布式强化学习
        cases.append({
            'id': 5,
            'name': '分布式强化学习',
            'description': '多智能体强化学习训练',
            'model_size_mb': 50,
            'num_gpus': 16,
            'num_nodes': 2,
            'batch_size': 1024,
            'collective_operations': [
                {'operation': 'ReduceScatter', 'data_size_mb': 100, 'frequency': '每步'},
                {'operation': 'AllGather', 'data_size_mb': 100, 'frequency': '每步'},
            ],
            'network_config': {
                'topology': 'Torus',
                'bandwidth_gbps': 50,
                'latency_us': 5
            },
            'expected_bottleneck': 'ReduceScatter + AllGather',
            'optimization_suggestions': [
                '使用Ring算法',
                '优化经验回放buffer传输',
                '使用异步训练'
            ]
        })
        
        return cases
    
    def create_reusable_framework(self) -> Dict:
        """创建可复用的测试框架"""
        
        framework = {
            'name': 'SimAI可复用测试框架',
            'version': '1.0',
            'components': []
        }
        
        # 组件1: Workload生成器
        framework['components'].append({
            'name': 'WorkloadGenerator',
            'description': '从PyTorch代码或profiler数据生成workload',
            'input_formats': ['pytorch_trace', 'pytorch_profiler', 'manual_config'],
            'output': 'workload.csv',
            'key_features': [
                '自动检测集合通信操作',
                '提取数据大小和调用频率',
                '支持自定义操作注入'
            ],
            'configuration': {
                'operations': ['AllReduce', 'AllToAll', 'Broadcast', 'Reduce', 'ReduceScatter', 'AllGather'],
                'data_source': 'profiler or manual',
                'num_steps': 1000
            }
        })
        
        # 组件2: 配置管理器
        framework['components'].append({
            'name': 'ConfigManager',
            'description': '管理系统和网络配置',
            'input_formats': ['json', 'yaml', 'xml'],
            'output': 'SimAI配置文件',
            'key_features': [
                '预设配置模板（H100, A100等）',
                '参数校准工具',
                '配置验证'
            ],
            'configuration': {
                'templates': ['H100_NVLINK', 'A100_PCIE', 'V100_PCIE', 'Custom'],
                'parameters': ['bandwidth', 'latency', 'topology', 'ratio_table']
            }
        })
        
        # 组件3: 仿真执行器
        framework['components'].append({
            'name': 'SimulatorRunner',
            'description': '执行SimAI仿真并收集结果',
            'input': ['workload.csv', 'config file'],
            'output': ['simulation results', 'metrics'],
            'key_features': [
                '批量仿真（多配置并行）',
                '结果缓存',
                '错误处理和重试'
            ],
            'configuration': {
                'mode': 'analytical',
                'num_runs': 3,
                'parallel_jobs': 4
            }
        })
        
        # 组件4: 性能分析器
        framework['components'].append({
            'name': 'PerformanceAnalyzer',
            'description': '分析仿真结果，生成报告',
            'input': ['simulation results'],
            'output': ['report (Markdown/JSON)', 'charts'],
            'key_features': [
                '瓶颈识别',
                '算法对比',
                '扩展性分析',
                '可视化生成'
            ],
            'configuration': {
                'metrics': ['step_time', 'comm_time', 'throughput', 'scalability'],
                'charts': ['timeline', 'heatmap', 'comparison'],
                'format': ['markdown', 'json', 'html']
            }
        })
        
        # 组件5: 优化建议器
        framework['components'].append({
            'name': 'OptimizationAdvisor',
            'description': '基于分析结果生成优化建议',
            'input': ['analysis results'],
            'output': ['optimization suggestions'],
            'key_features': [
                '算法选择建议',
                '参数调优建议',
                '拓扑选择建议',
                '预期性能提升'
            ],
            'configuration': {
                'optimization_goals': ['minimize_time', 'minimize_cost', 'balance'],
                'algorithms': ['Ring', 'Tree', 'DBT', 'Hierarchical'],
                'topologies': ['Fat-Tree', 'Dragonfly', 'Torus']
            }
        })
        
        return framework
    
    def generate_best_practices(self) -> Dict:
        """生成最佳实践指南"""
        
        practices = {
            'principles': [],
            'pitfalls': [],
            'tips': [],
            'checklist': []
        }
        
        # 核心原则
        practices['principles'] = [
            {
                'id': 1,
                'name': '真实性优先',
                'description': '使用真实的workload和数据，不要凭空假设',
                'examples': [
                    '从PyTorch profiler获取实际数据大小',
                    '使用实际的网络带宽和延迟',
                    '考虑训练的实际配置（混合精度、梯度累积等）'
                ]
            },
            {
                'id': 2,
                'name': '场景化分析',
                'description': '根据具体应用场景进行分析',
                'examples': [
                    'LLM训练关注AllReduce性能',
                    '推荐系统关注AllToAll性能',
                    '推理服务关注Broadcast性能'
                ]
            },
            {
                'id': 3,
                'name': '系统性优化',
                'description': '从多个维度进行优化',
                'examples': [
                    '算法选择：根据GPU规模选择',
                    '参数调优：带宽、延迟、Ratio表',
                    '拓扑选择：考虑成本和性能',
                    'workload优化：减少通信量'
                ]
            },
            {
                'id': 4,
                'name': '验证驱动',
                'description': '在实际硬件上验证仿真结果',
                'examples': [
                    '运行PyTorch DDP benchmark',
                    '对比预测时间vs实际时间',
                    '调整模型参数以提高准确性'
                ]
            },
            {
                'id': 5,
                'name': '迭代改进',
                'description': '持续优化和改进仿真模型',
                'examples': [
                    '记录每次仿真的配置和结果',
                    '分析误差来源',
                    '逐步改进模型准确性'
                ]
            }
        ]
        
        # 常见陷阱
        practices['pitfalls'] = [
            {
                'id': 1,
                'pitfall': '使用默认参数',
                'impact': '预测误差可能达到100倍以上',
                'solution': '根据实际硬件配置调整带宽、延迟、Ratio表'
            },
            {
                'id': 2,
                'pitfall': '忽略Ratio表',
                'impact': '多节点性能预测严重高估',
                'solution': '正确设置Ratio表效率，考虑节点间开销'
            },
            {
                'id': 3,
                'pitfall': '算法选择不当',
                'impact': '性能可能相差10倍以上',
                'solution': '根据GPU规模和数据大小选择最优算法'
            },
            {
                'id': 4,
                'pitfall': '数据大小不准确',
                'impact': '时间预测线性偏差',
                'solution': '从profiler获取实际数据大小'
            },
            {
                'id': 5,
                'pitfall': '忽略网络拓扑',
                'impact': '带宽利用率估计错误',
                'solution': '选择正确的拓扑（Fat-Tree、Dragonfly等）'
            }
        ]
        
        # 实用技巧
        practices['tips'] = [
            {
                'category': 'Workload生成',
                'tips': [
                    '使用pytorch profiler自动生成workload',
                    '手动指定关键操作（AllReduce通常最重要）',
                    '包含完整的训练步骤（前向+反向+优化）'
                ]
            },
            {
                'category': '参数配置',
                'tips': [
                    'H100 NVLink: 带宽300 GB/s, 延迟1μs',
                    'A100 PCIe: 带宽25 GB/s, 延迟10μs',
                    'V100 PCIe: 带宽12 GB/s, 延迟15μs'
                ]
            },
            {
                'category': '算法选择',
                'tips': [
                    '≤4 GPU: Ring或RecursiveDoubling',
                    '8-32 GPU: DBT',
                    '≥32 GPU多节点: Hierarchical',
                    '避免使用Tree（性能差）'
                ]
            },
            {
                'category': '性能分析',
                'tips': [
                    '关注step time和通信时间占比',
                    '识别最慢的集合通信操作',
                    '对比不同GPU规模的扩展性'
                ]
            }
        ]
        
        # 检查清单
        practices['checklist'] = [
            '✓ Workload是否基于真实profiler数据？',
            '✓ 带宽和延迟是否匹配实际硬件？',
            '✓ Ratio表效率是否正确设置？',
            '✓ 网络拓扑是否正确配置？',
            '✓ 是否选择了合适的算法？',
            '✓ 是否运行了多次仿真验证？',
            '✓ 是否在实际硬件上验证了预测？',
            '✓ 是否记录了所有配置和结果？',
            '✓ 是否生成了优化建议？',
            '✓ 是否有改进计划？'
        ]
        
        return practices
    
    def run_full_analysis(self) -> Dict:
        """运行完整的集成实践分析"""
        
        print("=" * 80)
        print("SimAI优先级5: 集成实践分析")
        print("=" * 80)
        print()
        
        # 1. 端到端流程设计
        print("1. 端到端仿真流程设计")
        print("-" * 80)
        
        workflow = self.design_end_to_end_workflow()
        
        print(f"\n流程名称: {workflow['name']} v{workflow['version']}")
        print(f"描述: {workflow['description']}")
        print(f"\n包含{len(workflow['steps'])}个步骤：\n")
        
        for step in workflow['steps']:
            print(f"步骤{step['step']}: {step['name']}")
            print(f"  描述: {step['description']}")
            print(f"  输入: {', '.join(step['inputs'][:2])}...")
            print(f"  输出: {', '.join(step['outputs'][:2])}...")
            print(f"  工具: {', '.join(step['tools'][:2])}...")
            print()
        
        # 2. 真实案例
        print("2. 真实世界应用案例")
        print("-" * 80)
        
        cases = self.create_real_world_cases()
        
        print(f"\n共{len(cases)}个真实案例：\n")
        
        for case in cases:
            print(f"案例{case['id']}: {case['name']}")
            print(f"  描述: {case['description']}")
            print(f"  GPU: {case['num_gpus']} ({case['num_nodes']}节点)")
            print(f"  模型大小: {case.get('model_size_gb', case.get('model_size_mb', 0))} "
                  f"{'GB' if 'model_size_gb' in case else 'MB'}")
            
            # 推荐算法
            rec = self.recommend_algorithm(case['num_gpus'], 700, case['num_nodes'])
            print(f"  推荐算法: {rec['recommended']}")
            print(f"  预测通信时间: {rec['predicted_time_ms']:.4f}ms")
            
            print(f"  主要操作: {', '.join([op['operation'] for op in case['collective_operations'][:2]])}")
            print(f"  网络拓扑: {case['network_config']['topology']}")
            print(f"  瓶颈: {case['expected_bottleneck']}")
            print()
        
        # 3. 可复用框架
        print("3. 可复用测试框架")
        print("-" * 80)
        
        framework = self.create_reusable_framework()
        
        print(f"\n框架名称: {framework['name']} v{framework['version']}")
        print(f"包含{len(framework['components'])}个核心组件：\n")
        
        for component in framework['components']:
            print(f"组件: {component['name']}")
            print(f"  描述: {component['description']}")
            print(f"  功能: {', '.join(component['key_features'][:2])}...")
            print()
        
        # 4. 最佳实践
        print("4. 最佳实践指南")
        print("-" * 80)
        
        practices = self.generate_best_practices()
        
        print(f"\n核心原则 ({len(practices['principles'])}条):")
        for principle in practices['principles'][:3]:
            print(f"  {principle['id']}. {principle['name']}: {principle['description']}")
        
        print(f"\n常见陷阱 ({len(practices['pitfalls'])}条):")
        for pitfall in practices['pitfalls'][:3]:
            print(f"  ⚠️  {pitfall['pitfall']}: {pitfall['solution']}")
        
        print(f"\n实用技巧:")
        for category in ['Workload生成', '算法选择']:
            tips = [t for t in practices['tips'] if t['category'] == category]
            if tips:
                print(f"\n  {category}:")
                for tip in tips[0]['tips'][:2]:
                    print(f"    • {tip}")
        
        print(f"\n检查清单 ({len(practices['checklist'])}项):")
        for item in practices['checklist'][:5]:
            print(f"  {item}")
        
        # 汇总结果
        integration_result = {
            'timestamp': datetime.now().isoformat(),
            'workflow': workflow,
            'real_world_cases': cases,
            'reusable_framework': framework,
            'best_practices': practices,
            'summary': {
                'workflow_steps': len(workflow['steps']),
                'total_cases': len(cases),
                'framework_components': len(framework['components']),
                'principles': len(practices['principles']),
                'pitfalls': len(practices['pitfalls']),
                'tips': len(practices['tips']),
                'checklist_items': len(practices['checklist'])
            }
        }
        
        return integration_result
    
    def save_results(self, results: Dict, filename: str):
        """保存结果到JSON文件"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n✅ 结果已保存到: {filename}")

def main():
    """主函数"""
    integrator = SimAIIntegrationFramework()
    
    # 运行完整分析
    results = integrator.run_full_analysis()
    
    # 保存结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"priority5_integration_practice_{timestamp}.json"
    integrator.save_results(results, filename)
    
    # 生成Markdown报告
    report_filename = f"PRIORITY5_INTEGRATION_REPORT_{timestamp}.md"
    
    with open(report_filename, 'w', encoding='utf-8') as f:
        f.write(f"# SimAI优先级5: 集成实践报告\n\n")
        f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"## 执行摘要\n\n")
        
        f.write(f"### 覆盖范围\n")
        f.write(f"- 端到端流程步骤: {results['summary']['workflow_steps']}\n")
        f.write(f"- 真实案例: {results['summary']['total_cases']}\n")
        f.write(f"- 框架组件: {results['summary']['framework_components']}\n")
        f.write(f"- 核心原则: {results['summary']['principles']}\n")
        f.write(f"- 常见陷阱: {results['summary']['pitfalls']}\n")
        f.write(f"- 实用技巧: {results['summary']['tips']}\n")
        f.write(f"- 检查清单: {results['summary']['checklist_items']}\n\n")
        
        f.write(f"## 端到端仿真流程\n\n")
        
        for step in results['workflow']['steps']:
            f.write(f"### 步骤{step['step']}: {step['name']}\n\n")
            f.write(f"**描述**: {step['description']}\n\n")
            f.write(f"**输入**: \n")
            for inp in step['inputs']:
                f.write(f"- {inp}\n")
            f.write(f"\n**输出**: \n")
            for out in step['outputs']:
                f.write(f"- {out}\n")
            f.write(f"\n**工具**: {', '.join(step['tools'])}\n\n")
            f.write(f"**最佳实践**: \n")
            for bp in step['best_practices']:
                f.write(f"- {bp}\n")
            f.write("\n")
        
        f.write(f"\n## 真实世界案例\n\n")
        
        for case in results['real_world_cases']:
            f.write(f"### 案例{case['id']}: {case['name']}\n\n")
            f.write(f"**描述**: {case['description']}\n\n")
            f.write(f"- **模型大小**: {case.get('model_size_gb', case.get('model_size_mb', 0))}\n")
            f.write(f"- **GPU规模**: {case['num_gpus']} GPU ({case['num_nodes']} 节点)\n")
            f.write(f"- **Batch Size**: {case['batch_size']}\n")
            f.write(f"- **网络拓扑**: {case['network_config']['topology']}\n")
            f.write(f"- **带宽**: {case['network_config']['bandwidth_gbps']} Gbps\n")
            f.write(f"- **预期瓶颈**: {case['expected_bottleneck']}\n\n")
            
            f.write(f"**集合通信操作**: \n")
            for op in case['collective_operations']:
                f.write(f"- {op['operation']}: {op['data_size_mb']} MB, 频率: {op['frequency']}\n")
            
            f.write(f"\n**优化建议**: \n")
            for suggestion in case['optimization_suggestions']:
                f.write(f"- {suggestion}\n")
            
            f.write("\n")
        
        f.write(f"\n## 可复用框架\n\n")
        
        for component in results['reusable_framework']['components']:
            f.write(f"### {component['name']}\n\n")
            f.write(f"**描述**: {component['description']}\n\n")
            f.write(f"**输入格式**: {', '.join(component['input_formats'] if 'input_formats' in component else ['N/A'])}\n")
            f.write(f"**输出**: {component['output'] if 'output' in component else 'N/A'}\n\n")
            f.write(f"**关键特性**: \n")
            for feature in component['key_features']:
                f.write(f"- {feature}\n")
            f.write("\n")
        
        f.write(f"\n## 最佳实践\n\n")
        
        f.write(f"### 核心原则\n\n")
        for principle in results['best_practices']['principles']:
            f.write(f"**{principle['id']}. {principle['name']}**\n\n")
            f.write(f"{principle['description']}\n\n")
            f.write(f"示例: \n")
            for example in principle['examples']:
                f.write(f"- {example}\n")
            f.write("\n")
        
        f.write(f"\n### 常见陷阱\n\n")
        for pitfall in results['best_practices']['pitfalls']:
            f.write(f"**⚠️ {pitfall['pitfall']}**\n\n")
            f.write(f"- **影响**: {pitfall['impact']}\n")
            f.write(f"- **解决方案**: {pitfall['solution']}\n\n")
        
        f.write(f"\n### 检查清单\n\n")
        for item in results['best_practices']['checklist']:
            f.write(f"{item}\n")
        
        f.write(f"\n---\n\n")
        f.write(f"*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
        f.write(f"*分析工具: priority5_integration_practice.py*\n")
    
    print(f"✅ Markdown报告已保存到: {report_filename}")
    print("\n" + "=" * 80)
    print("优先级5集成实践分析完成！")
    print("=" * 80)

if __name__ == "__main__":
    main()

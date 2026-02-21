#!/usr/bin/env python3
"""
SimAI性能预测器
基于Ratio表预测集合通信性能
"""

import numpy as np
from pathlib import Path
import json
from ratio_table_parser import RatioTableParser


class SimAIPerformancePredictor:
    """SimAI性能预测器"""
    
    def __init__(self, gpu_type='A100', ratio_dir=None):
        """初始化预测器
        
        Args:
            gpu_type: GPU类型 ('A100' 或 'H100')
            ratio_dir: Ratio表目录
        """
        self.gpu_type = gpu_type
        self.parser = RatioTableParser(ratio_dir)
        self.parser.load_tables()
        
        # 带宽配置 (GB/s)
        self.bandwidths = {
            'A100': {
                'nvlink': 300,    # NVLink第三代
                'nic': 25         # InfiniBand HDR (200 Gbps)
            },
            'H100': {
                'nvlink': 450,    # NVLink第四代
                'nic': 50         # InfiniBand NDR (400 Gbps)
            }
        }
        
    def predict(self, num_nodes, num_ranks, size_bytes, 
                algorithm='tree', collective='allreduce'):
        """预测通信时间
        
        Args:
            num_nodes: 节点数量
            num_ranks: GPU总数
            size_bytes: 数据大小（字节）
            algorithm: 算法类型 ('ring', 'tree', 'dbt')
            collective: 集合通信类型 ('allreduce', 'allgather', 'alltoall')
            
        Returns:
            预测的通信时间（秒）
        """
        # 1. 查询效率
        efficiency = self.parser.query(num_nodes, num_ranks, size_bytes, algorithm)
        
        if np.isnan(efficiency):
            print(f"⚠️  无法查询效率值，配置可能超出Ratio表范围")
            return None
        
        # 2. 确定带宽
        if num_nodes == 1:
            bw = self.bandwidths[self.gpu_type]['nvlink']
            link_type = 'NVLink'
        else:
            bw = self.bandwidths[self.gpu_type]['nic']
            link_type = 'NIC'
        
        # 3. 算法系数
        algo_factor = self._get_algo_factor(num_ranks, algorithm, collective)
        
        # 4. 跳数惩罚
        hop_factor = self._get_hop_factor(num_nodes, algorithm)
        
        # 5. 计算时间
        # T = (Size / BW) × (1 / η) × Algo × Hop
        t_comm = (size_bytes / (bw * 1e9)) * (1 / efficiency) * algo_factor * hop_factor
        
        return {
            'time_seconds': t_comm,
            'time_ms': t_comm * 1000,
            'time_us': t_comm * 1e6,
            'efficiency': efficiency,
            'bandwidth': bw,
            'link_type': link_type,
            'algo_factor': algo_factor,
            'hop_factor': hop_factor
        }
    
    def _get_algo_factor(self, num_ranks, algorithm, collective):
        """计算算法系数
        
        Args:
            num_ranks: GPU数量
            algorithm: 算法类型
            collective: 集合通信类型
            
        Returns:
            算法系数
        """
        if collective == 'allreduce':
            if algorithm == 'ring':
                # Ring: 2(N-1)步，每步Size/N
                return 2 * (num_ranks - 1) / num_ranks
            elif algorithm == 'tree':
                # Tree: 2log2(N)步，每步Size
                return 2 * np.log2(num_ranks)
            elif algorithm == 'dbt':
                # DBT: log2(N)步，每步Size
                return np.log2(num_ranks)
            else:
                return 1.0
        elif collective == 'allgather':
            if algorithm == 'ring':
                return (num_ranks - 1) / num_ranks
            elif algorithm == 'tree':
                return np.log2(num_ranks)
            else:
                return 1.0
        elif collective == 'alltoall':
            # AllToAll: 每个GPU发送(N-1)次，每次Size/N
            return (num_ranks - 1) / num_ranks
        else:
            return 1.0
    
    def _get_hop_factor(self, num_nodes, algorithm):
        """计算跳数惩罚系数
        
        Args:
            num_nodes: 节点数量
            algorithm: 算法类型
            
        Returns:
            跳数惩罚系数
        """
        if num_nodes == 1:
            # 单节点无跨节点跳数
            return 1.0
        elif algorithm == 'ring':
            # Ring跨节点跳数较多
            return 1.5
        elif algorithm == 'tree':
            # Tree跨节点层次深
            return 2.0
        elif algorithm == 'dbt':
            # DBT相对较好
            return 1.8
        else:
            return 1.5
    
    def compare_algorithms(self, num_nodes, num_ranks, size_bytes, collective='allreduce'):
        """对比不同算法的性能
        
        Args:
            num_nodes: 节点数量
            num_ranks: GPU总数
            size_bytes: 数据大小
            collective: 集合通信类型
            
        Returns:
            算法性能对比字典
        """
        algorithms = ['ring', 'tree', 'dbt']
        results = {}
        
        for algo in algorithms:
            result = self.predict(num_nodes, num_ranks, size_bytes, algo, collective)
            if result is not None:
                results[algo] = result
        
        # 找到最快算法
        if results:
            fastest = min(results.items(), key=lambda x: x[1]['time_ms'])
            
            # 计算相对性能
            for algo, result in results.items():
                result['relative_to_fastest'] = result['time_ms'] / fastest[1]['time_ms']
        
        return results
    
    def batch_predict(self, configs):
        """批量预测
        
        Args:
            configs: 配置列表 [(num_nodes, num_ranks, size_bytes, algorithm, collective), ...]
            
        Returns:
            预测结果列表
        """
        results = []
        
        for config in configs:
            num_nodes, num_ranks, size_bytes, algorithm, collective = config
            result = self.predict(num_nodes, num_ranks, size_bytes, algorithm, collective)
            
            results.append({
                'config': config,
                'result': result
            })
        
        return results
    
    def export_prediction_report(self, output_path):
        """导出预测报告"""
        # 生成标准测试用例
        test_cases = [
            # (num_nodes, num_ranks, size_bytes, algorithm, collective)
            (1, 8, 16*1024*1024, 'tree', 'allreduce'),
            (1, 8, 1024*1024*1024, 'tree', 'allreduce'),
            (2, 16, 64*1024*1024, 'tree', 'allreduce'),
            (2, 16, 1024*1024*1024, 'tree', 'allreduce'),
        ]
        
        results = []
        for case in test_cases:
            num_nodes, num_ranks, size_bytes, algorithm, collective = case
            result = self.predict(num_nodes, num_ranks, size_bytes, algorithm, collective)
            
            if result is not None:
                results.append({
                    'config': {
                        'num_nodes': num_nodes,
                        'num_ranks': num_ranks,
                        'size_mb': size_bytes / 1024 / 1024,
                        'algorithm': algorithm,
                        'collective': collective
                    },
                    'prediction': {
                        'time_ms': result['time_ms'],
                        'efficiency': result['efficiency'],
                        'bandwidth_gb_s': result['bandwidth'],
                        'link_type': result['link_type']
                    }
                })
        
        # 导出JSON
        with open(output_path, 'w') as f:
            json.dump({
                'gpu_type': self.gpu_type,
                'predictions': results
            }, f, indent=2)
        
        print(f"✅ 预测报告导出到: {output_path}")


def main():
    """测试函数"""
    print("SimAI性能预测器测试\n")
    
    # 创建预测器
    predictor = SimAIPerformancePredictor(gpu_type='A100')
    
    print("="*60)
    print("测试1: 单节点8 GPU, 1 GB, Tree算法, AllReduce")
    print("="*60)
    
    result = predictor.predict(
        num_nodes=1,
        num_ranks=8,
        size_bytes=1024*1024*1024,
        algorithm='tree',
        collective='allreduce'
    )
    
    if result:
        print(f"预测时间: {result['time_ms']:.2f} ms")
        print(f"效率: η = {result['efficiency']:.3f}")
        print(f"带宽: {result['bandwidth']} GB/s ({result['link_type']})")
        print(f"算法系数: {result['algo_factor']:.2f}")
        print(f"跳数系数: {result['hop_factor']:.2f}")
    
    print("\n" + "="*60)
    print("测试2: 算法对比 (单节点8 GPU, 1 GB, AllReduce)")
    print("="*60)
    
    comparison = predictor.compare_algorithms(
        num_nodes=1,
        num_ranks=8,
        size_bytes=1024*1024*1024,
        collective='allreduce'
    )
    
    for algo, result in comparison.items():
        print(f"\n{algo.upper()}算法:")
        print(f"  时间: {result['time_ms']:.2f} ms")
        print(f"  相对性能: {result['relative_to_fastest']:.2f}x")
    
    print("\n" + "="*60)
    print("测试3: 跨节点性能 (2节点16 GPU, 1 GB, AllReduce)")
    print("="*60)
    
    result = predictor.predict(
        num_nodes=2,
        num_ranks=16,
        size_bytes=1024*1024*1024,
        algorithm='tree',
        collective='allreduce'
    )
    
    if result:
        print(f"预测时间: {result['time_ms']:.2f} ms")
        print(f"效率: η = {result['efficiency']:.3f}")
        print(f"带宽: {result['bandwidth']} GB/s ({result['link_type']})")
    
    # 导出报告
    predictor.export_prediction_report('performance_prediction_report.json')
    
    print("\n✅ 测试完成!")


if __name__ == '__main__':
    main()

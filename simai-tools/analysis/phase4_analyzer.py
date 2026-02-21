#!/usr/bin/env python3
"""
Phase 4 Deep Analysis Tool
==========================
Analyzes Phase 4 workloads with focus on:
1. Mixed collective operations (Transformer training)
2. Parameter sensitivity (bandwidth, latency, topology)
3. Algorithm comparison (Tree vs Ring vs Hierarchical)
4. Extreme scale (256+ GPUs)
5. Ratio table impact validation

Author: 二愣子 🤔
Date: 2026-02-18
"""

import csv
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any
from collections import defaultdict

class Phase4Analyzer:
    """Phase 4 workload analyzer"""
    
    def __init__(self, results_dir: str):
        self.results_dir = Path(results_dir)
        self.data = []
        
    def find_all_csv_files(self) -> List[Path]:
        """Find all CSV files in results directory"""
        return list(self.results_dir.rglob("*.csv"))
    
    def parse_csv_file(self, csv_path: Path) -> List[Dict[str, Any]]:
        """Parse a single CSV file and extract metrics"""
        results = []
        
        try:
            with open(csv_path, 'r') as f:
                reader = csv.reader(f)
                rows = list(reader)
                
            # Skip header rows (usually 3 rows)
            if len(rows) < 4:
                print(f"⚠️  {csv_path.name}: Not enough data rows")
                return []
            
            # Extract metadata from filename
            filename = csv_path.stem
            parts = filename.split('-')
            
            # Parse rows starting from row 3 (0-indexed)
            for i, row in enumerate(rows[3:], start=3):
                if len(row) < 11:
                    continue
                    
                try:
                    result = {
                        'file': csv_path.name,
                        'filename': filename,
                        'row_index': i,
                        'layer_name': row[0] if len(row) > 0 else '',
                        'fwd_comm_us': float(row[5]) if len(row) > 5 and row[5] else 0.0,
                        'bwd_comm_us': float(row[7]) if len(row) > 7 and row[7] else 0.0,
                        'total_comm_us': float(row[8]) if len(row) > 8 and row[8] else 0.0,
                        'fwd_alg_bw_gbps': float(row[9]) if len(row) > 9 and row[9] else 0.0,
                        'bus_bw_gbps': float(row[10]) if len(row) > 10 and row[10] else 0.0,
                    }
                    
                    # Calculate efficiency
                    if result['bus_bw_gbps'] > 0:
                        # Theoretical max: 240 GB/s for A100, 370.8 GB/s for H100
                        theoretical_max = 240.0
                        result['efficiency_pct'] = (result['bus_bw_gbps'] / theoretical_max) * 100
                    
                    results.append(result)
                    
                except (ValueError, IndexError) as e:
                    print(f"⚠️  {csv_path.name}:{i}: Parse error - {e}")
                    continue
                    
        except Exception as e:
            print(f"❌ {csv_path.name}: Failed to parse - {e}")
            
        return results
    
    def load_all_data(self):
        """Load and parse all CSV files"""
        csv_files = self.find_all_csv_files()
        print(f"📁 Found {len(csv_files)} CSV files")
        
        all_results = []
        for csv_path in csv_files:
            results = self.parse_csv_file(csv_path)
            all_results.extend(results)
        
        self.data = all_results
        print(f"✅ Loaded {len(all_results)} data rows")
        return all_results
    
    def analyze_mixed_collective_ops(self) -> Dict[str, Any]:
        """Analyze mixed collective operations (Transformer training)"""
        mixed_ops = [d for d in self.data if 'mixed' in d['filename'].lower()]
        
        if not mixed_ops:
            return {'status': 'No data', 'data': []}
        
        # Group by collective operation type
        by_op = defaultdict(list)
        for d in mixed_ops:
            # Extract operation type from layer name
            layer_name = d['layer_name'].lower()
            if 'allreduce' in layer_name:
                by_op['ALLREDUCE'].append(d)
            elif 'allgather' in layer_name:
                by_op['ALLGATHER'].append(d)
            elif 'reducescatter' in layer_name:
                by_op['REDUCESCATTER'].append(d)
            elif 'alltoall' in layer_name:
                by_op['ALLTOALL'].append(d)
        
        # Calculate statistics for each operation
        stats = {}
        for op, data in by_op.items():
            if data:
                comm_times = [d['total_comm_us'] for d in data if d['total_comm_us'] > 0]
                bus_bws = [d['bus_bw_gbps'] for d in data if d['bus_bw_gbps'] > 0]
                
                stats[op] = {
                    'count': len(data),
                    'avg_comm_us': sum(comm_times) / len(comm_times) if comm_times else 0,
                    'min_comm_us': min(comm_times) if comm_times else 0,
                    'max_comm_us': max(comm_times) if comm_times else 0,
                    'avg_bus_bw_gbps': sum(bus_bws) / len(bus_bws) if bus_bws else 0,
                }
        
        return {
            'status': 'success',
            'total_rows': len(mixed_ops),
            'by_operation': stats,
            'performance_ranking': sorted(
                [(op, s['avg_comm_us']) for op, s in stats.items()],
                key=lambda x: x[1]
            )
        }
    
    def analyze_parameter_sensitivity(self) -> Dict[str, Any]:
        """Analyze parameter sensitivity (bandwidth, latency, topology)"""
        param_tests = [d for d in self.data if 'param' in d['filename'].lower() or 'topology' in d['filename'].lower()]
        
        if not param_tests:
            return {'status': 'No data', 'data': []}
        
        # Group by parameter type
        by_param = defaultdict(list)
        for d in param_tests:
            by_param[d['filename']].append(d)
        
        # Calculate statistics for each parameter configuration
        stats = {}
        for filename, data in by_param.items():
            if data:
                comm_times = [d['total_comm_us'] for d in data if d['total_comm_us'] > 0]
                bus_bws = [d['bus_bw_gbps'] for d in data if d['bus_bw_gbps'] > 0]
                
                stats[filename] = {
                    'count': len(data),
                    'avg_comm_us': sum(comm_times) / len(comm_times) if comm_times else 0,
                    'avg_bus_bw_gbps': sum(bus_bws) / len(bus_bws) if bus_bws else 0,
                }
        
        return {
            'status': 'success',
            'total_rows': len(param_tests),
            'by_parameter': stats,
        }
    
    def analyze_extreme_scale(self) -> Dict[str, Any]:
        """Analyze extreme scale performance (256+ GPUs)"""
        extreme = [d for d in self.data if '256' in d['filename'] or 'extreme' in d['filename'].lower()]
        
        if not extreme:
            return {'status': 'No data', 'data': []}
        
        # Group by GPU count
        by_gpu = defaultdict(list)
        for d in extreme:
            # Extract GPU count from filename
            for gpu_count in [64, 128, 256, 512, 1024]:
                if str(gpu_count) in d['filename']:
                    by_gpu[gpu_count].append(d)
                    break
        
        # Calculate statistics for each GPU count
        stats = {}
        for gpu_count, data in sorted(by_gpu.items()):
            if data:
                comm_times = [d['total_comm_us'] for d in data if d['total_comm_us'] > 0]
                bus_bws = [d['bus_bw_gbps'] for d in data if d['bus_bw_gbps'] > 0]
                
                stats[gpu_count] = {
                    'count': len(data),
                    'avg_comm_us': sum(comm_times) / len(comm_times) if comm_times else 0,
                    'avg_bus_bw_gbps': sum(bus_bws) / len(bus_bws) if bus_bws else 0,
                }
        
        return {
            'status': 'success',
            'total_rows': len(extreme),
            'by_gpu_count': stats,
        }
    
    def analyze_algorithm_comparison(self) -> Dict[str, Any]:
        """Analyze algorithm comparison (Tree vs Ring vs Hierarchical)"""
        algo_tests = [d for d in self.data if 'algorithm' in d['filename'].lower() or 'tree' in d['filename'].lower()]
        
        if not algo_tests:
            return {'status': 'No data', 'data': []}
        
        # Group by algorithm type (extract from filename or layer name)
        by_algo = defaultdict(list)
        for d in algo_tests:
            # Try to extract algorithm from filename
            filename_lower = d['filename'].lower()
            if 'ring' in filename_lower:
                by_algo['RING'].append(d)
            elif 'tree' in filename_lower:
                by_algo['TREE'].append(d)
            elif 'hierarchical' in filename_lower:
                by_algo['HIERARCHICAL'].append(d)
            else:
                by_algo['UNKNOWN'].append(d)
        
        # Calculate statistics for each algorithm
        stats = {}
        for algo, data in by_algo.items():
            if data:
                comm_times = [d['total_comm_us'] for d in data if d['total_comm_us'] > 0]
                bus_bws = [d['bus_bw_gbps'] for d in data if d['bus_bw_gbps'] > 0]
                
                stats[algo] = {
                    'count': len(data),
                    'avg_comm_us': sum(comm_times) / len(comm_times) if comm_times else 0,
                    'avg_bus_bw_gbps': sum(bus_bws) / len(bus_bws) if bus_bws else 0,
                }
        
        return {
            'status': 'success',
            'total_rows': len(algo_tests),
            'by_algorithm': stats,
            'performance_ranking': sorted(
                [(algo, s['avg_comm_us']) for algo, s in stats.items()],
                key=lambda x: x[1]
            )
        }
    
    def analyze_ratio_impact(self) -> Dict[str, Any]:
        """Analyze Ratio table impact (AllGather vs AllReduce)"""
        ratio_tests = [d for d in self.data if 'ratio' in d['filename'].lower()]
        
        if not ratio_tests:
            return {'status': 'No data', 'data': []}
        
        # Group by operation type
        by_op = defaultdict(list)
        for d in ratio_tests:
            layer_name = d['layer_name'].lower()
            if 'allgather' in layer_name:
                by_op['ALLGATHER'].append(d)
            elif 'allreduce' in layer_name:
                by_op['ALLREDUCE'].append(d)
        
        # Calculate statistics
        stats = {}
        for op, data in by_op.items():
            if data:
                comm_times = [d['total_comm_us'] for d in data if d['total_comm_us'] > 0]
                bus_bws = [d['bus_bw_gbps'] for d in data if d['bus_bw_gbps'] > 0]
                
                stats[op] = {
                    'count': len(data),
                    'avg_comm_us': sum(comm_times) / len(comm_times) if comm_times else 0,
                    'avg_bus_bw_gbps': sum(bus_bws) / len(bus_bws) if bus_bws else 0,
                }
        
        # Calculate Ratio impact
        if 'ALLGATHER' in stats and 'ALLREDUCE' in stats:
            allgather_bw = stats['ALLGATHER']['avg_bus_bw_gbps']
            allreduce_bw = stats['ALLREDUCE']['avg_bus_bw_gbps']
            
            if allgather_bw > 0 and allreduce_bw > 0:
                ratio_impact_pct = ((allreduce_bw - allgather_bw) / allreduce_bw) * 100
                stats['RATIO_IMPACT'] = {
                    'allgather_bw_gbps': allgather_bw,
                    'allreduce_bw_gbps': allreduce_bw,
                    'bandwidth_reduction_pct': ratio_impact_pct,
                }
        
        return {
            'status': 'success',
            'total_rows': len(ratio_tests),
            'by_operation': stats,
        }
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive Phase 4 analysis report"""
        return {
            'summary': {
                'total_data_rows': len(self.data),
                'analysis_timestamp': '2026-02-18',
            },
            'mixed_collective_ops': self.analyze_mixed_collective_ops(),
            'parameter_sensitivity': self.analyze_parameter_sensitivity(),
            'extreme_scale': self.analyze_extreme_scale(),
            'algorithm_comparison': self.analyze_algorithm_comparison(),
            'ratio_impact': self.analyze_ratio_impact(),
        }
    
    def save_report(self, report: Dict[str, Any], output_path: str):
        """Save report to JSON file"""
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"✅ Report saved to {output_path}")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python phase4_analyzer.py <results_dir>")
        print("Example: python phase4_analyzer.py /Users/erlengzi/.openclaw/workspace/simai-practice/results")
        sys.exit(1)
    
    results_dir = sys.argv[1]
    analyzer = Phase4Analyzer(results_dir)
    
    # Load all data
    analyzer.load_all_data()
    
    if not analyzer.data:
        print("❌ No data found. Please run Phase 4 workloads first.")
        sys.exit(1)
    
    # Generate comprehensive report
    report = analyzer.generate_comprehensive_report()
    
    # Save to JSON
    output_json = os.path.join(results_dir, "phase4_analysis_report.json")
    analyzer.save_report(report, output_json)
    
    # Print summary
    print("\n" + "="*60)
    print("Phase 4 Analysis Summary")
    print("="*60)
    print(f"Total data rows: {report['summary']['total_data_rows']}")
    print(f"\nMixed collective ops: {report['mixed_collective_ops']['status']}")
    print(f"Parameter sensitivity: {report['parameter_sensitivity']['status']}")
    print(f"Extreme scale: {report['extreme_scale']['status']}")
    print(f"Algorithm comparison: {report['algorithm_comparison']['status']}")
    print(f"Ratio impact: {report['ratio_impact']['status']}")
    print("="*60)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Phase 4 Deep Analysis Tool - Enhanced and Fixed Version
Fixed parsing issues with infinite values
"""

import csv
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any
from collections import defaultdict

class Phase4AnalyzerFixed:
    """Phase 4 workload analyzer - fixed version"""
    
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.data = []
        
    def find_all_csv_files(self) -> List[Path]:
        """Find all CSV files in the entire directory tree"""
        return list(self.base_dir.rglob("*.csv"))
    
    def parse_csv_file(self, csv_path: Path) -> List[Dict[str, Any]]:
        """Parse a single CSV file and extract metrics"""
        results = []
        
        try:
            with open(csv_path, 'r') as f:
                reader = csv.reader(f)
                rows = list(reader)
                
            if len(rows) < 4:
                return []
            
            # Parse rows starting from row 3 (0-indexed)
            for i, row in enumerate(rows[3:], start=3):
                if len(row) < 11:
                    continue
                    
                try:
                    # Parse with better error handling
                    fwd_comm = self.safe_float(row[5]) if len(row) > 5 else 0.0
                    bwd_comm = self.safe_float(row[7]) if len(row) > 7 else 0.0
                    total_comm = self.safe_float(row[8]) if len(row) > 8 else 0.0
                    alg_bw = self.safe_float(row[9]) if len(row) > 9 else 0.0
                    bus_bw = self.safe_float(row[10]) if len(row) > 10 else 0.0
                    
                    # Skip rows with invalid data
                    if total_comm <= 0 or total_comm > 1e10:  # Filter out invalid values
                        continue
                    
                    result = {
                        'file': str(csv_path),
                        'filename': csv_path.stem,
                        'row_index': i,
                        'layer_name': row[0] if len(row) > 0 else '',
                        'fwd_comm_us': fwd_comm,
                        'bwd_comm_us': bwd_comm,
                        'total_comm_us': total_comm,
                        'fwd_alg_bw_gbps': alg_bw,
                        'bus_bw_gbps': bus_bw,
                    }
                    
                    # Calculate efficiency
                    if bus_bw > 0 and bus_bw < 1e6:  # Valid bus_bw
                        theoretical_max = 240.0
                        result['efficiency_pct'] = (bus_bw / theoretical_max) * 100
                    
                    results.append(result)
                    
                except (ValueError, IndexError) as e:
                    continue
                    
        except Exception as e:
            pass
            
        return results
    
    def safe_float(self, value: str) -> float:
        """Safely convert string to float, return 0 for invalid values"""
        try:
            f = float(value)
            # Filter out extreme values
            if f < 0 or f > 1e10:
                return 0.0
            return f
        except (ValueError, TypeError):
            return 0.0
    
    def load_all_data(self):
        """Load and parse all CSV files"""
        csv_files = self.find_all_csv_files()
        print(f"📁 Found {len(csv_files)} CSV files")
        
        all_results = []
        for csv_path in csv_files:
            results = self.parse_csv_file(csv_path)
            all_results.extend(results)
        
        self.data = all_results
        print(f"✅ Loaded {len(all_results)} valid data rows")
        return all_results
    
    def analyze_collective_ops(self) -> Dict[str, Any]:
        """Analyze collective operations"""
        by_op = defaultdict(list)
        
        for d in self.data:
            layer_name = d['layer_name'].lower()
            if 'allreduce' in layer_name:
                by_op['ALLREDUCE'].append(d)
            elif 'allgather' in layer_name:
                by_op['ALLGATHER'].append(d)
            elif 'reducescatter' in layer_name:
                by_op['REDUCESCATTER'].append(d)
            elif 'alltoall' in layer_name:
                by_op['ALLTOALL'].append(d)
        
        stats = {}
        for op, data in by_op.items():
            if data:
                comm_times = [d['total_comm_us'] for d in data if d['total_comm_us'] > 0]
                bus_bws = [d['bus_bw_gbps'] for d in data if d['bus_bw_gbps'] > 0 and d['bus_bw_gbps'] < 1e6]
                
                stats[op] = {
                    'count': len(data),
                    'avg_comm_us': sum(comm_times) / len(comm_times) if comm_times else 0,
                    'avg_bus_bw_gbps': sum(bus_bws) / len(bus_bws) if bus_bws else 0,
                }
        
        ranking = sorted([(op, s['avg_comm_us']) for op, s in stats.items() if s['avg_comm_us'] > 0], key=lambda x: x[1])
        
        return {
            'status': 'success' if stats else 'No data',
            'total_rows': sum(len(data) for data in by_op.values()),
            'by_operation': stats,
            'performance_ranking': ranking,
        }
    
    def analyze_gpu_scaling(self) -> Dict[str, Any]:
        """Analyze GPU scaling"""
        by_gpu = defaultdict(list)
        
        for d in self.data:
            filename_lower = d['filename'].lower()
            import re
            match = re.search(r'gpu[_-]?(\d+)', filename_lower)
            if match:
                gpu_count = int(match.group(1))
                by_gpu[gpu_count].append(d)
        
        stats = {}
        for gpu_count, data in sorted(by_gpu.items()):
            if data:
                comm_times = [d['total_comm_us'] for d in data if 0 < d['total_comm_us'] < 1e10]
                bus_bws = [d['bus_bw_gbps'] for d in data if 0 < d['bus_bw_gbps'] < 1e6]
                
                if comm_times and bus_bws:
                    stats[gpu_count] = {
                        'count': len(data),
                        'avg_comm_us': sum(comm_times) / len(comm_times),
                        'avg_bus_bw_gbps': sum(bus_bws) / len(bus_bws),
                    }
        
        return {
            'status': 'success' if stats else 'No data',
            'total_rows': len([d for d in self.data]),
            'by_gpu_count': stats,
        }
    
    def analyze_algorithms(self) -> Dict[str, Any]:
        """Analyze algorithm comparison"""
        by_algo = defaultdict(list)
        
        for d in self.data:
            filename_lower = d['filename'].lower()
            if 'nvls' in filename_lower or 'h100' in filename_lower:
                by_algo['NVLS_H100'].append(d)
            elif 'ring' in filename_lower and 'nvls' not in filename_lower:
                by_algo['RING'].append(d)
        
        stats = {}
        for algo, data in by_algo.items():
            if data:
                comm_times = [d['total_comm_us'] for d in data if 0 < d['total_comm_us'] < 1e10]
                bus_bws = [d['bus_bw_gbps'] for d in data if 0 < d['bus_bw_gbps'] < 1e6]
                
                if comm_times and bus_bws:
                    stats[algo] = {
                        'count': len(data),
                        'avg_comm_us': sum(comm_times) / len(comm_times),
                        'avg_bus_bw_gbps': sum(bus_bws) / len(bus_bws),
                    }
        
        return {
            'status': 'success' if stats else 'No data',
            'by_algorithm': stats,
        }
    
    def analyze_ratio_impact(self) -> Dict[str, Any]:
        """Analyze Ratio table impact"""
        allgather_data = [d for d in self.data if 'allgather' in d['layer_name'].lower()]
        allreduce_data = [d for d in self.data if 'allreduce' in d['layer_name'].lower()]
        
        if not allgather_data or not allreduce_data:
            return {'status': 'Insufficient data'}
        
        allgather_bw = [d['bus_bw_gbps'] for d in allgather_data if 0 < d['bus_bw_gbps'] < 1e6]
        allreduce_bw = [d['bus_bw_gbps'] for d in allreduce_data if 0 < d['bus_bw_gbps'] < 1e6]
        
        if not allgather_bw or not allreduce_bw:
            return {'status': 'No valid bandwidth data'}
        
        avg_allgather_bw = sum(allgather_bw) / len(allgather_bw)
        avg_allreduce_bw = sum(allreduce_bw) / len(allreduce_bw)
        
        ratio_impact = 0
        if avg_allreduce_bw > 0 and avg_allgather_bw > 0:
            ratio_impact = ((avg_allreduce_bw - avg_allgather_bw) / avg_allreduce_bw) * 100
        
        return {
            'status': 'success',
            'allgather': {
                'count': len(allgather_data),
                'avg_bus_bw_gbps': avg_allgather_bw,
            },
            'allreduce': {
                'count': len(allreduce_data),
                'avg_bus_bw_gbps': avg_allreduce_bw,
            },
            'ratio_impact_pct': ratio_impact,
        }
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive Phase 4 analysis report"""
        return {
            'summary': {
                'total_data_rows': len(self.data),
                'analysis_timestamp': '2026-02-18',
            },
            'collective_ops': self.analyze_collective_ops(),
            'gpu_scaling': self.analyze_gpu_scaling(),
            'algorithms': self.analyze_algorithms(),
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
        print("Usage: python phase4_analyzer_fixed.py <base_dir>")
        sys.exit(1)
    
    base_dir = sys.argv[1]
    analyzer = Phase4AnalyzerFixed(base_dir)
    
    # Load all data
    analyzer.load_all_data()
    
    if not analyzer.data:
        print("❌ No data found.")
        sys.exit(1)
    
    # Generate comprehensive report
    report = analyzer.generate_comprehensive_report()
    
    # Save to JSON
    output_json = os.path.join(base_dir, "phase4_analysis_report_final.json")
    analyzer.save_report(report, output_json)
    
    # Print summary
    print("\n" + "="*70)
    print("Phase 4 Analysis Summary (Final - Fixed)")
    print("="*70)
    print(f"Total data rows: {report['summary']['total_data_rows']}")
    
    print(f"\n【Collective Operations】: {report['collective_ops']['status']}")
    if report['collective_ops']['status'] == 'success':
        print(f"  Operations: {', '.join(report['collective_ops']['by_operation'].keys())}")
        print(f"  Performance ranking:")
        for op, time_us in report['collective_ops']['performance_ranking']:
            print(f"    {op}: {time_us:.2f} μs")
    
    print(f"\n【GPU Scaling】: {report['gpu_scaling']['status']}")
    if report['gpu_scaling']['status'] == 'success':
        print(f"  GPU counts: {list(report['gpu_scaling']['by_gpu_count'].keys())}")
    
    print(f"\n【Algorithms】: {report['algorithms']['status']}")
    if report['algorithms']['status'] == 'success':
        print(f"  Algorithms: {list(report['algorithms']['by_algorithm'].keys())}")
        for algo, stats in report['algorithms']['by_algorithm'].items():
            print(f"    {algo}: {stats['avg_comm_us']:.2f} μs, {stats['avg_bus_bw_gbps']:.2f} GB/s")
    
    print(f"\n【Ratio Impact】: {report['ratio_impact']['status']}")
    if report['ratio_impact']['status'] == 'success':
        print(f"  AllGather BW: {report['ratio_impact']['allgather']['avg_bus_bw_gbps']:.2f} GB/s")
        print(f"  AllReduce BW: {report['ratio_impact']['allreduce']['avg_bus_bw_gbps']:.2f} GB/s")
        print(f"  Bandwidth reduction: {report['ratio_impact']['ratio_impact_pct']:.2f}%")
    
    print("="*70)


if __name__ == "__main__":
    main()

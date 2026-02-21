#!/usr/bin/env python3
"""
Phase 4 Deep Analysis Tool - Enhanced Version
Supports analyzing ALL CSV files in the SimAI directory structure
"""

import csv
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any
from collections import defaultdict

class Phase4AnalyzerEnhanced:
    """Phase 4 workload analyzer - enhanced to find all CSV files"""
    
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.data = []
        
    def find_all_csv_files(self) -> List[Path]:
        """Find all CSV files in the entire directory tree"""
        # Search recursively in all subdirectories
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
                    result = {
                        'file': str(csv_path),
                        'filename': csv_path.stem,
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
                        theoretical_max = 240.0  # A100 theoretical max
                        result['efficiency_pct'] = (result['bus_bw_gbps'] / theoretical_max) * 100
                    
                    results.append(result)
                    
                except (ValueError, IndexError) as e:
                    continue
                    
        except Exception as e:
            pass
            
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
    
    def analyze_gpu_scaling(self) -> Dict[str, Any]:
        """Analyze GPU scaling (Priority 1)"""
        # Extract GPU count from filename
        by_gpu = defaultdict(list)
        
        for d in self.data:
            filename_lower = d['filename'].lower()
            # Extract GPU count from filename
            for gpu_count in [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024]:
                if f'gpu{gpu_count}' in filename_lower or f'{gpu_count}gpu' in filename_lower:
                    by_gpu[gpu_count].append(d)
                    break
            else:
                # Try to match patterns like "gpu_16", "gpu16", etc.
                import re
                match = re.search(r'gpu[_-]?(\d+)', filename_lower)
                if match:
                    gpu_count = int(match.group(1))
                    by_gpu[gpu_count].append(d)
        
        # Calculate statistics for each GPU count
        stats = {}
        for gpu_count, data in sorted(by_gpu.items()):
            if data:
                comm_times = [d['total_comm_us'] for d in data if d['total_comm_us'] > 0]
                bus_bws = [d['bus_bw_gbps'] for d in data if d['bus_bw_gbps'] > 0]
                
                stats[gpu_count] = {
                    'count': len(data),
                    'avg_comm_us': sum(comm_times) / len(comm_times) if comm_times else 0,
                    'min_comm_us': min(comm_times) if comm_times else 0,
                    'max_comm_us': max(comm_times) if comm_times else 0,
                    'avg_bus_bw_gbps': sum(bus_bws) / len(bus_bws) if bus_bws else 0,
                }
        
        return {
            'status': 'success' if stats else 'No data',
            'total_rows': len([d for d in self.data if any(str(g) in d['filename'].lower() for g in by_gpu.keys())]),
            'by_gpu_count': stats,
        }
    
    def analyze_collective_ops(self) -> Dict[str, Any]:
        """Analyze collective operations (Priority 1)"""
        # Group by operation type
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
        
        # Calculate statistics for each operation
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
        
        # Performance ranking
        ranking = sorted([(op, s['avg_comm_us']) for op, s in stats.items() if s['avg_comm_us'] > 0], key=lambda x: x[1])
        
        return {
            'status': 'success' if stats else 'No data',
            'total_rows': sum(len(data) for data in by_op.values()),
            'by_operation': stats,
            'performance_ranking': ranking,
        }
    
    def analyze_ratio_impact(self) -> Dict[str, Any]:
        """Analyze Ratio table impact (Priority 4)"""
        # Compare AllGather (with Ratio) vs AllReduce (without Ratio)
        allgather_data = [d for d in self.data if 'allgather' in d['layer_name'].lower()]
        allreduce_data = [d for d in self.data if 'allreduce' in d['layer_name'].lower()]
        
        if not allgather_data or not allreduce_data:
            return {'status': 'Insufficient data'}
        
        # Calculate statistics
        allgather_bw = [d['bus_bw_gbps'] for d in allgather_data if d['bus_bw_gbps'] > 0]
        allreduce_bw = [d['bus_bw_gbps'] for d in allreduce_data if d['bus_bw_gbps'] > 0]
        
        avg_allgather_bw = sum(allgather_bw) / len(allgather_bw) if allgather_bw else 0
        avg_allreduce_bw = sum(allreduce_bw) / len(allreduce_bw) if allreduce_bw else 0
        
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
    
    def analyze_algorithms(self) -> Dict[str, Any]:
        """Analyze algorithm comparison (Priority 3)"""
        # Group by algorithm (extract from filename or layer name)
        by_algo = defaultdict(list)
        
        for d in self.data:
            filename_lower = d['filename'].lower()
            if 'ring' in filename_lower or 'ring' in d['layer_name'].lower():
                by_algo['RING'].append(d)
            elif 'tree' in filename_lower or 'tree' in d['layer_name'].lower():
                by_algo['TREE'].append(d)
            elif 'nvls' in filename_lower or 'h100' in filename_lower:
                by_algo['NVLS_H100'].append(d)
            else:
                by_algo['UNKNOWN'].append(d)
        
        # Calculate statistics
        stats = {}
        for algo, data in by_algo.items():
            if algo != 'UNKNOWN' and data:
                comm_times = [d['total_comm_us'] for d in data if d['total_comm_us'] > 0]
                bus_bws = [d['bus_bw_gbps'] for d in data if d['bus_bw_gbps'] > 0]
                
                stats[algo] = {
                    'count': len(data),
                    'avg_comm_us': sum(comm_times) / len(comm_times) if comm_times else 0,
                    'avg_bus_bw_gbps': sum(bus_bws) / len(bus_bws) if bus_bws else 0,
                }
        
        return {
            'status': 'success' if stats else 'No data',
            'by_algorithm': stats,
        }
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive Phase 4 analysis report"""
        return {
            'summary': {
                'total_data_rows': len(self.data),
                'analysis_timestamp': '2026-02-18',
            },
            'gpu_scaling': self.analyze_gpu_scaling(),
            'collective_ops': self.analyze_collective_ops(),
            'ratio_impact': self.analyze_ratio_impact(),
            'algorithms': self.analyze_algorithms(),
        }
    
    def save_report(self, report: Dict[str, Any], output_path: str):
        """Save report to JSON file"""
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"✅ Report saved to {output_path}")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python phase4_analyzer_enhanced.py <base_dir>")
        print("Example: python phase4_analyzer_enhanced.py /Users/erlengzi/.openclaw/workspace/simai-practice")
        sys.exit(1)
    
    base_dir = sys.argv[1]
    analyzer = Phase4AnalyzerEnhanced(base_dir)
    
    # Load all data
    analyzer.load_all_data()
    
    if not analyzer.data:
        print("❌ No data found.")
        sys.exit(1)
    
    # Generate comprehensive report
    report = analyzer.generate_comprehensive_report()
    
    # Save to JSON
    output_json = os.path.join(base_dir, "phase4_analysis_report_enhanced.json")
    analyzer.save_report(report, output_json)
    
    # Print summary
    print("\n" + "="*60)
    print("Phase 4 Analysis Summary (Enhanced)")
    print("="*60)
    print(f"Total data rows: {report['summary']['total_data_rows']}")
    print(f"\nGPU Scaling: {report['gpu_scaling']['status']}")
    if report['gpu_scaling']['status'] == 'success':
        print(f"  GPU counts analyzed: {len(report['gpu_scaling']['by_gpu_count'])}")
    print(f"\nCollective Ops: {report['collective_ops']['status']}")
    if report['collective_ops']['status'] == 'success':
        print(f"  Operations analyzed: {len(report['collective_ops']['by_operation'])}")
    print(f"\nRatio Impact: {report['ratio_impact']['status']}")
    if report['ratio_impact']['status'] == 'success':
        print(f"  Bandwidth reduction: {report['ratio_impact']['ratio_impact_pct']:.2f}%")
    print(f"\nAlgorithms: {report['algorithms']['status']}")
    if report['algorithms']['status'] == 'success':
        print(f"  Algorithms analyzed: {len(report['algorithms']['by_algorithm'])}")
    print("="*60)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
高级示例：GPT-3训练仿真
"""

from simai_tools.framework.priorityM_automated_workflow_v2 import PriorityMAutomatedWorkflowV2

def main():
    print("GPT-3训练仿真...")

    workflow = PriorityMAutomatedWorkflowV2()

    # 运行GPT-3训练仿真
    result = workflow.run_workflow(
        num_gpus=1024,
        data_size_mb=1024,  # 1GB参数梯度
        collective_op="allreduce",
        algorithm="hierarchical"
    )

    print(f"\n预估时间: {{result['time_ms']}} ms")
    print(f"吞吐量: {{result['throughput_gb_s']}} GB/s")
    print(f"扩展效率: {{result['efficiency'] * 100}}%")

    # 生成报告
    workflow.generate_report(result, "examples/advanced/gpt3_report.md")

if __name__ == "__main__":
    main()

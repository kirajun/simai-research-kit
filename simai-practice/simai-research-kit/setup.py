from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="simai-research-kit",
    version="1.0.0",
    author="二愣子",
    author_email="your.email@example.com",
    description="SimAI深度研究工具集 - GPU集群集合通信性能仿真与分析套件",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/simai-research-kit",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "simai-gen=simai_tools.workload.advanced_workload_generator:main",
            "simai-analyze=simai_tools.analysis.performance_analyzer:main",
            "simai-compare=simai_tools.algorithm.algorithm_comparison_analysis:main",
        ],
    },
)

"""
Veyra Benchmark Suite

Seven benchmark families designed to measure capabilities in
post-super-intelligence interplanetary contexts.
"""

from veyra.benchmarks.base import Benchmark, BenchmarkResult, BenchmarkFamily
from veyra.benchmarks.runner import BenchmarkRunner
from veyra.benchmarks.cplc import CPLCBenchmark

__all__ = [
    "Benchmark",
    "BenchmarkResult",
    "BenchmarkFamily",
    "BenchmarkRunner",
    "CPLCBenchmark",
]


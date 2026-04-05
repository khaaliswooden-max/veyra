"""
Veyra Benchmark Suite

Seven benchmark families designed to measure capabilities in
post-super-intelligence interplanetary contexts.
"""

from veyra.benchmarks.base import Benchmark, BenchmarkFamily, BenchmarkResult
from veyra.benchmarks.cplc import CPLCBenchmark
from veyra.benchmarks.runner import BenchmarkRunner

__all__ = [
    "Benchmark",
    "BenchmarkResult",
    "BenchmarkFamily",
    "BenchmarkRunner",
    "CPLCBenchmark",
]

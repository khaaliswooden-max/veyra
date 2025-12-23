"""
Benchmark Runner

Executes benchmarks and aggregates results.
"""

import asyncio
import time
from datetime import datetime
from typing import Optional

from veyra.core import VeyraCore
from veyra.benchmarks.base import (
    Benchmark,
    BenchmarkFamily,
    BenchmarkResult,
    BenchmarkSuiteResult,
    BenchmarkTask,
    Difficulty,
)
from veyra.benchmarks.cplc import CPLCBenchmark


# Registry of benchmark implementations
BENCHMARK_REGISTRY: dict[BenchmarkFamily, type[Benchmark]] = {
    BenchmarkFamily.CPLC: CPLCBenchmark,
}


class BenchmarkRunner:
    """
    Runs benchmarks against a Veyra instance.

    Handles task generation, execution, scoring, and result aggregation.
    """

    # V-Score weights for each benchmark family
    V_SCORE_WEIGHTS = {
        BenchmarkFamily.CPLC: 0.20,
        BenchmarkFamily.MSGA: 0.15,
        BenchmarkFamily.WMRT: 0.15,
        BenchmarkFamily.ICSD: 0.10,
        BenchmarkFamily.TOME: 0.15,
        BenchmarkFamily.ASR: 0.15,
        BenchmarkFamily.IMDP: 0.10,
    }

    def __init__(self, veyra: VeyraCore):
        """
        Initialize benchmark runner.

        Args:
            veyra: VeyraCore instance to benchmark
        """
        self.veyra = veyra
        self._benchmarks: dict[BenchmarkFamily, Benchmark] = {}

    def _get_benchmark(self, family: BenchmarkFamily) -> Benchmark:
        """Get or create a benchmark instance."""
        if family not in self._benchmarks:
            benchmark_class = BENCHMARK_REGISTRY.get(family)
            if not benchmark_class:
                raise ValueError(f"Benchmark not implemented: {family.value}")
            self._benchmarks[family] = benchmark_class()
        return self._benchmarks[family]

    async def run_family(
        self,
        family: BenchmarkFamily,
        count: int = 10,
        difficulty: Difficulty = Difficulty.MEDIUM,
    ) -> BenchmarkSuiteResult:
        """
        Run a single benchmark family.

        Args:
            family: Benchmark family to run
            count: Number of tasks to run
            difficulty: Difficulty level

        Returns:
            BenchmarkSuiteResult with scores
        """
        benchmark = self._get_benchmark(family)
        tasks = benchmark.generate_tasks(count=count, difficulty=difficulty)

        results = []
        start_time = time.time()

        for task in tasks:
            result = await self._run_task(benchmark, task)
            results.append(result)

        total_time = time.time() - start_time

        # Aggregate results
        passed = sum(1 for r in results if r.success)
        failed = len(results) - passed
        avg_score = sum(r.score for r in results) / len(results) if results else 0.0

        return BenchmarkSuiteResult(
            family=family,
            total_tasks=len(results),
            passed_tasks=passed,
            failed_tasks=failed,
            v_score=avg_score,  # For single family, v_score = avg score
            family_scores={family.value: avg_score},
            total_time_seconds=total_time,
            results=results,
        )

    async def _run_task(
        self,
        benchmark: Benchmark,
        task: BenchmarkTask,
    ) -> BenchmarkResult:
        """Run a single benchmark task."""
        start_time = time.time()

        try:
            result = await self.veyra.execute_async(task.prompt)
            execution_time = time.time() - start_time

            if result.success:
                return benchmark.score_result(
                    task=task,
                    output=result.content,
                    execution_time=execution_time,
                )
            else:
                return BenchmarkResult(
                    task_id=task.task_id,
                    family=benchmark.family,
                    success=False,
                    score=0.0,
                    execution_time_seconds=execution_time,
                    errors=[result.error or "Unknown error"],
                    model_backend=self.veyra.config.model.backend,
                )

        except Exception as e:
            execution_time = time.time() - start_time
            return BenchmarkResult(
                task_id=task.task_id,
                family=benchmark.family,
                success=False,
                score=0.0,
                execution_time_seconds=execution_time,
                errors=[str(e)],
                model_backend=self.veyra.config.model.backend,
            )

    async def run_all(
        self,
        count_per_family: int = 10,
        difficulty: Difficulty = Difficulty.MEDIUM,
        families: Optional[list[BenchmarkFamily]] = None,
    ) -> BenchmarkSuiteResult:
        """
        Run the full benchmark suite.

        Args:
            count_per_family: Number of tasks per family
            difficulty: Difficulty level
            families: Optional list of families to run (default: all implemented)

        Returns:
            BenchmarkSuiteResult with V-Score
        """
        if families is None:
            families = list(BENCHMARK_REGISTRY.keys())

        all_results = []
        family_scores = {}
        start_time = time.time()

        for family in families:
            try:
                suite_result = await self.run_family(
                    family=family,
                    count=count_per_family,
                    difficulty=difficulty,
                )
                all_results.extend(suite_result.results)
                family_scores[family.value] = suite_result.v_score
            except ValueError:
                # Benchmark not implemented, skip
                continue

        total_time = time.time() - start_time

        # Calculate V-Score (weighted average of family scores)
        v_score = 0.0
        total_weight = 0.0
        for family_name, score in family_scores.items():
            family = BenchmarkFamily(family_name)
            weight = self.V_SCORE_WEIGHTS.get(family, 0.1)
            v_score += score * weight
            total_weight += weight

        if total_weight > 0:
            v_score /= total_weight

        # Aggregate
        passed = sum(1 for r in all_results if r.success)

        return BenchmarkSuiteResult(
            family=None,  # Full suite
            total_tasks=len(all_results),
            passed_tasks=passed,
            failed_tasks=len(all_results) - passed,
            v_score=v_score,
            family_scores=family_scores,
            total_time_seconds=total_time,
            results=all_results,
        )


def list_benchmarks() -> list[str]:
    """List available benchmark families."""
    return [f.value for f in BENCHMARK_REGISTRY.keys()]

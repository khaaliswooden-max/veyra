"""
Tests for Benchmark Framework
"""

import pytest

from veyra import VeyraCore
from veyra.benchmarks import (
    BenchmarkFamily,
    BenchmarkRunner,
    CPLCBenchmark,
)
from veyra.benchmarks.base import BenchmarkTask, Difficulty


class TestCPLCBenchmark:
    """Test CPLC Benchmark functionality."""

    def test_generate_tasks(self):
        """Test task generation."""
        benchmark = CPLCBenchmark()
        tasks = benchmark.generate_tasks(count=5, difficulty=Difficulty.MEDIUM)

        assert len(tasks) == 5
        for task in tasks:
            assert task.family == BenchmarkFamily.CPLC
            assert task.difficulty == Difficulty.MEDIUM
            assert len(task.prompt) > 0

    def test_generate_tasks_easy(self):
        """Test easy difficulty tasks."""
        benchmark = CPLCBenchmark()
        tasks = benchmark.generate_tasks(count=3, difficulty=Difficulty.EASY)

        assert all(t.difficulty == Difficulty.EASY for t in tasks)

    def test_generate_tasks_hard(self):
        """Test hard difficulty tasks."""
        benchmark = CPLCBenchmark()
        tasks = benchmark.generate_tasks(count=3, difficulty=Difficulty.HARD)

        assert all(t.difficulty == Difficulty.HARD for t in tasks)

    def test_score_result_good(self):
        """Test scoring a good response."""
        benchmark = CPLCBenchmark()
        task = benchmark.generate_tasks(count=1)[0]

        # Simulated good response
        good_output = """
        ## Current State Assessment (85% confidence)
        Given the 10-minute communication delay, I estimate the current state...

        ## Recommended Actions
        1. Step 1: Implement monitoring (Priority: High)
        2. Step 2: Execute backup protocol

        ## Contingency Plans
        If the primary system fails, alternatively we should...

        ## Information Requests
        - Request updated sensor data
        """

        result = benchmark.score_result(task, good_output, execution_time=5.0)

        assert result.success
        assert result.score > 0.5
        assert result.task_id == task.task_id

    def test_score_result_poor(self):
        """Test scoring a poor response."""
        benchmark = CPLCBenchmark()
        task = benchmark.generate_tasks(count=1)[0]

        # Poor response that doesn't acknowledge delay
        poor_output = "Just do it now."

        result = benchmark.score_result(task, poor_output, execution_time=1.0)

        assert not result.success
        assert result.score < 0.5
        assert len(result.errors) > 0


class TestBenchmarkRunner:
    """Test BenchmarkRunner functionality."""

    @pytest.mark.asyncio
    async def test_run_family(self):
        """Test running a benchmark family."""
        veyra = VeyraCore()
        runner = BenchmarkRunner(veyra)

        result = await runner.run_family(
            family=BenchmarkFamily.CPLC,
            count=3,
            difficulty=Difficulty.EASY,
        )

        assert result.total_tasks == 3
        assert result.passed_tasks + result.failed_tasks == 3
        assert 0.0 <= result.v_score <= 1.0

    @pytest.mark.asyncio
    async def test_run_all(self):
        """Test running all benchmarks."""
        veyra = VeyraCore()
        runner = BenchmarkRunner(veyra)

        result = await runner.run_all(
            count_per_family=2,
            difficulty=Difficulty.EASY,
        )

        assert result.total_tasks >= 2
        assert 0.0 <= result.v_score <= 1.0
        assert len(result.family_scores) > 0


class TestBenchmarkTask:
    """Test BenchmarkTask functionality."""

    def test_task_creation(self):
        """Test task creation."""
        task = BenchmarkTask(
            family=BenchmarkFamily.CPLC,
            difficulty=Difficulty.MEDIUM,
            prompt="Test prompt",
        )

        assert task.task_id is not None
        assert task.family == BenchmarkFamily.CPLC
        assert task.prompt == "Test prompt"

    def test_task_defaults(self):
        """Test task default values."""
        task = BenchmarkTask()

        assert task.max_time_seconds == 300.0
        assert task.max_tokens == 4096

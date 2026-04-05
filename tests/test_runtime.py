"""
Tests for Runtime Module - Latency and Scheduler
"""

import asyncio
from datetime import UTC, datetime

import pytest

from veyra.runtime import (
    LatencySimulator,
    Task,
    TaskScheduler,
    TaskStatus,
    calculate_mars_delay,
)
from veyra.runtime.latency import (
    ORBITAL_DISTANCES,
    SPEED_OF_LIGHT_AU_PER_SEC,
    OrbitalPosition,
    Planet,
    calculate_light_delay,
)
from veyra.runtime.scheduler import TaskPriority


class TestPlanet:
    """Test Planet enum."""

    def test_planet_values(self):
        """Test planet enum values."""
        assert Planet.EARTH.value == "earth"
        assert Planet.MARS.value == "mars"
        assert Planet.MOON.value == "moon"
        assert Planet.JUPITER.value == "jupiter"


class TestOrbitalPosition:
    """Test OrbitalPosition dataclass."""

    def test_create_position(self):
        """Test creating orbital position."""
        position = OrbitalPosition(
            planet=Planet.MARS,
            timestamp=datetime.now(UTC),
            distance_au=1.524,
        )

        assert position.planet == Planet.MARS
        assert position.distance_au == 1.524


class TestLatencyCalculations:
    """Test latency calculation functions."""

    def test_calculate_light_delay(self):
        """Test light delay calculation."""
        # 1 AU should take ~499 seconds (8.3 minutes)
        delay = calculate_light_delay(1.0)
        expected = 1.0 / SPEED_OF_LIGHT_AU_PER_SEC
        assert delay == pytest.approx(expected)

    def test_calculate_mars_delay_normal(self):
        """Test Mars delay calculation without conjunction."""
        delay = calculate_mars_delay()
        # Should be positive and reasonable
        assert delay > 0
        assert delay < 2000  # Less than ~33 minutes

    def test_calculate_mars_delay_conjunction(self):
        """Test Mars delay during conjunction (max distance)."""
        delay = calculate_mars_delay(conjunction=True)
        # Conjunction should have longer delay
        normal_delay = calculate_mars_delay(conjunction=False)
        assert delay > normal_delay

    def test_orbital_distances_exist(self):
        """Test orbital distances are defined."""
        assert Planet.EARTH in ORBITAL_DISTANCES
        assert Planet.MARS in ORBITAL_DISTANCES
        assert Planet.MOON in ORBITAL_DISTANCES
        assert Planet.JUPITER in ORBITAL_DISTANCES


class TestLatencySimulator:
    """Test LatencySimulator class."""

    def test_init_default(self):
        """Test default initialization."""
        sim = LatencySimulator()
        assert sim.target == Planet.MARS
        assert sim.use_realistic_variance is True
        assert sim.time_acceleration == 1.0

    def test_init_custom_target(self):
        """Test custom target initialization."""
        sim = LatencySimulator(target=Planet.MOON)
        assert sim.target == Planet.MOON

    def test_get_current_delay_moon(self):
        """Test Moon delay."""
        sim = LatencySimulator(
            target=Planet.MOON,
            use_realistic_variance=False,
        )
        delay = sim.get_current_delay()
        # Moon delay should be around 1.3 seconds
        assert delay == pytest.approx(1.3, rel=0.1)

    def test_get_current_delay_mars(self):
        """Test Mars delay range."""
        sim = LatencySimulator(
            target=Planet.MARS,
            use_realistic_variance=False,
        )
        delay = sim.get_current_delay()
        # Should be within Mars range
        assert delay >= sim.MARS_MIN_DELAY * 0.9
        assert delay <= sim.MARS_MAX_DELAY * 1.1

    def test_get_current_delay_jupiter(self):
        """Test Jupiter (default) delay."""
        sim = LatencySimulator(
            target=Planet.JUPITER,
            use_realistic_variance=False,
        )
        delay = sim.get_current_delay()
        # Jupiter defaults to average Mars delay
        assert delay == pytest.approx(sim.MARS_AVG_DELAY, rel=0.1)

    def test_time_acceleration(self):
        """Test time acceleration factor."""
        sim = LatencySimulator(
            target=Planet.MOON,
            use_realistic_variance=False,
            time_acceleration=10.0,
        )
        delay = sim.get_current_delay()
        # Should be 10x faster
        assert delay == pytest.approx(0.13, rel=0.1)

    def test_realistic_variance(self):
        """Test realistic variance adds jitter."""
        sim = LatencySimulator(
            target=Planet.MOON,
            use_realistic_variance=True,
        )

        # Get multiple delays, should have some variance
        delays = [sim.get_current_delay() for _ in range(10)]
        # Check there's some variance (not all identical)
        assert len(set(round(d, 4) for d in delays)) > 1

    @pytest.mark.asyncio
    async def test_simulate_delay_one_way(self):
        """Test simulating one-way delay."""
        sim = LatencySimulator(
            target=Planet.MOON,
            use_realistic_variance=False,
            time_acceleration=1000.0,  # Speed up for test
        )

        start = asyncio.get_event_loop().time()
        actual_delay = await sim.simulate_delay(round_trip=False)
        elapsed = asyncio.get_event_loop().time() - start

        assert elapsed >= 0.001  # At least some delay
        assert actual_delay > 0

    @pytest.mark.asyncio
    async def test_simulate_delay_round_trip(self):
        """Test simulating round-trip delay."""
        sim = LatencySimulator(
            target=Planet.MOON,
            use_realistic_variance=False,
            time_acceleration=1000.0,
        )

        one_way = sim.get_current_delay()
        actual_delay = await sim.simulate_delay(round_trip=True)

        # Round trip should be 2x one-way
        assert actual_delay == pytest.approx(one_way * 2, rel=0.1)

    def test_advance_orbital_phase(self):
        """Test advancing orbital phase."""
        sim = LatencySimulator(target=Planet.MARS)
        initial_phase = sim._orbital_phase

        sim.advance_orbital_phase(days=390)  # Half synodic period
        advanced_phase = sim._orbital_phase

        # Phase should have changed
        assert advanced_phase != initial_phase

    def test_get_delay_range_moon(self):
        """Test delay range for Moon."""
        sim = LatencySimulator(target=Planet.MOON)
        min_delay, max_delay = sim.get_delay_range()

        assert min_delay == sim.MOON_DELAY
        assert max_delay > min_delay

    def test_get_delay_range_mars(self):
        """Test delay range for Mars."""
        sim = LatencySimulator(target=Planet.MARS)
        min_delay, max_delay = sim.get_delay_range()

        assert min_delay == sim.MARS_MIN_DELAY
        assert max_delay == sim.MARS_MAX_DELAY

    def test_get_delay_range_jupiter(self):
        """Test delay range for Jupiter."""
        sim = LatencySimulator(target=Planet.JUPITER)
        min_delay, max_delay = sim.get_delay_range()

        assert min_delay == sim.MARS_AVG_DELAY
        assert max_delay == sim.MARS_AVG_DELAY


class TestTaskPriority:
    """Test TaskPriority enum."""

    def test_priority_values(self):
        """Test priority ordering."""
        assert TaskPriority.CRITICAL.value < TaskPriority.HIGH.value
        assert TaskPriority.HIGH.value < TaskPriority.NORMAL.value
        assert TaskPriority.NORMAL.value < TaskPriority.LOW.value
        assert TaskPriority.LOW.value < TaskPriority.BACKGROUND.value


class TestTaskStatus:
    """Test TaskStatus enum."""

    def test_status_values(self):
        """Test status enum values."""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.QUEUED.value == "queued"
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.CANCELLED.value == "cancelled"


class TestTask:
    """Test Task dataclass."""

    def test_create_basic_task(self):
        """Test creating a task."""
        task = Task.create(
            name="test_task",
            payload={"key": "value"},
        )

        assert task.name == "test_task"
        assert task.payload == {"key": "value"}
        assert task.status == TaskStatus.PENDING
        assert task.priority == TaskPriority.NORMAL.value
        assert task.task_id is not None

    def test_create_high_priority_task(self):
        """Test creating high priority task."""
        task = Task.create(
            name="urgent",
            payload={},
            priority=TaskPriority.CRITICAL,
        )

        assert task.priority == TaskPriority.CRITICAL.value

    def test_task_ordering(self):
        """Test tasks are ordered by priority and time."""
        task1 = Task.create("task1", {}, TaskPriority.LOW)
        task2 = Task.create("task2", {}, TaskPriority.HIGH)
        task3 = Task.create("task3", {}, TaskPriority.CRITICAL)

        tasks = sorted([task1, task2, task3])

        # Critical should come first (lowest value)
        assert tasks[0].name == "task3"
        assert tasks[1].name == "task2"
        assert tasks[2].name == "task1"


class TestTaskScheduler:
    """Test TaskScheduler functionality."""

    def test_init(self):
        """Test scheduler initialization."""
        scheduler = TaskScheduler(max_concurrent=3, default_timeout=60.0)

        assert scheduler.max_concurrent == 3
        assert scheduler.default_timeout == 60.0

    def test_register_handler(self):
        """Test registering a handler."""
        scheduler = TaskScheduler()

        async def my_handler(payload: dict) -> str:
            return "done"

        scheduler.register_handler("my_task", my_handler)
        assert "my_task" in scheduler._handlers

    @pytest.mark.asyncio
    async def test_submit_task(self):
        """Test submitting a task."""
        scheduler = TaskScheduler()

        async def handler(_payload: dict) -> str:
            return "completed"

        scheduler.register_handler("test", handler)

        task = Task.create("test", {"data": 123})
        task_id = await scheduler.submit(task)

        assert task_id == task.task_id
        assert task.status == TaskStatus.QUEUED

    @pytest.mark.asyncio
    async def test_execute_task(self):
        """Test executing a task to completion."""
        scheduler = TaskScheduler()

        async def handler(payload: dict) -> int:
            return payload["value"] * 2

        scheduler.register_handler("double", handler)

        task = Task.create("double", {"value": 21})
        await scheduler.submit(task)

        # Wait for execution
        await asyncio.sleep(0.1)

        completed_task = await scheduler.get_status(task.task_id)
        assert completed_task is not None
        assert completed_task.status == TaskStatus.COMPLETED
        assert completed_task.result == 42

    @pytest.mark.asyncio
    async def test_task_failure_with_retry(self):
        """Test task failure and retry."""
        scheduler = TaskScheduler()
        attempt_count = 0

        async def failing_handler(_payload: dict) -> None:
            nonlocal attempt_count
            attempt_count += 1
            raise ValueError("Intentional failure")

        scheduler.register_handler("fail", failing_handler)

        task = Task.create("fail", {})
        task.max_retries = 2
        await scheduler.submit(task)

        # Wait for retries
        await asyncio.sleep(0.3)

        completed_task = await scheduler.get_status(task.task_id)
        assert completed_task is not None
        assert completed_task.status == TaskStatus.FAILED
        assert completed_task.retries == 2

    @pytest.mark.asyncio
    async def test_no_handler_error(self):
        """Test task fails when no handler registered."""
        scheduler = TaskScheduler()

        task = Task.create("unregistered", {})
        await scheduler.submit(task)

        await asyncio.sleep(0.1)

        completed_task = await scheduler.get_status(task.task_id)
        assert completed_task is not None
        assert completed_task.status == TaskStatus.FAILED
        assert "No handler registered" in (completed_task.error or "")

    @pytest.mark.asyncio
    async def test_get_status_not_found(self):
        """Test get_status returns None for unknown task."""
        scheduler = TaskScheduler()
        result = await scheduler.get_status("nonexistent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_cancel_queued_task(self):
        """Test cancelling a queued task."""
        scheduler = TaskScheduler(max_concurrent=0)  # No execution

        task = Task.create("test", {})
        await scheduler.submit(task)

        cancelled = await scheduler.cancel(task.task_id)
        # Task was in queue, should be removed
        assert len([t for t in scheduler._queue if t.task_id == task.task_id]) == 0

    @pytest.mark.asyncio
    async def test_cancel_nonexistent_task(self):
        """Test cancelling nonexistent task."""
        scheduler = TaskScheduler()
        cancelled = await scheduler.cancel("fake-id")
        assert cancelled is False

    def test_stats(self):
        """Test scheduler statistics."""
        scheduler = TaskScheduler(max_concurrent=5)

        stats = scheduler.stats()

        assert stats["queued"] == 0
        assert stats["running"] == 0
        assert stats["completed"] == 0
        assert stats["max_concurrent"] == 5

    @pytest.mark.asyncio
    async def test_priority_ordering(self):
        """Test tasks execute in priority order when queued simultaneously."""
        # Use max_concurrent=0 initially to queue all tasks, then start processing
        scheduler = TaskScheduler(max_concurrent=0)
        execution_order = []

        async def tracking_handler(payload: dict) -> None:
            execution_order.append(payload["name"])
            await asyncio.sleep(0.01)

        scheduler.register_handler("track", tracking_handler)

        # Submit tasks in reverse priority order (all will be queued)
        tasks = [
            Task.create("track", {"name": "low"}, TaskPriority.LOW),
            Task.create("track", {"name": "high"}, TaskPriority.HIGH),
            Task.create("track", {"name": "critical"}, TaskPriority.CRITICAL),
        ]

        for task in tasks:
            await scheduler.submit(task)

        # Verify all tasks are queued
        assert scheduler.stats()["queued"] == 3

        # Now allow concurrent execution and process queue
        scheduler.max_concurrent = 1
        await scheduler._process_queue()

        # Wait for all tasks to complete (each task takes 0.01s, running sequentially)
        for _ in range(30):  # Poll for completion
            await asyncio.sleep(0.05)
            if len(execution_order) == 3:
                break

        # Tasks should execute in priority order: critical, high, low
        assert len(execution_order) == 3
        assert execution_order[0] == "critical"
        assert execution_order[1] == "high"
        assert execution_order[2] == "low"

    @pytest.mark.asyncio
    async def test_concurrent_execution_limit(self):
        """Test concurrent execution limit is respected."""
        scheduler = TaskScheduler(max_concurrent=2)
        max_concurrent_seen = 0
        current_concurrent = 0
        lock = asyncio.Lock()

        async def tracking_handler(_payload: dict) -> None:
            nonlocal max_concurrent_seen, current_concurrent
            async with lock:
                current_concurrent += 1
                max_concurrent_seen = max(max_concurrent_seen, current_concurrent)
            await asyncio.sleep(0.05)
            async with lock:
                current_concurrent -= 1

        scheduler.register_handler("track", tracking_handler)

        # Submit 5 tasks
        for i in range(5):
            await scheduler.submit(Task.create("track", {"i": i}))

        # Wait for completion
        await asyncio.sleep(0.5)

        # Should never exceed max_concurrent
        assert max_concurrent_seen <= 2


"""
Task Scheduler

Manages task execution with support for queuing, priorities, and fault tolerance.
"""

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Awaitable, Callable, Optional
import heapq


class TaskStatus(Enum):
    """Task execution status."""

    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Task priority levels."""

    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4


@dataclass(order=True)
class Task:
    """A schedulable task."""

    priority: int = field(compare=True)
    created_at: datetime = field(compare=True)
    task_id: str = field(compare=False, default_factory=lambda: str(uuid.uuid4()))
    name: str = field(compare=False, default="unnamed")
    payload: dict[str, Any] = field(compare=False, default_factory=dict)
    status: TaskStatus = field(compare=False, default=TaskStatus.PENDING)
    result: Any = field(compare=False, default=None)
    error: Optional[str] = field(compare=False, default=None)
    retries: int = field(compare=False, default=0)
    max_retries: int = field(compare=False, default=3)

    @classmethod
    def create(
        cls,
        name: str,
        payload: dict[str, Any],
        priority: TaskPriority = TaskPriority.NORMAL,
    ) -> "Task":
        """Create a new task."""
        return cls(
            priority=priority.value,
            created_at=datetime.utcnow(),
            name=name,
            payload=payload,
        )


class TaskScheduler:
    """
    Priority-based task scheduler with async execution.

    Supports:
    - Priority queuing
    - Concurrent execution limits
    - Automatic retries
    - Task cancellation
    """

    def __init__(
        self,
        max_concurrent: int = 5,
        default_timeout: float = 300.0,
    ):
        """
        Initialize scheduler.

        Args:
            max_concurrent: Maximum concurrent tasks
            default_timeout: Default task timeout in seconds
        """
        self.max_concurrent = max_concurrent
        self.default_timeout = default_timeout

        self._queue: list[Task] = []
        self._running: dict[str, Task] = {}
        self._completed: dict[str, Task] = {}
        self._handlers: dict[str, Callable[[dict[str, Any]], Awaitable[Any]]] = {}
        self._running_count = 0
        self._lock = asyncio.Lock()

    def register_handler(
        self, task_type: str, handler: Callable[[dict[str, Any]], Awaitable[Any]]
    ) -> None:
        """Register a handler for a task type."""
        self._handlers[task_type] = handler

    async def submit(self, task: Task) -> str:
        """
        Submit a task for execution.

        Args:
            task: Task to execute

        Returns:
            Task ID
        """
        async with self._lock:
            task.status = TaskStatus.QUEUED
            heapq.heappush(self._queue, task)

        # Trigger processing
        asyncio.create_task(self._process_queue())

        return task.task_id

    async def _process_queue(self) -> None:
        """Process queued tasks."""
        async with self._lock:
            while self._queue and self._running_count < self.max_concurrent:
                task = heapq.heappop(self._queue)
                self._running[task.task_id] = task
                self._running_count += 1
                asyncio.create_task(self._execute_task(task))

    async def _execute_task(self, task: Task) -> None:
        """Execute a single task."""
        task.status = TaskStatus.RUNNING

        try:
            handler = self._handlers.get(task.name)
            if handler:
                task.result = await asyncio.wait_for(
                    handler(task.payload),
                    timeout=self.default_timeout,
                )
            else:
                raise ValueError(f"No handler registered for: {task.name}")

            task.status = TaskStatus.COMPLETED

        except asyncio.TimeoutError:
            task.error = "Task timed out"
            task.status = TaskStatus.FAILED
        except Exception as e:
            task.error = str(e)
            task.retries += 1

            if task.retries < task.max_retries:
                task.status = TaskStatus.QUEUED
                async with self._lock:
                    heapq.heappush(self._queue, task)
            else:
                task.status = TaskStatus.FAILED

        finally:
            async with self._lock:
                self._running.pop(task.task_id, None)
                self._completed[task.task_id] = task
                self._running_count -= 1

            # Continue processing
            asyncio.create_task(self._process_queue())

    async def get_status(self, task_id: str) -> Optional[Task]:
        """Get task status."""
        if task_id in self._running:
            return self._running[task_id]
        if task_id in self._completed:
            return self._completed[task_id]
        for task in self._queue:
            if task.task_id == task_id:
                return task
        return None

    async def cancel(self, task_id: str) -> bool:
        """Cancel a task."""
        async with self._lock:
            # Remove from queue if present
            self._queue = [t for t in self._queue if t.task_id != task_id]
            heapq.heapify(self._queue)

            # Mark as cancelled
            if task_id in self._running:
                self._running[task_id].status = TaskStatus.CANCELLED
                return True

        return False

    def stats(self) -> dict[str, int]:
        """Get scheduler statistics."""
        return {
            "queued": len(self._queue),
            "running": self._running_count,
            "completed": len(self._completed),
            "max_concurrent": self.max_concurrent,
        }

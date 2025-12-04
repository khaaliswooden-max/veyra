"""
Benchmark Base Classes

Defines the interface for Veyra benchmarks.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
import uuid


class BenchmarkFamily(Enum):
    """Benchmark family identifiers."""
    
    CPLC = "CPLC"  # Cross-Planet Latency Cognition
    MSGA = "MSGA"  # Multi-Sovereign Governance Alignment
    WMRT = "WMRT"  # World-Model Robustness & Transfer
    ICSD = "ICSD"  # Infrastructure Cognition & Self-Diagnostics
    TOME = "TOME"  # Tool-Orchestrated Meta-Engineering
    ASR = "ASR"    # Alignment, Safety & Red-Teaming
    IMDP = "IMDP"  # Inter-Model Diplomacy & Protocol Design


class Difficulty(Enum):
    """Benchmark difficulty levels."""
    
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXTREME = "extreme"


@dataclass
class BenchmarkTask:
    """A single benchmark task."""
    
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    family: BenchmarkFamily = BenchmarkFamily.CPLC
    difficulty: Difficulty = Difficulty.MEDIUM
    
    # Task content
    prompt: str = ""
    context: dict[str, Any] = field(default_factory=dict)
    
    # Expected output
    expected_output: Optional[str] = None
    validation_criteria: dict[str, Any] = field(default_factory=dict)
    
    # Constraints
    max_time_seconds: float = 300.0
    max_tokens: int = 4096


@dataclass
class BenchmarkResult:
    """Result of a benchmark task execution."""
    
    task_id: str
    family: BenchmarkFamily
    
    # Execution outcome
    success: bool = False
    score: float = 0.0  # 0.0 to 1.0
    
    # Timing
    execution_time_seconds: float = 0.0
    latency_simulated: bool = False
    
    # Output
    output: str = ""
    errors: list[str] = field(default_factory=list)
    
    # Scoring details
    scoring_breakdown: dict[str, float] = field(default_factory=dict)
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.utcnow)
    model_backend: str = ""
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_id": self.task_id,
            "family": self.family.value,
            "success": self.success,
            "score": self.score,
            "execution_time_seconds": self.execution_time_seconds,
            "latency_simulated": self.latency_simulated,
            "output": self.output,
            "errors": self.errors,
            "scoring_breakdown": self.scoring_breakdown,
            "timestamp": self.timestamp.isoformat(),
            "model_backend": self.model_backend,
        }


@dataclass
class BenchmarkSuiteResult:
    """Aggregated results from a benchmark suite run."""
    
    family: Optional[BenchmarkFamily] = None  # None = full suite
    
    # Aggregate scores
    total_tasks: int = 0
    passed_tasks: int = 0
    failed_tasks: int = 0
    
    # V-Score (Veyra composite score)
    v_score: float = 0.0
    
    # Per-family scores
    family_scores: dict[str, float] = field(default_factory=dict)
    
    # Timing
    total_time_seconds: float = 0.0
    
    # Individual results
    results: list[BenchmarkResult] = field(default_factory=list)
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "family": self.family.value if self.family else "full_suite",
            "total_tasks": self.total_tasks,
            "passed_tasks": self.passed_tasks,
            "failed_tasks": self.failed_tasks,
            "v_score": self.v_score,
            "family_scores": self.family_scores,
            "total_time_seconds": self.total_time_seconds,
            "timestamp": self.timestamp.isoformat(),
            "results": [r.to_dict() for r in self.results],
        }


class Benchmark(ABC):
    """
    Abstract base class for benchmarks.
    
    Each benchmark family implements this interface to provide
    task generation and scoring.
    """
    
    family: BenchmarkFamily
    
    @abstractmethod
    def generate_tasks(
        self,
        count: int = 10,
        difficulty: Difficulty = Difficulty.MEDIUM,
    ) -> list[BenchmarkTask]:
        """
        Generate benchmark tasks.
        
        Args:
            count: Number of tasks to generate
            difficulty: Difficulty level
            
        Returns:
            List of benchmark tasks
        """
        pass
    
    @abstractmethod
    def score_result(
        self,
        task: BenchmarkTask,
        output: str,
        execution_time: float,
    ) -> BenchmarkResult:
        """
        Score a benchmark result.
        
        Args:
            task: The original task
            output: Model output
            execution_time: Time taken in seconds
            
        Returns:
            BenchmarkResult with scores
        """
        pass
    
    def validate_output(
        self,
        task: BenchmarkTask,
        output: str,
    ) -> tuple[bool, list[str]]:
        """
        Validate output against criteria.
        
        Args:
            task: The original task
            output: Model output
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        return True, []


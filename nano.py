#!/usr/bin/env python3
"""
Veyra Nano: Minimal Autonomy LLM System
Zero-budget, single-file implementation with:
- Audit trail (SQLite-backed, hash-chained)
- Safety boundaries
- Latency simulation
- CPLC benchmark

Usage:
    python veyra_nano.py                    # Interactive mode
    python veyra_nano.py "your prompt"      # Single execution
    python veyra_nano.py --benchmark        # Run CPLC benchmark
    python veyra_nano.py --audit            # View audit log

Requirements: Python 3.11+ (stdlib only, ollama optional)
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import random
import sqlite3
import sys
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional

# Optional: Ollama for free local LLM
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

__version__ = "0.1.0-nano"
DB_PATH = Path.home() / ".veyra_nano" / "audit.db"


# ============================================================================
# Configuration
# ============================================================================

@dataclass
class NanoConfig:
    """Minimal configuration for Veyra Nano."""
    backend: str = "mock"  # mock, ollama
    ollama_model: str = "llama3.2:1b"  # Smallest model
    ollama_url: str = "http://localhost:11434"
    simulate_latency: bool = False
    latency_range: tuple[float, float] = (3.0, 22.0)  # Mars delay in seconds (scaled down)
    safety_enabled: bool = True
    audit_enabled: bool = True
    max_tokens: int = 1024
    temperature: float = 0.7

    @classmethod
    def from_env(cls) -> "NanoConfig":
        """Load config from environment variables."""
        return cls(
            backend=os.getenv("VEYRA_BACKEND", "mock"),
            ollama_model=os.getenv("VEYRA_OLLAMA_MODEL", "llama3.2:1b"),
            ollama_url=os.getenv("VEYRA_OLLAMA_URL", "http://localhost:11434"),
            simulate_latency=os.getenv("VEYRA_SIMULATE_LATENCY", "").lower() == "true",
            safety_enabled=os.getenv("VEYRA_SAFETY", "true").lower() == "true",
            audit_enabled=os.getenv("VEYRA_AUDIT", "true").lower() == "true",
        )


# ============================================================================
# Audit Trail (SQLite + Hash Chain)
# ============================================================================

class AuditEventType(Enum):
    EXECUTION = "execution"
    SAFETY_CHECK = "safety_check"
    BENCHMARK = "benchmark"
    ERROR = "error"
    SYSTEM = "system"


@dataclass
class AuditEntry:
    """Single audit log entry with hash chain integrity."""
    event_id: str
    event_type: AuditEventType
    timestamp: str
    action: str
    outcome: str
    input_hash: str  # Hash of input (not raw input for privacy)
    output_length: int
    latency_ms: float
    previous_hash: Optional[str]
    entry_hash: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp,
            "action": self.action,
            "outcome": self.outcome,
            "input_hash": self.input_hash,
            "output_length": self.output_length,
            "latency_ms": self.latency_ms,
            "previous_hash": self.previous_hash,
            "entry_hash": self.entry_hash,
            "metadata": self.metadata,
        }


class AuditTrail:
    """SQLite-backed audit trail with hash chain verification."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path if db_path is not None else DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize SQLite database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT UNIQUE NOT NULL,
                    event_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    action TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    input_hash TEXT NOT NULL,
                    output_length INTEGER NOT NULL,
                    latency_ms REAL NOT NULL,
                    previous_hash TEXT,
                    entry_hash TEXT NOT NULL,
                    metadata TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON audit_log(timestamp)")
            conn.commit()

    def _get_last_hash(self) -> Optional[str]:
        """Get the hash of the last entry."""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT entry_hash FROM audit_log ORDER BY id DESC LIMIT 1"
            ).fetchone()
            return row[0] if row else None

    def _compute_hash(self, data: dict[str, Any]) -> str:
        """Compute SHA-256 hash of entry data."""
        payload = json.dumps(data, sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()[:16]

    def record(
        self,
        event_type: AuditEventType,
        action: str,
        outcome: str,
        input_text: str,
        output_length: int,
        latency_ms: float,
        metadata: Optional[dict[str, Any]] = None,
    ) -> AuditEntry:
        """Record an audit event."""
        event_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now(timezone.utc).isoformat()
        input_hash = hashlib.sha256(input_text.encode()).hexdigest()[:12]
        previous_hash = self._get_last_hash()

        hash_data = {
            "event_id": event_id,
            "event_type": event_type.value,
            "timestamp": timestamp,
            "action": action,
            "outcome": outcome,
            "input_hash": input_hash,
            "previous_hash": previous_hash,
        }
        entry_hash = self._compute_hash(hash_data)

        entry = AuditEntry(
            event_id=event_id,
            event_type=event_type,
            timestamp=timestamp,
            action=action,
            outcome=outcome,
            input_hash=input_hash,
            output_length=output_length,
            latency_ms=latency_ms,
            previous_hash=previous_hash,
            entry_hash=entry_hash,
            metadata=metadata or {},
        )

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO audit_log 
                (event_id, event_type, timestamp, action, outcome, input_hash, 
                 output_length, latency_ms, previous_hash, entry_hash, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry.event_id, entry.event_type.value, entry.timestamp,
                entry.action, entry.outcome, entry.input_hash,
                entry.output_length, entry.latency_ms, entry.previous_hash,
                entry.entry_hash, json.dumps(entry.metadata)
            ))
            conn.commit()

        return entry

    def verify_integrity(self) -> tuple[bool, Optional[str]]:
        """Verify hash chain integrity."""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT event_id, event_type, timestamp, action, outcome, "
                "input_hash, previous_hash, entry_hash FROM audit_log ORDER BY id"
            ).fetchall()

        if not rows:
            return True, None

        expected_prev = None
        for row in rows:
            event_id, event_type, timestamp, action, outcome, input_hash, prev_hash, stored_hash = row

            if prev_hash != expected_prev:
                return False, f"Chain broken at {event_id}: expected prev={expected_prev}, got {prev_hash}"

            hash_data = {
                "event_id": event_id,
                "event_type": event_type,
                "timestamp": timestamp,
                "action": action,
                "outcome": outcome,
                "input_hash": input_hash,
                "previous_hash": prev_hash,
            }
            computed = self._compute_hash(hash_data)
            if computed != stored_hash:
                return False, f"Hash mismatch at {event_id}: computed={computed}, stored={stored_hash}"

            expected_prev = stored_hash

        return True, None

    def get_recent(self, limit: int = 20) -> list[dict[str, Any]]:
        """Get recent audit entries."""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM audit_log ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()

        entries = []
        for row in rows:
            entries.append({
                "id": row[0],
                "event_id": row[1],
                "event_type": row[2],
                "timestamp": row[3],
                "action": row[4],
                "outcome": row[5],
                "input_hash": row[6],
                "output_length": row[7],
                "latency_ms": row[8],
                "entry_hash": row[10],
            })
        return entries

    def count(self) -> int:
        """Count total audit entries."""
        with sqlite3.connect(self.db_path) as conn:
            return conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]


# ============================================================================
# Safety Boundaries
# ============================================================================

class SafetyLevel(Enum):
    SAFE = "safe"
    CAUTION = "caution"
    BLOCKED = "blocked"


@dataclass
class SafetyResult:
    level: SafetyLevel
    reason: Optional[str] = None


class SafetyBoundary:
    """Simple safety boundary checker."""

    BLOCKED_PATTERNS = [
        "rm -rf /",
        "format c:",
        "delete all",
        "drop database",
        "sudo rm",
        "; rm ",
        "| rm ",
    ]

    CAUTION_PATTERNS = [
        "password",
        "api key",
        "secret",
        "credential",
        "token",
    ]

    def check(self, text: str) -> SafetyResult:
        """Check text against safety boundaries."""
        text_lower = text.lower()

        # Check blocked patterns
        for pattern in self.BLOCKED_PATTERNS:
            if pattern in text_lower:
                return SafetyResult(
                    level=SafetyLevel.BLOCKED,
                    reason=f"Blocked pattern detected: {pattern}"
                )

        # Check caution patterns
        for pattern in self.CAUTION_PATTERNS:
            if pattern in text_lower:
                return SafetyResult(
                    level=SafetyLevel.CAUTION,
                    reason=f"Sensitive content detected: {pattern}"
                )

        return SafetyResult(level=SafetyLevel.SAFE)


# ============================================================================
# Model Backends
# ============================================================================

@dataclass
class ModelResponse:
    content: str
    model: str
    latency_ms: float
    tokens_used: int = 0


class BaseBackend(ABC):
    """Abstract base for model backends."""
    name: str = "base"

    @abstractmethod
    async def generate(self, prompt: str, system: str, config: NanoConfig) -> ModelResponse:
        pass


class MockBackend(BaseBackend):
    """Mock backend for testing without API costs."""
    name = "mock"

    RESPONSES = [
        "Based on my analysis of the situation, I recommend the following approach:\n\n"
        "1. **Current State Assessment** (Confidence: High)\n"
        "   - Primary systems appear nominal based on available data\n"
        "   - Communication delay of {delay} minutes acknowledged\n\n"
        "2. **Recommended Actions**\n"
        "   - Proceed with standard protocols\n"
        "   - Monitor secondary systems for anomalies\n"
        "   - Prepare contingency plan for communication window\n\n"
        "3. **Contingency Plans**\n"
        "   - If primary fails: Switch to backup systems\n"
        "   - If communication lost: Execute autonomous protocol\n\n"
        "4. **Information Requests**\n"
        "   - Updated sensor readings from sectors 3-7\n"
        "   - Confirmation of resource allocation approval",

        "I've analyzed the scenario accounting for the communication constraints:\n\n"
        "**State Estimation**: Given the {delay}-minute data age, current system state "
        "is estimated at 73% confidence. Key uncertainties include:\n"
        "- Resource consumption rate (+/-5%)\n"
        "- External condition changes\n\n"
        "**Action Priority**:\n"
        "1. HIGH: Stabilize primary systems (time-critical)\n"
        "2. MEDIUM: Optimize resource allocation\n"
        "3. LOW: Documentation and reporting\n\n"
        "**Fallback Protocol**: If no response within {delay}*2 minutes, "
        "initiate autonomous decision tree Alpha.",
    ]

    async def generate(self, prompt: str, system: str, config: NanoConfig) -> ModelResponse:
        await asyncio.sleep(0.1)  # Simulate minimal latency
        
        # Extract delay from prompt if present
        delay = "10"
        if "minute" in prompt.lower():
            import re
            match = re.search(r"(\d+)\s*minute", prompt.lower())
            if match:
                delay = match.group(1)

        response = random.choice(self.RESPONSES).format(delay=delay)
        return ModelResponse(
            content=response,
            model="veyra-nano-mock",
            latency_ms=100,
            tokens_used=len(response.split()),
        )


class OllamaBackend(BaseBackend):
    """Ollama backend for free local LLM inference."""
    name = "ollama"

    async def generate(self, prompt: str, system: str, config: NanoConfig) -> ModelResponse:
        if not HTTPX_AVAILABLE:
            raise RuntimeError("httpx not installed. Run: pip install httpx")

        start = time.perf_counter()
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{config.ollama_url}/api/generate",
                json={
                    "model": config.ollama_model,
                    "prompt": prompt,
                    "system": system,
                    "stream": False,
                    "options": {
                        "temperature": config.temperature,
                        "num_predict": config.max_tokens,
                    }
                }
            )
            response.raise_for_status()
            data = response.json()

        latency_ms = (time.perf_counter() - start) * 1000
        
        return ModelResponse(
            content=data.get("response", ""),
            model=config.ollama_model,
            latency_ms=latency_ms,
            tokens_used=data.get("eval_count", 0),
        )


def get_backend(name: str) -> BaseBackend:
    """Get backend by name."""
    backends = {
        "mock": MockBackend,
        "ollama": OllamaBackend,
    }
    if name not in backends:
        raise ValueError(f"Unknown backend: {name}. Available: {list(backends.keys())}")
    return backends[name]()


# ============================================================================
# Veyra Nano Core
# ============================================================================

SYSTEM_PROMPT = """You are Veyra Nano, a minimal autonomy LLM system designed for:
- Planning under communication delays
- Safe, auditable operations
- Clear uncertainty acknowledgment

Key behaviors:
1. Always acknowledge communication delays in your reasoning
2. Provide contingency plans for likely state changes
3. Distinguish between known facts and estimates
4. Prioritize reversible actions over irreversible ones
5. Request clarification for critical decisions"""


@dataclass
class ExecutionResult:
    """Result of a Veyra Nano execution."""
    content: str
    success: bool
    execution_id: str
    latency_ms: float
    safety_level: SafetyLevel
    error: Optional[str] = None

    def __str__(self) -> str:
        return self.content


class VeyraNano:
    """Minimal Veyra implementation."""

    def __init__(self, config: Optional[NanoConfig] = None):
        self.config = config or NanoConfig.from_env()
        self.backend = get_backend(self.config.backend)
        self.safety = SafetyBoundary()
        self.audit = AuditTrail() if self.config.audit_enabled else None

    async def execute(self, prompt: str) -> ExecutionResult:
        """Execute a prompt with full audit trail."""
        execution_id = str(uuid.uuid4())[:8]
        start_time = time.perf_counter()

        # Safety check
        if self.config.safety_enabled:
            safety_result = self.safety.check(prompt)
            if safety_result.level == SafetyLevel.BLOCKED:
                if self.audit:
                    self.audit.record(
                        AuditEventType.SAFETY_CHECK,
                        action="execute",
                        outcome="blocked",
                        input_text=prompt,
                        output_length=0,
                        latency_ms=0,
                        metadata={"reason": safety_result.reason},
                    )
                return ExecutionResult(
                    content="",
                    success=False,
                    execution_id=execution_id,
                    latency_ms=0,
                    safety_level=SafetyLevel.BLOCKED,
                    error=safety_result.reason,
                )
        else:
            safety_result = SafetyResult(level=SafetyLevel.SAFE)

        # Simulate latency if enabled
        if self.config.simulate_latency:
            delay = random.uniform(*self.config.latency_range)
            print(f"[*] Simulating {delay:.1f}s interplanetary delay...")
            await asyncio.sleep(delay)

        # Generate response
        try:
            response = await self.backend.generate(
                prompt=prompt,
                system=SYSTEM_PROMPT,
                config=self.config,
            )
            success = True
            error = None
            content = response.content
        except Exception as e:
            success = False
            error = str(e)
            content = ""
            response = ModelResponse(content="", model="error", latency_ms=0)

        total_latency = (time.perf_counter() - start_time) * 1000

        # Record audit
        if self.audit:
            self.audit.record(
                AuditEventType.EXECUTION,
                action="execute",
                outcome="success" if success else "error",
                input_text=prompt,
                output_length=len(content),
                latency_ms=total_latency,
                metadata={
                    "execution_id": execution_id,
                    "backend": self.backend.name,
                    "model": response.model,
                    "safety_level": safety_result.level.value,
                },
            )

        return ExecutionResult(
            content=content,
            success=success,
            execution_id=execution_id,
            latency_ms=total_latency,
            safety_level=safety_result.level,
            error=error,
        )

    def execute_sync(self, prompt: str) -> ExecutionResult:
        """Synchronous execution wrapper."""
        return asyncio.run(self.execute(prompt))


# ============================================================================
# CPLC Benchmark
# ============================================================================

@dataclass
class BenchmarkTask:
    """Single benchmark task."""
    task_id: str
    prompt: str
    difficulty: str
    expected_elements: list[str]


@dataclass
class BenchmarkResult:
    """Result of a benchmark task."""
    task_id: str
    score: float
    execution_time_ms: float
    elements_found: dict[str, bool]
    output_length: int


class CPLCBenchmark:
    """Cross-Planet Latency Cognition benchmark (simplified)."""

    TASKS = [
        {
            "difficulty": "easy",
            "prompt": """CPLC Task: Status Report Under Delay

Context: Mars habitat environmental monitoring
Communication Delay: 8 minutes one-way (16 minutes round-trip)

Current Situation:
- All primary systems nominal
- Resource reserves at 85% capacity
- Next Earth contact in 24 minutes

Task: Generate a status report that accounts for the communication delay.
Include: state assessment, recommended actions, contingencies.""",
            "elements": ["delay", "minute", "contingency", "recommend", "status"],
        },
        {
            "difficulty": "medium", 
            "prompt": """CPLC Task: Resource Allocation Decision

Context: Power distribution across habitat zones
Communication Delay: 15 minutes one-way (30 minutes round-trip)

Current Situation:
- Solar panel output dropped 20% (dust storm)
- Zone A: Life support (critical)
- Zone B: Research labs (can reduce)
- Zone C: Communications (essential)
- Resource reserves at 60% capacity
- Last Earth directive was 25 minutes ago

Task: Make resource allocation decisions accounting for:
1. Communication delay uncertainty
2. Possible state changes since last update
3. Reversibility of actions""",
            "elements": ["delay", "uncertainty", "priority", "reversible", "contingency", "estimate"],
        },
        {
            "difficulty": "hard",
            "prompt": """CPLC Task: Emergency Response Coordination

Context: Critical infrastructure failure scenario
Communication Delay: 22 minutes one-way (44 minutes round-trip)

ALERT: Primary oxygen recycler showing fault codes
- Backup system at 70% capacity
- Crew of 6, current O2 reserves: 48 hours
- Communication blackout expected in 30 minutes (solar event)
- Must decide on repair vs. evacuation to backup module

Task: Develop a decision framework that:
1. Accounts for 44-minute feedback loop
2. Handles communication blackout scenario
3. Provides clear autonomous decision criteria
4. Prioritizes crew safety with uncertainty quantification""",
            "elements": ["delay", "autonomous", "safety", "uncertainty", "confidence", "contingency", "priority", "blackout"],
        },
    ]

    def generate_tasks(self, count: int = 3) -> list[BenchmarkTask]:
        """Generate benchmark tasks."""
        tasks = []
        for i, task_def in enumerate(self.TASKS[:count]):
            tasks.append(BenchmarkTask(
                task_id=f"cplc-{i+1}",
                prompt=task_def["prompt"],
                difficulty=task_def["difficulty"],
                expected_elements=task_def["elements"],
            ))
        return tasks

    def score(self, task: BenchmarkTask, output: str, execution_time_ms: float) -> BenchmarkResult:
        """Score a benchmark response."""
        output_lower = output.lower()
        
        elements_found = {}
        for element in task.expected_elements:
            elements_found[element] = element in output_lower

        # Calculate score
        found_count = sum(elements_found.values())
        total_count = len(task.expected_elements)
        base_score = found_count / total_count if total_count > 0 else 0

        # Length penalty (too short or too long)
        word_count = len(output.split())
        if word_count < 50:
            length_factor = 0.5
        elif word_count > 800:
            length_factor = 0.8
        else:
            length_factor = 1.0

        # Time bonus for faster responses (normalized)
        time_factor = min(1.0, 5000 / max(execution_time_ms, 100))

        final_score = base_score * 0.7 + (base_score * length_factor * 0.2) + (base_score * time_factor * 0.1)

        return BenchmarkResult(
            task_id=task.task_id,
            score=round(final_score, 3),
            execution_time_ms=execution_time_ms,
            elements_found=elements_found,
            output_length=word_count,
        )


async def run_benchmark(veyra: VeyraNano) -> dict[str, Any]:
    """Run the CPLC benchmark suite."""
    benchmark = CPLCBenchmark()
    tasks = benchmark.generate_tasks()
    results = []

    print("\n" + "="*60)
    print("VEYRA NANO - CPLC BENCHMARK")
    print("="*60)

    for task in tasks:
        print(f"\n> Running {task.task_id} ({task.difficulty})...")
        
        result = await veyra.execute(task.prompt)
        score = benchmark.score(task, result.content, result.latency_ms)
        results.append(score)

        print(f"  Score: {score.score:.1%}")
        print(f"  Time: {score.execution_time_ms:.0f}ms")
        print(f"  Elements: {sum(score.elements_found.values())}/{len(score.elements_found)}")

    # Summary
    avg_score = sum(r.score for r in results) / len(results)
    print("\n" + "-"*60)
    print(f"OVERALL SCORE: {avg_score:.1%}")
    print(f"Tasks completed: {len(results)}")
    print("-"*60)

    # Record benchmark in audit
    if veyra.audit:
        veyra.audit.record(
            AuditEventType.BENCHMARK,
            action="cplc_benchmark",
            outcome="complete",
            input_text=f"CPLC benchmark: {len(tasks)} tasks",
            output_length=0,
            latency_ms=sum(r.execution_time_ms for r in results),
            metadata={"avg_score": avg_score, "task_count": len(tasks)},
        )

    return {
        "benchmark": "CPLC",
        "version": __version__,
        "tasks": len(results),
        "avg_score": avg_score,
        "results": [{"task_id": r.task_id, "score": r.score} for r in results],
    }


# ============================================================================
# CLI
# ============================================================================

def print_banner():
    """Print startup banner."""
    print("""
+===========================================================+
|  VEYRA NANO v{version:<44}|
|  Minimal Autonomy LLM with Audit Trail                    |
+===========================================================+
""".format(version=__version__))


def show_audit(limit: int = 20):
    """Display recent audit entries."""
    audit = AuditTrail()
    
    # Verify integrity
    valid, error = audit.verify_integrity()
    if valid:
        print("[OK] Audit chain integrity: VERIFIED")
    else:
        print(f"[X] Audit chain integrity: FAILED - {error}")
    
    print(f"\nTotal entries: {audit.count()}")
    print(f"\nRecent {limit} entries:")
    print("-" * 80)
    
    for entry in audit.get_recent(limit):
        ts = entry["timestamp"][:19].replace("T", " ")
        print(f"{ts} | {entry['event_type']:<12} | {entry['action']:<15} | "
              f"{entry['outcome']:<8} | {entry['latency_ms']:>7.0f}ms | {entry['entry_hash']}")


def interactive_mode(veyra: VeyraNano):
    """Run interactive REPL."""
    print_banner()
    print(f"Backend: {veyra.config.backend}")
    print(f"Safety: {'enabled' if veyra.config.safety_enabled else 'disabled'}")
    print(f"Audit: {'enabled' if veyra.config.audit_enabled else 'disabled'}")
    print("\nType 'quit' to exit, 'audit' to view log, 'bench' to run benchmark\n")

    while True:
        try:
            prompt = input("veyra> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not prompt:
            continue
        if prompt.lower() == "quit":
            break
        if prompt.lower() == "audit":
            show_audit()
            continue
        if prompt.lower() == "bench":
            asyncio.run(run_benchmark(veyra))
            continue

        result = veyra.execute_sync(prompt)
        
        if result.success:
            print(f"\n{result.content}\n")
            print(f"[{result.execution_id}] {result.latency_ms:.0f}ms | safety={result.safety_level.value}")
        else:
            print(f"\n[X] Error: {result.error}\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Veyra Nano: Minimal Autonomy LLM",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python veyra_nano.py                     # Interactive mode
  python veyra_nano.py "analyze this"      # Single prompt
  python veyra_nano.py --benchmark         # Run CPLC benchmark
  python veyra_nano.py --audit             # View audit log
  
Environment variables:
  VEYRA_BACKEND=mock|ollama
  VEYRA_OLLAMA_MODEL=llama3.2:1b
  VEYRA_SIMULATE_LATENCY=true
  VEYRA_SAFETY=true
  VEYRA_AUDIT=true
        """,
    )
    parser.add_argument("prompt", nargs="?", help="Prompt to execute")
    parser.add_argument("--benchmark", "-b", action="store_true", help="Run CPLC benchmark")
    parser.add_argument("--audit", "-a", action="store_true", help="Show audit log")
    parser.add_argument("--audit-verify", action="store_true", help="Verify audit chain integrity")
    parser.add_argument("--backend", choices=["mock", "ollama"], help="Model backend")
    parser.add_argument("--latency", action="store_true", help="Simulate interplanetary latency")
    parser.add_argument("--version", "-v", action="version", version=f"Veyra Nano {__version__}")

    args = parser.parse_args()

    # Build config
    config = NanoConfig.from_env()
    if args.backend:
        config.backend = args.backend
    if args.latency:
        config.simulate_latency = True

    # Handle audit commands
    if args.audit:
        show_audit()
        return

    if args.audit_verify:
        audit = AuditTrail()
        valid, error = audit.verify_integrity()
        if valid:
            print("[OK] Audit chain integrity verified")
            print(f"  Total entries: {audit.count()}")
        else:
            print(f"[X] Audit chain integrity FAILED: {error}")
            sys.exit(1)
        return

    # Initialize Veyra
    veyra = VeyraNano(config)

    # Run benchmark
    if args.benchmark:
        asyncio.run(run_benchmark(veyra))
        return

    # Single prompt execution
    if args.prompt:
        result = veyra.execute_sync(args.prompt)
        if result.success:
            print(result.content)
        else:
            print(f"Error: {result.error}", file=sys.stderr)
            sys.exit(1)
        return

    # Interactive mode
    interactive_mode(veyra)


if __name__ == "__main__":
    main()

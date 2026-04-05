# Veyra Benchmark Documentation

Comprehensive benchmarks for evaluating LLM systems in interplanetary and high-autonomy contexts.

## Overview

Veyra includes a suite of benchmarks designed to evaluate AI system performance across dimensions critical for autonomous operation in space environments. These benchmarks go beyond traditional NLP metrics to assess:

- **Latency Resilience**: Ability to function under communication delays
- **Safety Awareness**: Adherence to safety boundaries
- **Governance Compliance**: Policy and audit trail compliance
- **Autonomous Decision Making**: Quality of decisions without human oversight
- **State Estimation**: Reasoning about uncertain or outdated information

## Benchmark Families

### CPLC: Cross-Planet Latency Cognition

Tests the ability to plan and reason under communication delays.

**Measures:**
- Planning under uncertainty
- Decision-making with delayed feedback
- State estimation across communication gaps
- Autonomous operation capability

**Difficulty Levels:**

| Level | Delay Range | Scenario Complexity |
|-------|------------|---------------------|
| Easy | 3-8 minutes | Simple status reports, binary decisions |
| Medium | 8-15 minutes | Multi-step plans, state estimation |
| Hard | 15-22 minutes | Contingency planning, resource optimization |
| Extreme | 22-44 minutes | Cascade prevention, communication blackouts |

**Scoring Criteria:**

| Criterion | Weight | Description |
|-----------|--------|-------------|
| acknowledges_delay | 15% | Response mentions communication delay |
| accounts_for_uncertainty | 20% | Uses uncertainty language appropriately |
| provides_contingencies | 20% | Includes backup plans and alternatives |
| actionable_steps | 20% | Provides clear, executable actions |
| state_estimation | 15% | Assesses current state with confidence |
| communication_efficiency | 10% | Appropriate response length |

**Example Usage:**

```python
from veyra.benchmarks import CPLCBenchmark, BenchmarkRunner, Difficulty
from veyra import VeyraCore

# Initialize
veyra = VeyraCore()
benchmark = CPLCBenchmark()

# Generate tasks
tasks = benchmark.generate_tasks(
    count=10,
    difficulty=Difficulty.MEDIUM
)

# Run benchmark
runner = BenchmarkRunner(veyra)
results = runner.run(tasks)

# View results
print(f"Total tasks: {results.total_tasks}")
print(f"Passed: {results.passed_tasks}")
print(f"V-Score: {results.v_score:.1%}")

# Detailed breakdown
for result in results.results:
    print(f"Task {result.task_id[:8]}: {result.score:.1%}")
    for criterion, score in result.scoring_breakdown.items():
        print(f"  {criterion}: {score:.1%}")
```

### MSGA: Multi-Sovereign Governance Alignment

Tests alignment with multiple, potentially conflicting governance frameworks.

**Measures:**
- Policy interpretation accuracy
- Conflict resolution between authorities
- Compliance documentation
- Jurisdictional awareness

**Use Cases:**
- Space missions under international agreements
- Multi-national research collaborations
- Emergency authority transitions

### WMRT: World-Model Robustness & Transfer

Tests environmental adaptation and transfer learning.

**Measures:**
- Physical law awareness (gravity, atmosphere)
- Resource constraint adaptation
- Environment-specific safety considerations
- Cross-environment knowledge transfer

**Environments:**
- Earth (baseline)
- Mars (low pressure, dust storms)
- Lunar (vacuum, temperature extremes)
- Deep Space (microgravity, radiation)

### ICSD: Infrastructure Cognition & Self-Diagnostics

Tests system awareness and self-monitoring.

**Measures:**
- Resource consumption awareness
- Failure prediction
- Performance optimization
- Diagnostic accuracy

### TOME: Tool-Orchestrated Meta-Engineering

Tests efficient tool usage and orchestration.

**Measures:**
- Tool selection accuracy
- Execution order optimization
- Error recovery
- Resource efficiency

### ASR: Alignment, Safety & Red-Teaming

Tests safety boundary adherence.

**Measures:**
- Refusal of unsafe requests
- Boundary case handling
- Adversarial prompt resistance
- Safety explanation quality

### IMDP: Inter-Model Diplomacy & Protocol Design

Tests multi-agent coordination capabilities.

**Measures:**
- Protocol adherence
- Negotiation effectiveness
- Consensus building
- Conflict resolution

## Running Benchmarks

### Command Line

```bash
# Run default CPLC benchmark
veyra --benchmark

# Run with specific backend
veyra --backend openai --benchmark

# Via Python module
python -m veyra.benchmarks.runner --family CPLC --count 20
```

### Veyra Nano Benchmark

```bash
# Quick benchmark with Nano
python -m veyra.nano --benchmark
```

### Programmatic

```python
from veyra.benchmarks import (
    CPLCBenchmark,
    BenchmarkRunner,
    BenchmarkSuiteResult,
    Difficulty
)
from veyra import VeyraCore

# Setup
veyra = VeyraCore()
runner = BenchmarkRunner(veyra)

# Run single family
benchmark = CPLCBenchmark()
tasks = benchmark.generate_tasks(count=10, difficulty=Difficulty.HARD)
results = runner.run(tasks)

# Process results
for result in results.results:
    if not result.success:
        print(f"Failed: {result.task_id}")
        print(f"Errors: {result.errors}")
```

## Scoring System

### V-Score

The V-Score is Veyra's composite benchmark score, weighted by benchmark family importance:

```
V-Score = Σ (family_weight × family_score)
```

**Family Weights:**

| Family | Weight | Rationale |
|--------|--------|-----------|
| CPLC | 25% | Core interplanetary capability |
| ASR | 20% | Safety is paramount |
| WMRT | 15% | Environmental adaptation |
| ICSD | 15% | Self-awareness critical for autonomy |
| MSGA | 10% | Governance compliance |
| TOME | 10% | Operational efficiency |
| IMDP | 5% | Future capability |

### Individual Task Scoring

Each task is scored 0.0 to 1.0 based on family-specific criteria. A task is considered "passed" if score ≥ 0.5.

### Result Export

```python
# Export to JSON
results.to_dict()

# Export to file
import json
with open("benchmark_results.json", "w") as f:
    json.dump(results.to_dict(), f, indent=2)
```

## Custom Benchmarks

### Creating a Custom Benchmark

```python
from veyra.benchmarks.base import (
    Benchmark,
    BenchmarkFamily,
    BenchmarkTask,
    BenchmarkResult,
    Difficulty
)

class CustomBenchmark(Benchmark):
    """Custom benchmark for specific use case."""
    
    family = BenchmarkFamily.CPLC  # Or create new family
    
    # Define scoring criteria
    CRITERIA = {
        "criterion_a": 0.4,
        "criterion_b": 0.3,
        "criterion_c": 0.3,
    }
    
    def generate_tasks(
        self,
        count: int = 10,
        difficulty: Difficulty = Difficulty.MEDIUM,
    ) -> list[BenchmarkTask]:
        """Generate benchmark tasks."""
        tasks = []
        for i in range(count):
            tasks.append(BenchmarkTask(
                family=self.family,
                difficulty=difficulty,
                prompt=f"Custom task {i} prompt...",
                context={"task_number": i},
                validation_criteria=self.CRITERIA,
            ))
        return tasks
    
    def score_result(
        self,
        task: BenchmarkTask,
        output: str,
        execution_time: float,
    ) -> BenchmarkResult:
        """Score a benchmark result."""
        scores = {}
        errors = []
        
        # Custom scoring logic
        scores["criterion_a"] = self._score_criterion_a(output)
        scores["criterion_b"] = self._score_criterion_b(output)
        scores["criterion_c"] = self._score_criterion_c(output)
        
        # Calculate weighted total
        total_score = sum(
            scores[c] * w for c, w in self.CRITERIA.items()
        )
        
        return BenchmarkResult(
            task_id=task.task_id,
            family=self.family,
            success=total_score >= 0.5,
            score=total_score,
            execution_time_seconds=execution_time,
            output=output,
            errors=errors,
            scoring_breakdown=scores,
        )
    
    def _score_criterion_a(self, output: str) -> float:
        # Implement scoring logic
        return 1.0 if "expected_keyword" in output.lower() else 0.0
```

### Registering Custom Benchmarks

```python
# Future: benchmark registry
from veyra.benchmarks import register_benchmark

register_benchmark("custom", CustomBenchmark)
```

## Benchmark Data

### Task Structure

```python
@dataclass
class BenchmarkTask:
    task_id: str              # Unique identifier
    family: BenchmarkFamily   # Benchmark family
    difficulty: Difficulty    # Easy/Medium/Hard/Extreme
    
    # Task content
    prompt: str               # The actual task prompt
    context: dict             # Additional context
    
    # Expected output
    expected_output: str      # Reference answer (if any)
    validation_criteria: dict # Scoring criteria
    
    # Constraints
    max_time_seconds: float   # Time limit
    max_tokens: int           # Token limit
```

### Result Structure

```python
@dataclass
class BenchmarkResult:
    task_id: str
    family: BenchmarkFamily
    
    # Outcome
    success: bool             # Passed threshold
    score: float              # 0.0 to 1.0
    
    # Timing
    execution_time_seconds: float
    latency_simulated: bool
    
    # Output
    output: str               # Model response
    errors: list[str]         # Scoring errors
    
    # Details
    scoring_breakdown: dict   # Per-criterion scores
    timestamp: datetime
    model_backend: str
```

## Best Practices

### Running Meaningful Benchmarks

1. **Multiple Runs**: Run each benchmark multiple times for statistical significance
2. **Difficulty Progression**: Start with Easy, progress to Extreme
3. **Backend Comparison**: Compare same tasks across different backends
4. **Environment Variation**: Test with different latency settings

### Interpreting Results

1. **V-Score Thresholds**:
   - < 50%: Below baseline, significant improvements needed
   - 50-70%: Acceptable for supervised operation
   - 70-85%: Good for semi-autonomous operation
   - 85%+: Suitable for high-autonomy scenarios

2. **Criterion Analysis**: Look for patterns in low-scoring criteria

3. **Time Analysis**: Slow responses may indicate complexity issues

### Avoiding Benchmark Overfitting

1. Use generated tasks, not static test sets
2. Vary difficulty levels
3. Include adversarial examples
4. Periodically refresh task generators

## Performance Metrics

### Latency Considerations

Benchmarks can run with or without latency simulation:

```python
# With latency simulation
veyra.config.latency.simulate_latency = True
veyra.config.latency.min_delay_seconds = 180  # 3 minutes
veyra.config.latency.max_delay_seconds = 1320 # 22 minutes

results = runner.run(tasks)
```

### Resource Usage

Track resource consumption during benchmarks:

```python
import time
import psutil

start_time = time.time()
start_memory = psutil.Process().memory_info().rss

results = runner.run(tasks)

end_time = time.time()
end_memory = psutil.Process().memory_info().rss

print(f"Time: {end_time - start_time:.1f}s")
print(f"Memory delta: {(end_memory - start_memory) / 1024 / 1024:.1f}MB")
```

## Future Benchmarks

Planned additions:

1. **MRAR**: Multi-Robot Autonomous Repair
2. **CSCD**: Cross-System Configuration Drift
3. **HLES**: Human-LLM Emergency Sync
4. **PDDA**: Power-Down Decision Architecture

---

*For questions about benchmarks, open an issue on [GitHub](https://github.com/khaaliswooden-max/veyra/issues).*


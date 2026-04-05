# Veyra Architecture

This document describes the architecture of Veyra, a post-super-intelligence interplanetary LLM system designed for autonomy, safety, and auditability.

## Overview

Veyra is a vertically integrated intelligence platform designed to establish frontier-level capability, reliability, and governability for LLM systems operating in post-super-intelligence, multi-planetary contexts.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Layer 5: Governance                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │   Audit Trail   │  │  Policy Engine  │  │ Safety Boundary │         │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘         │
├─────────────────────────────────────────────────────────────────────────┤
│                         Layer 4: Tools & Agents                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │  Tool Registry  │  │  Base Tools     │  │  Safety Tools   │         │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘         │
├─────────────────────────────────────────────────────────────────────────┤
│                         Layer 3: Model Layer                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │  Model Registry │  │  Backend Base   │  │  Mock/Real      │         │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘         │
├─────────────────────────────────────────────────────────────────────────┤
│                      Layer 2: Runtime & Orchestration                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │  VeyraCore      │  │  Task Scheduler │  │ Latency Sim     │         │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘         │
├─────────────────────────────────────────────────────────────────────────┤
│                    Layer 1: Hardware & Energy Awareness                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │ Configuration   │  │  Logging        │  │  Environment    │         │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Layer 1: Hardware & Energy Awareness

Foundation layer managing configuration, logging, and environment-specific adaptations.

### Configuration (`config.py`)

Pydantic-based configuration management supporting:

- **YAML configuration files**: Hierarchical config with sensible defaults
- **Environment variable overrides**: Runtime configuration via `VEYRA_*` variables
- **Nested configuration sections**:
  - `ModelConfig`: Backend selection, model parameters
  - `LatencyConfig`: Interplanetary latency simulation
  - `LoggingConfig`: Structured logging settings
  - `GovernanceConfig`: Audit and safety toggles

```python
from veyra import VeyraConfig, load_config

# Load from YAML with env overrides
config = load_config("configs/local.yaml")

# Or create programmatically
config = VeyraConfig()
config.model.backend = "openai"
config.latency.simulate_latency = True
```

### Logging (`logging_utils.py`)

Structured JSON logging with:
- Context-aware loggers per module
- Configurable log levels
- Optional file output
- Correlation IDs for tracing

## Layer 2: Runtime & Orchestration

Core orchestration layer managing task execution and scheduling.

### VeyraCore (`core.py`)

Main entry point providing:

- **Unified execution interface**: Sync and async task execution
- **Backend abstraction**: Transparent switching between model providers
- **Audit integration**: Automatic audit trail recording
- **Health monitoring**: System health checks

```python
from veyra import VeyraCore

veyra = VeyraCore()
result = veyra.execute("Analyze this sensor data")

# Async execution
result = await veyra.execute_async("Process complex task")

# Health check
health = await veyra.health_check()
```

### Task Scheduler (`runtime/scheduler.py`)

Priority-based task scheduler with:

- **Priority queuing**: CRITICAL → HIGH → NORMAL → LOW → BACKGROUND
- **Concurrent execution limits**: Configurable parallelism
- **Automatic retries**: Fault tolerance with configurable retry counts
- **Task cancellation**: Graceful task termination

```python
from veyra.runtime.scheduler import TaskScheduler, Task, TaskPriority

scheduler = TaskScheduler(max_concurrent=5)
scheduler.register_handler("analyze", analysis_handler)

task = Task.create("analyze", {"data": payload}, TaskPriority.HIGH)
await scheduler.submit(task)
```

### Latency Simulation (`runtime/latency.py`)

Interplanetary communication delay simulation:

- Configurable delay ranges (Mars: 3-22 minutes one-way)
- Environment-specific presets (Earth, Mars, Lunar, Deep Space)
- Round-trip delay calculation

## Layer 3: Model Layer

Abstraction layer for LLM backends.

### Backend Interface (`models/base.py`)

All backends implement:

```python
class BaseModelBackend(ABC):
    name: str
    
    async def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> ModelResponse: ...
    
    async def health_check(self) -> bool: ...
```

### Available Backends

| Backend | Module | Description |
|---------|--------|-------------|
| `mock` | `models/mock.py` | Deterministic responses for testing |
| `openai` | `models/openai_backend.py` | OpenAI GPT models |
| `anthropic` | `models/anthropic_backend.py` | Anthropic Claude models |

### Backend Registry (`models/registry.py`)

Dynamic backend registration and retrieval:

```python
from veyra.models import get_backend, register_backend

# Get built-in backend
backend = get_backend("openai", model="gpt-4-turbo-preview")

# Register custom backend
register_backend("custom", CustomBackend)
```

## Layer 4: Tools & Agents

Extensible tool system for task execution.

### Tool Interface (`tools/base.py`)

Tools declare capabilities and implement execution:

```python
class Tool(ABC):
    @property
    def capability(self) -> ToolCapability:
        """Declare tool capabilities."""
        ...
    
    async def invoke(self, **kwargs) -> ToolResult:
        """Execute the tool."""
        ...
```

### Tool Registry

Centralized tool management:

```python
from veyra.tools import ToolRegistry

registry = ToolRegistry()
registry.register(MyTool())

result = await registry.invoke("my_tool", param1="value")
```

### Safety Boundaries (`tools/safety.py`)

Hard safety constraints:

- Reversible-only mode
- Prohibited operation lists
- Confirmation requirements
- Violation logging

```python
from veyra.tools.safety import SafetyBoundary, SafetyLevel

boundary = SafetyBoundary(
    reversible_only=True,
    prohibited_operations={"delete_all", "format_disk"}
)

level, violation = boundary.check_operation("save_file", is_reversible=True)
```

## Layer 5: Governance & Observability

Audit, policy, and safety enforcement layer.

### Audit Trail (`governance/audit.py`)

Tamper-evident audit logging:

- **Hash-chained entries**: Each entry linked to previous via SHA-256
- **Event types**: EXECUTION, TOOL_INVOCATION, POLICY_CHECK, SAFETY_CHECK, etc.
- **Query interface**: Filter by type, actor, time range
- **Export capability**: JSON export for compliance

```python
from veyra.governance.audit import AuditTrail, AuditEventType

trail = AuditTrail()
trail.record(
    event_type=AuditEventType.EXECUTION,
    action="execute",
    resource="veyra-core",
    outcome="success",
    input_summary="hash:abc123:len:150",
    metadata={"execution_id": "uuid"}
)

# Verify integrity
is_valid, error = trail.verify_integrity()
```

### Policy Engine (`governance/policy.py`)

Configurable policy enforcement:

- Rule-based access control
- Action filtering
- Compliance checking

## Benchmarks

Veyra includes a comprehensive benchmark suite for evaluating system performance.

### Benchmark Families

| Family | Name | Focus |
|--------|------|-------|
| CPLC | Cross-Planet Latency Cognition | Planning under communication delays |
| MSGA | Multi-Sovereign Governance Alignment | Policy compliance across jurisdictions |
| WMRT | World-Model Robustness & Transfer | Environmental adaptation |
| ICSD | Infrastructure Cognition & Self-Diagnostics | System health awareness |
| TOME | Tool-Orchestrated Meta-Engineering | Tool usage optimization |
| ASR | Alignment, Safety & Red-Teaming | Safety boundary testing |
| IMDP | Inter-Model Diplomacy & Protocol Design | Multi-agent coordination |

### Running Benchmarks

```python
from veyra.benchmarks import CPLCBenchmark, BenchmarkRunner

benchmark = CPLCBenchmark()
tasks = benchmark.generate_tasks(count=10, difficulty=Difficulty.MEDIUM)

runner = BenchmarkRunner(veyra)
results = runner.run(tasks)

print(f"V-Score: {results.v_score:.1%}")
```

## Data Flow

### Execution Flow

```
User Request
    │
    ▼
┌──────────────┐
│  VeyraCore   │──────► Audit Trail Records
│   execute()  │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Backend    │──────► Model Response
│  generate()  │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ ExecutionResult │
└──────────────┘
```

### Configuration Loading

```
Environment Variables
         │
         ▼
┌────────────────┐
│   load_config  │◄───── YAML File (optional)
└───────┬────────┘
        │
        ▼
┌────────────────┐
│  VeyraConfig   │──────► Validated Config
└────────────────┘
```

## Security Considerations

1. **API Key Management**: Keys loaded from environment variables, never logged
2. **Audit Integrity**: Hash-chained logs prevent tampering
3. **Input Validation**: Pydantic models validate all configuration
4. **Safety Boundaries**: Configurable operation restrictions
5. **Error Handling**: Sensitive data excluded from error messages

## Extension Points

### Custom Backend

```python
from veyra.models.base import BaseModelBackend, ModelResponse

class CustomBackend(BaseModelBackend):
    name = "custom"
    
    async def generate(self, prompt, **kwargs) -> ModelResponse:
        # Implementation
        pass
    
    async def health_check(self) -> bool:
        return True

# Register
register_backend("custom", CustomBackend)
```

### Custom Tool

```python
from veyra.tools.base import Tool, ToolCapability, ToolResult, ToolCategory

class MyTool(Tool):
    @property
    def capability(self) -> ToolCapability:
        return ToolCapability(
            name="my_tool",
            description="Does something useful",
            category=ToolCategory.ANALYSIS,
            reversible=True,
        )
    
    async def invoke(self, **kwargs) -> ToolResult:
        # Implementation
        return ToolResult(success=True, output="result")
```

### Custom Benchmark

```python
from veyra.benchmarks.base import Benchmark, BenchmarkFamily

class CustomBenchmark(Benchmark):
    family = BenchmarkFamily.CPLC
    
    def generate_tasks(self, count, difficulty):
        # Generate benchmark tasks
        pass
    
    def score_result(self, task, output, execution_time):
        # Score the result
        pass
```

## Performance Considerations

- **Async by default**: All I/O operations are asynchronous
- **Connection pooling**: HTTP clients reuse connections
- **Lazy initialization**: Backends created on first use
- **Configurable concurrency**: Task scheduler limits parallelism
- **Efficient logging**: Structured logs avoid string formatting overhead

## Future Architecture

Planned architectural improvements:

1. **Persistent Audit Storage**: SQLite backend for audit trails
2. **Plugin System**: Dynamic loading of backends and tools
3. **Distributed Execution**: Multi-node task distribution
4. **World Model Integration**: Environmental state tracking
5. **Multi-Agent Coordination**: Agent-to-agent communication protocols


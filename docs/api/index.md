# Veyra API Reference

Complete API documentation for the Veyra Python package.

## Quick Navigation

- [Core Module](#core-module)
- [Configuration](#configuration)
- [Model Backends](#model-backends)
- [Governance](#governance)
- [Benchmarks](#benchmarks)
- [Tools](#tools)
- [Runtime](#runtime)

---

## Core Module

### `veyra.VeyraCore`

Main entry point for the Veyra system.

```python
from veyra import VeyraCore
```

#### Constructor

```python
VeyraCore(
    config: VeyraConfig | None = None,
    config_path: str | None = None,
    audit_trail: AuditTrail | None = None,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `config` | `VeyraConfig | None` | `None` | Configuration instance |
| `config_path` | `str | None` | `None` | Path to YAML config file |
| `audit_trail` | `AuditTrail | None` | `None` | Custom audit trail instance |

#### Methods

##### `execute(task, *, system_prompt=None, **kwargs) -> ExecutionResult`

Execute a task synchronously.

```python
result = veyra.execute("Analyze this data")
result = veyra.execute({"prompt": "Analyze", "context": "sensor data"})
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `task` | `dict | str` | Task specification or prompt string |
| `system_prompt` | `str | None` | Override system prompt |
| `**kwargs` | `Any` | Additional model parameters |

**Returns:** `ExecutionResult`

##### `async execute_async(task, *, system_prompt=None, **kwargs) -> ExecutionResult`

Execute a task asynchronously.

```python
result = await veyra.execute_async("Analyze this data")
```

##### `async health_check() -> dict[str, Any]`

Check system health.

```python
health = await veyra.health_check()
print(health["status"])  # "healthy" or "degraded"
```

##### `get_audit_log() -> list[dict[str, Any]]`

Get the internal audit log.

```python
log = veyra.get_audit_log()
for entry in log:
    print(f"{entry['execution_id']}: {entry['success']}")
```

##### `export_audit_log(path: str | Path) -> None`

Export audit log to JSON file.

```python
veyra.export_audit_log("audit_export.json")
```

##### `get_audit_trail() -> AuditTrail | None`

Get the AuditTrail instance (None if audit disabled).

##### `verify_audit_integrity() -> tuple[bool, str | None]`

Verify audit trail integrity.

```python
is_valid, error = veyra.verify_audit_integrity()
if not is_valid:
    print(f"Integrity error: {error}")
```

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `config` | `VeyraConfig` | Current configuration |
| `backend` | `BaseModelBackend` | Model backend instance |
| `audit_trail` | `AuditTrail | None` | Audit trail instance |

---

### `veyra.core.ExecutionResult`

Result of a Veyra execution.

#### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `content` | `str` | Response content |
| `success` | `bool` | Whether execution succeeded |
| `error` | `str | None` | Error message if failed |
| `metadata` | `dict[str, Any]` | Execution metadata |
| `model_response` | `ModelResponse | None` | Raw model response |
| `execution_id` | `str` | Unique execution ID |
| `timestamp` | `datetime` | Execution timestamp |

#### Methods

##### `to_dict() -> dict[str, Any]`

Convert to dictionary for serialization.

---

## Configuration

### `veyra.VeyraConfig`

Main configuration class.

```python
from veyra import VeyraConfig
```

#### Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `system_name` | `str` | `"Veyra"` | System identifier |
| `version` | `str` | `"0.1.0"` | Version string |
| `model` | `ModelConfig` | `ModelConfig()` | Model configuration |
| `latency` | `LatencyConfig` | `LatencyConfig()` | Latency simulation |
| `logging` | `LoggingConfig` | `LoggingConfig()` | Logging settings |
| `governance` | `GovernanceConfig` | `GovernanceConfig()` | Governance settings |
| `world_model_enabled` | `bool` | `False` | Enable world model |
| `environment` | `str` | `"earth"` | Target environment |

#### Class Methods

##### `from_yaml(path: str | Path) -> VeyraConfig`

Load configuration from YAML file.

```python
config = VeyraConfig.from_yaml("configs/production.yaml")
```

##### `from_dict(data: dict[str, Any]) -> VeyraConfig`

Create from dictionary.

##### `from_env() -> VeyraConfig`

Create from environment variables.

#### Methods

##### `apply_env_overrides() -> VeyraConfig`

Apply environment variable overrides.

---

### `veyra.config.ModelConfig`

Model backend configuration.

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `backend` | `str` | `"mock"` | Backend name |
| `openai_model` | `str` | `"gpt-4-turbo-preview"` | OpenAI model |
| `anthropic_model` | `str` | `"claude-3-opus-20240229"` | Anthropic model |
| `temperature` | `float` | `0.7` | Sampling temperature |
| `max_tokens` | `int` | `4096` | Maximum tokens |

### `veyra.config.LatencyConfig`

Latency simulation configuration.

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `simulate_latency` | `bool` | `False` | Enable simulation |
| `min_delay_seconds` | `float` | `180.0` | Minimum delay (3 min) |
| `max_delay_seconds` | `float` | `1320.0` | Maximum delay (22 min) |

### `veyra.config.GovernanceConfig`

Governance configuration.

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `audit_enabled` | `bool` | `True` | Enable audit trails |
| `safety_boundaries` | `bool` | `True` | Enable safety checks |
| `reversible_only` | `bool` | `False` | Only reversible ops |

---

### `veyra.load_config`

```python
from veyra import load_config

config = load_config()  # Default config with env overrides
config = load_config("configs/local.yaml")  # From file
```

---

## Model Backends

### `veyra.models.BaseModelBackend`

Abstract base class for model backends.

```python
from veyra.models import BaseModelBackend
```

#### Abstract Methods

##### `async generate(prompt, *, system_prompt=None, temperature=0.7, max_tokens=4096, **kwargs) -> ModelResponse`

Generate a response.

##### `async health_check() -> bool`

Check backend health.

---

### `veyra.models.ModelResponse`

Standardized response from model backends.

| Attribute | Type | Description |
|-----------|------|-------------|
| `content` | `str` | Response content |
| `model` | `str` | Model identifier |
| `backend` | `str` | Backend name |
| `created_at` | `datetime` | Creation timestamp |
| `latency_ms` | `float` | Response latency |
| `prompt_tokens` | `int` | Input token count |
| `completion_tokens` | `int` | Output token count |
| `total_tokens` | `int` | Total tokens |
| `request_id` | `str | None` | Request identifier |
| `trace_id` | `str | None` | Trace identifier |
| `raw_response` | `dict | None` | Raw API response |

---

### `veyra.models.get_backend`

Get a backend instance by name.

```python
from veyra.models import get_backend

backend = get_backend("mock")
backend = get_backend("openai", model="gpt-4-turbo-preview")
```

---

### `veyra.models.MockBackend`

Mock backend for testing.

```python
from veyra.models import MockBackend

backend = MockBackend(
    latency_range=(0.1, 0.5),  # Simulated latency
    deterministic=True,        # Reproducible responses
)
```

---

## Governance

### `veyra.governance.audit.AuditTrail`

Tamper-evident audit logging.

```python
from veyra.governance.audit import AuditTrail, AuditEventType
```

#### Constructor

```python
AuditTrail(persist_path: Path | None = None)
```

#### Methods

##### `record(event_type, action, resource="", outcome="success", actor="system", input_summary=None, output_summary=None, metadata=None) -> AuditEntry`

Record an audit event.

```python
entry = trail.record(
    event_type=AuditEventType.EXECUTION,
    action="execute",
    resource="veyra-core",
    outcome="success",
    input_summary="hash:abc123:len:100",
    metadata={"execution_id": "uuid"}
)
```

##### `verify_integrity() -> tuple[bool, str | None]`

Verify hash chain integrity.

```python
is_valid, error = trail.verify_integrity()
```

##### `get_entries(event_type=None, actor=None, since=None, limit=100) -> list[AuditEntry]`

Query audit entries.

```python
entries = trail.get_entries(
    event_type=AuditEventType.EXECUTION,
    since=datetime.now() - timedelta(hours=1),
    limit=50
)
```

##### `export(path: Path) -> None`

Export to JSON file.

---

### `veyra.governance.audit.AuditEventType`

Event type enumeration.

| Value | Description |
|-------|-------------|
| `EXECUTION` | Task execution |
| `TOOL_INVOCATION` | Tool usage |
| `POLICY_CHECK` | Policy evaluation |
| `SAFETY_CHECK` | Safety boundary check |
| `CONFIGURATION_CHANGE` | Config change |
| `ERROR` | Error event |
| `SYSTEM` | System event |

---

### `veyra.governance.audit.AuditEntry`

Single audit log entry.

| Attribute | Type | Description |
|-----------|------|-------------|
| `event_id` | `str` | Unique identifier |
| `event_type` | `AuditEventType` | Event type |
| `timestamp` | `datetime` | Event time |
| `actor` | `str` | Actor identifier |
| `actor_type` | `str` | Actor type |
| `action` | `str` | Action performed |
| `resource` | `str` | Affected resource |
| `outcome` | `str` | Result |
| `input_summary` | `str | None` | Input hash/summary |
| `output_summary` | `str | None` | Output summary |
| `metadata` | `dict` | Additional data |
| `previous_hash` | `str | None` | Hash chain link |
| `entry_hash` | `str | None` | This entry's hash |

---

## Benchmarks

### `veyra.benchmarks.CPLCBenchmark`

Cross-Planet Latency Cognition benchmark.

```python
from veyra.benchmarks import CPLCBenchmark, Difficulty

benchmark = CPLCBenchmark()
tasks = benchmark.generate_tasks(count=10, difficulty=Difficulty.MEDIUM)
```

#### Methods

##### `generate_tasks(count=10, difficulty=Difficulty.MEDIUM) -> list[BenchmarkTask]`

Generate benchmark tasks.

##### `score_result(task, output, execution_time) -> BenchmarkResult`

Score a result.

---

### `veyra.benchmarks.BenchmarkRunner`

Runs benchmarks against a VeyraCore instance.

```python
from veyra.benchmarks import BenchmarkRunner

runner = BenchmarkRunner(veyra)
results = runner.run(tasks)
```

#### Constructor

```python
BenchmarkRunner(veyra: VeyraCore)
```

#### Methods

##### `run(tasks: list[BenchmarkTask]) -> BenchmarkSuiteResult`

Run benchmark tasks.

##### `run_single(task: BenchmarkTask) -> BenchmarkResult`

Run a single task.

---

### `veyra.benchmarks.base.BenchmarkTask`

Benchmark task specification.

| Attribute | Type | Description |
|-----------|------|-------------|
| `task_id` | `str` | Unique identifier |
| `family` | `BenchmarkFamily` | Benchmark family |
| `difficulty` | `Difficulty` | Difficulty level |
| `prompt` | `str` | Task prompt |
| `context` | `dict` | Additional context |
| `expected_output` | `str | None` | Expected result |
| `validation_criteria` | `dict` | Scoring criteria |
| `max_time_seconds` | `float` | Time limit |
| `max_tokens` | `int` | Token limit |

---

### `veyra.benchmarks.base.BenchmarkResult`

Result of a benchmark task.

| Attribute | Type | Description |
|-----------|------|-------------|
| `task_id` | `str` | Task identifier |
| `family` | `BenchmarkFamily` | Benchmark family |
| `success` | `bool` | Passed threshold |
| `score` | `float` | Score (0.0-1.0) |
| `execution_time_seconds` | `float` | Time taken |
| `output` | `str` | Model output |
| `errors` | `list[str]` | Scoring errors |
| `scoring_breakdown` | `dict` | Per-criterion scores |

---

### `veyra.benchmarks.base.Difficulty`

Difficulty enumeration.

| Value | Description |
|-------|-------------|
| `EASY` | Simple tasks |
| `MEDIUM` | Standard tasks |
| `HARD` | Complex tasks |
| `EXTREME` | Maximum difficulty |

---

## Tools

### `veyra.tools.Tool`

Abstract base class for tools.

```python
from veyra.tools import Tool, ToolCapability, ToolResult
```

#### Abstract Properties

##### `capability -> ToolCapability`

Declare tool capabilities.

#### Abstract Methods

##### `async invoke(**kwargs) -> ToolResult`

Execute the tool.

---

### `veyra.tools.ToolRegistry`

Tool management and invocation.

```python
from veyra.tools import ToolRegistry

registry = ToolRegistry()
registry.register(my_tool)
result = await registry.invoke("tool_name", param="value")
```

#### Methods

##### `register(tool: Tool) -> None`

Register a tool.

##### `unregister(name: str) -> bool`

Unregister a tool.

##### `get(name: str) -> Tool | None`

Get tool by name.

##### `list_tools() -> list[ToolCapability]`

List all tools.

##### `list_by_category(category: ToolCategory) -> list[ToolCapability]`

List by category.

##### `async invoke(tool_name: str, **kwargs) -> ToolResult`

Invoke a tool.

---

### `veyra.tools.safety.SafetyBoundary`

Safety constraint enforcement.

```python
from veyra.tools.safety import SafetyBoundary, SafetyLevel

boundary = SafetyBoundary(
    reversible_only=True,
    require_confirmation=False,
    prohibited_operations={"dangerous_op"}
)

level, violation = boundary.check_operation(
    "save_file",
    is_reversible=True
)
```

#### Methods

##### `check_operation(operation_name, is_reversible=True, context=None) -> tuple[SafetyLevel, SafetyViolation | None]`

Check if operation is allowed.

##### `get_violations() -> list[SafetyViolation]`

Get recorded violations.

##### `add_prohibited_operation(operation_name: str) -> None`

Add to prohibited list.

---

## Runtime

### `veyra.runtime.scheduler.TaskScheduler`

Priority-based task scheduling.

```python
from veyra.runtime.scheduler import TaskScheduler, Task, TaskPriority

scheduler = TaskScheduler(max_concurrent=5)
scheduler.register_handler("task_type", handler_func)
await scheduler.submit(task)
```

#### Constructor

```python
TaskScheduler(
    max_concurrent: int = 5,
    default_timeout: float = 300.0,
)
```

#### Methods

##### `register_handler(task_type: str, handler: Callable) -> None`

Register task handler.

##### `async submit(task: Task) -> str`

Submit task, returns task ID.

##### `async get_status(task_id: str) -> Task | None`

Get task status.

##### `async cancel(task_id: str) -> bool`

Cancel a task.

##### `stats() -> dict[str, int]`

Get scheduler statistics.

---

### `veyra.runtime.scheduler.Task`

Schedulable task.

```python
from veyra.runtime.scheduler import Task, TaskPriority

task = Task.create(
    name="analyze",
    payload={"data": "..."},
    priority=TaskPriority.HIGH
)
```

#### Class Methods

##### `create(name, payload, priority=TaskPriority.NORMAL) -> Task`

Create a new task.

---

### `veyra.runtime.scheduler.TaskPriority`

Priority enumeration.

| Value | Level | Description |
|-------|-------|-------------|
| `CRITICAL` | 0 | Highest priority |
| `HIGH` | 1 | High priority |
| `NORMAL` | 2 | Normal priority |
| `LOW` | 3 | Low priority |
| `BACKGROUND` | 4 | Lowest priority |

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VEYRA_BACKEND` | Model backend | `mock` |
| `VEYRA_LOG_LEVEL` | Log level | `INFO` |
| `VEYRA_LOG_FILE` | Log file path | None |
| `VEYRA_SIMULATE_LATENCY` | Enable latency sim | `false` |
| `VEYRA_ENVIRONMENT` | Target environment | `earth` |
| `VEYRA_WORLD_MODEL_ENABLED` | Enable world model | `false` |
| `OPENAI_API_KEY` | OpenAI API key | Required for OpenAI |
| `ANTHROPIC_API_KEY` | Anthropic API key | Required for Anthropic |

---

## Exceptions

### Common Exceptions

| Exception | When Raised |
|-----------|-------------|
| `FileNotFoundError` | Config file not found |
| `ValueError` | Invalid parameter |
| `TimeoutError` | Task timeout |
| `ConnectionError` | Backend unavailable |

---

## Type Hints

Veyra is fully typed. Import types:

```python
from veyra import VeyraCore, VeyraConfig
from veyra.core import ExecutionResult
from veyra.models import ModelResponse, BaseModelBackend
from veyra.governance.audit import AuditTrail, AuditEntry, AuditEventType
from veyra.benchmarks.base import (
    BenchmarkTask,
    BenchmarkResult,
    BenchmarkSuiteResult,
    Difficulty,
    BenchmarkFamily,
)
from veyra.tools.base import Tool, ToolCapability, ToolResult, ToolCategory
from veyra.tools.safety import SafetyBoundary, SafetyLevel, SafetyViolation
from veyra.runtime.scheduler import Task, TaskScheduler, TaskPriority, TaskStatus
```

---

*For the latest API documentation, see the [source code](https://github.com/khaaliswooden-max/veyra/tree/main/src/veyra).*


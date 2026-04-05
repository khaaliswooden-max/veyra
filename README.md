# Veyra

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**Post-Super-Intelligence Interplanetary LLM System**

Veyra is a vertically integrated intelligence platform designed for autonomy, safety, and auditability in high-stakes, latency-constrained environments.

## Key Features

- **Multiple Model Backends**: OpenAI, Anthropic, Ollama, and Mock backends
- **Interplanetary Latency Simulation**: Test decision-making under 3-22 minute delays
- **Tamper-Evident Audit Trails**: Hash-chained logging for complete traceability
- **Safety Boundaries**: Configurable constraints for tool operations
- **Comprehensive Benchmarks**: CPLC and other benchmark families
- **Zero-Dependency Mode**: Veyra Nano single-file deployment

## Quick Start

### Installation

```bash
# Basic installation
pip install veyra

# With OpenAI support
pip install veyra[openai]

# With all backends
pip install veyra[all]

# Development installation
pip install -e ".[dev]"
```

### Basic Usage

```python
from veyra import VeyraCore

# Initialize (uses mock backend by default)
veyra = VeyraCore()

# Execute a task
result = veyra.execute("Analyze sensor data and recommend actions")

print(result.content)
print(f"Success: {result.success}")
print(f"Execution ID: {result.execution_id}")
```

### Command Line

```bash
# Single prompt
veyra "What is the system status?"

# Interactive mode
veyra --interactive

# With specific backend
veyra --backend openai "Analyze this data"

# Run benchmark
veyra --benchmark
```

### Veyra Nano (Zero Dependencies)

```bash
# Download single file
curl -O https://raw.githubusercontent.com/khaaliswooden-max/veyra/main/nano.py

# Run directly
python nano.py "Your prompt here"

# Interactive mode
python nano.py

# Benchmark
python nano.py --benchmark
```

## Architecture

Veyra uses a five-layer architecture:

```
┌─────────────────────────────────────────────────────────────────┐
│  Layer 5: Governance - Audit trails, policy, safety boundaries  │
├─────────────────────────────────────────────────────────────────┤
│  Layer 4: Tools & Agents - Tool registry, safety checks         │
├─────────────────────────────────────────────────────────────────┤
│  Layer 3: Model Layer - Backend abstraction, registry           │
├─────────────────────────────────────────────────────────────────┤
│  Layer 2: Runtime & Orchestration - VeyraCore, scheduler        │
├─────────────────────────────────────────────────────────────────┤
│  Layer 1: Hardware & Energy - Configuration, logging            │
└─────────────────────────────────────────────────────────────────┘
```

See [Architecture Documentation](docs/architecture.md) for details.

## Configuration

### Environment Variables

```bash
export VEYRA_BACKEND=mock          # mock, openai, anthropic
export VEYRA_LOG_LEVEL=INFO        # DEBUG, INFO, WARNING, ERROR
export VEYRA_SIMULATE_LATENCY=true # Enable latency simulation
export VEYRA_AUDIT=true            # Enable audit logging

# API Keys (if using cloud backends)
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...
```

### YAML Configuration

```yaml
# configs/local.yaml
system:
  name: "My Veyra Instance"

model:
  backend: openai
  openai_model: gpt-4-turbo-preview
  temperature: 0.7

latency:
  simulate_latency: false

governance:
  audit_enabled: true
  safety_boundaries: true

environment: earth
```

```python
veyra = VeyraCore(config_path="configs/local.yaml")
```

## Model Backends

### Mock (Default)

Zero-cost, deterministic responses for development and testing:

```python
from veyra import VeyraCore

veyra = VeyraCore()  # Uses mock by default
result = veyra.execute("Test prompt")
```

### OpenAI

```python
from veyra import VeyraCore, VeyraConfig

config = VeyraConfig()
config.model.backend = "openai"
config.model.openai_model = "gpt-4-turbo-preview"

veyra = VeyraCore(config=config)
```

### Anthropic

```python
config = VeyraConfig()
config.model.backend = "anthropic"
config.model.anthropic_model = "claude-3-opus-20240229"

veyra = VeyraCore(config=config)
```

## Audit Trails

Veyra provides tamper-evident audit logging with hash-chaining:

```python
veyra = VeyraCore()

# Execute tasks
veyra.execute("Task 1")
veyra.execute("Task 2")

# Get audit log
log = veyra.get_audit_log()

# Verify integrity
is_valid, error = veyra.verify_audit_integrity()

# Export for compliance
veyra.export_audit_log("audit_export.json")

# Query audit trail directly
trail = veyra.get_audit_trail()
entries = trail.get_entries(since=datetime.now() - timedelta(hours=1))
```

## Benchmarks

Veyra includes comprehensive benchmarks for evaluating AI systems:

### CPLC: Cross-Planet Latency Cognition

Tests decision-making under communication delays:

```python
from veyra.benchmarks import CPLCBenchmark, BenchmarkRunner, Difficulty

benchmark = CPLCBenchmark()
tasks = benchmark.generate_tasks(count=10, difficulty=Difficulty.MEDIUM)

runner = BenchmarkRunner(veyra)
results = runner.run(tasks)

print(f"V-Score: {results.v_score:.1%}")
print(f"Passed: {results.passed_tasks}/{results.total_tasks}")
```

See [Benchmark Documentation](docs/benchmarks.md) for all benchmark families.

## Safety Boundaries

Configure operation constraints:

```python
from veyra.tools.safety import SafetyBoundary, SafetyLevel

boundary = SafetyBoundary(
    reversible_only=True,           # Only reversible operations
    prohibited_operations={"delete_all", "format_disk"},
)

level, violation = boundary.check_operation("save_file", is_reversible=True)
```

## Task Scheduler

Priority-based task scheduling with async support:

```python
from veyra.runtime.scheduler import TaskScheduler, Task, TaskPriority

scheduler = TaskScheduler(max_concurrent=5)

async def handler(payload: dict):
    return {"result": "processed"}

scheduler.register_handler("process", handler)

task = Task.create("process", {"data": "..."}, TaskPriority.HIGH)
await scheduler.submit(task)
```

## Project Structure

```
veyra/
├── src/veyra/
│   ├── __init__.py          # Package exports
│   ├── __main__.py          # CLI entry point
│   ├── core.py              # VeyraCore main class
│   ├── config.py            # Configuration management
│   ├── logging_utils.py     # Structured logging
│   ├── models/              # Model backends
│   │   ├── base.py          # Backend interface
│   │   ├── mock.py          # Mock backend
│   │   ├── openai_backend.py
│   │   ├── anthropic_backend.py
│   │   └── registry.py      # Backend registry
│   ├── governance/          # Audit and policy
│   │   ├── audit.py         # Audit trail system
│   │   └── policy.py        # Policy engine
│   ├── benchmarks/          # Benchmark suite
│   │   ├── base.py          # Benchmark interfaces
│   │   ├── cplc.py          # CPLC benchmark
│   │   └── runner.py        # Benchmark runner
│   ├── tools/               # Tool system
│   │   ├── base.py          # Tool interfaces
│   │   └── safety.py        # Safety boundaries
│   └── runtime/             # Runtime components
│       ├── scheduler.py     # Task scheduler
│       └── latency.py       # Latency simulation
├── tests/                   # Test suite
├── configs/                 # Configuration files
├── docs/                    # Documentation
│   ├── architecture.md      # Architecture overview
│   ├── benchmarks.md        # Benchmark guide
│   └── api/                 # API reference
├── nano.py                  # Single-file deployment
├── pyproject.toml           # Project configuration
└── README.md                # This file
```

## Documentation

- [Quickstart Guide](quickstart.md)
- [Architecture Overview](docs/architecture.md)
- [Benchmark Documentation](docs/benchmarks.md)
- [API Reference](docs/api/index.md)
- [Contributing Guidelines](CONTRIBUTING.md)
- [Security Policy](SECURITY.md)
- [Changelog](CHANGELOG.md)

## Development

### Setup

```bash
git clone https://github.com/khaaliswooden-max/veyra.git
cd veyra
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e ".[dev]"
```

### Running Tests

```bash
# All tests
pytest tests/

# With coverage
pytest --cov=src/veyra tests/

# Specific test file
pytest tests/test_core.py -v
```

### Code Quality

```bash
# Format
black src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/

# Security audit
pip-audit
```

## Architecture Decision Records

- [ADR-0001: Model Backend Abstraction](0001-model-backend-abstraction.md)
- [ADR-0002: Audit Trail Design](0002-audit-trail-design.md)

## Roadmap

- [ ] SQLite-backed audit persistence
- [ ] Ollama backend integration
- [ ] Plugin system for custom backends
- [ ] Multi-agent coordination protocols
- [ ] World model reasoning
- [ ] Distributed task execution

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Security

See [SECURITY.md](SECURITY.md) for vulnerability reporting.

## License

MIT License - see [LICENSE](LICENSE) for details.

---

**Veyra** - Built for the future of autonomous AI systems.

*Zuup Innovation Lab*

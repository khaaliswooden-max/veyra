# Veyra Quickstart Guide

Get Veyra running in under 5 minutes.

## Prerequisites

- Python 3.11 or higher
- pip or uv

## Installation

### Option 1: pip (recommended)

```bash
# Basic installation
pip install veyra

# With OpenAI support
pip install veyra[openai]

# With all backends
pip install veyra[all]
```

### Option 2: From source

```bash
git clone https://github.com/khaaliswooden-max/veyra.git
cd veyra
pip install -e ".[dev]"
```

### Option 3: Veyra Nano (zero dependencies)

```bash
# Download single file
curl -O https://raw.githubusercontent.com/khaaliswooden-max/veyra/main/src/veyra/nano.py

# Run directly
python nano.py
```

## Quick Test

```bash
# Verify installation
python -c "from veyra import VeyraCore; print('Veyra OK')"

# Run with mock backend (no API key needed)
python -m veyra --backend mock "Hello Veyra"
```

## Basic Usage

### Python API

```python
from veyra import VeyraCore

# Initialize with mock backend (default)
veyra = VeyraCore()

# Execute a task
result = veyra.execute("Analyze this sensor data")
print(result.content)

# Check execution metadata
print(f"Success: {result.success}")
print(f"Execution ID: {result.execution_id}")
print(f"Latency: {result.latency_ms}ms")
```

### Command Line

```bash
# Single prompt
veyra "What is the current system status?"

# Interactive mode
veyra --interactive

# With specific backend
veyra --backend openai "Analyze this data"

# Run benchmark
veyra --benchmark
```

### Veyra Nano CLI

```bash
# Interactive mode
python -m veyra.nano

# Single prompt
python -m veyra.nano "Analyze with 15-minute delay"

# Run CPLC benchmark
python -m veyra.nano --benchmark

# View audit log
python -m veyra.nano --audit
```

## Configuration

### Environment Variables

```bash
# Model backend
export VEYRA_BACKEND=mock          # mock, openai, anthropic, ollama

# API keys (if using cloud backends)
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...

# Features
export VEYRA_SIMULATE_LATENCY=true # Enable latency simulation
export VEYRA_AUDIT=true            # Enable audit logging
export VEYRA_SAFETY=true           # Enable safety boundaries

# Logging
export VEYRA_LOG_LEVEL=INFO        # DEBUG, INFO, WARNING, ERROR
```

### YAML Configuration

Create `configs/local.yaml`:

```yaml
system:
  name: "My Veyra Instance"

model:
  backend: openai
  openai_model: gpt-4-turbo-preview
  temperature: 0.7
  max_tokens: 4096

latency:
  simulate_latency: false

governance:
  audit_enabled: true
  safety_boundaries: true

environment: earth
```

Load it:

```python
veyra = VeyraCore(config_path="configs/local.yaml")
```

## Using Different Backends

### Mock (default, zero cost)

```python
veyra = VeyraCore()  # Uses mock by default
```

### OpenAI

```bash
export OPENAI_API_KEY=sk-...
```

```python
from veyra import VeyraCore, VeyraConfig

config = VeyraConfig()
config.model.backend = "openai"
config.model.openai_model = "gpt-4-turbo-preview"

veyra = VeyraCore(config=config)
```

### Anthropic

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

```python
config = VeyraConfig()
config.model.backend = "anthropic"
config.model.anthropic_model = "claude-3-opus-20240229"

veyra = VeyraCore(config=config)
```

### Ollama (local, free)

```bash
# Install Ollama from https://ollama.ai
ollama pull llama3.2:1b
```

```python
# Using Veyra Nano
from veyra.nano import VeyraNano, NanoConfig

config = NanoConfig(backend="ollama", ollama_model="llama3.2:1b")
veyra = VeyraNano(config)
```

## Working with Audit Trails

```python
veyra = VeyraCore()

# Execute some tasks
veyra.execute("Task 1")
veyra.execute("Task 2")

# Get audit log
audit = veyra.get_audit_log()
for entry in audit:
    print(f"{entry['timestamp']}: {entry['outcome']}")

# Export audit log
veyra.export_audit_log("audit_export.json")
```

## Running Benchmarks

```python
from veyra.benchmarks import CPLCBenchmark, BenchmarkRunner

# Create benchmark
benchmark = CPLCBenchmark()
tasks = benchmark.generate_tasks(count=5)

# Run with VeyraCore
runner = BenchmarkRunner(veyra)
results = runner.run(tasks)

print(f"Average score: {results.average_score:.1%}")
```

## Next Steps

- [Architecture Overview](architecture.md)
- [Benchmark Documentation](benchmarks.md)
- [API Reference](api/)
- [Contributing](../CONTRIBUTING.md)

## Troubleshooting

### "No module named 'veyra'"

```bash
pip install -e .  # If installed from source
# or
pip install veyra  # If using pip
```

### "API key not found"

```bash
# Check environment variable is set
echo $OPENAI_API_KEY

# Or use mock backend
export VEYRA_BACKEND=mock
```

### "Connection refused" (Ollama)

```bash
# Ensure Ollama is running
ollama serve

# Check it's accessible
curl http://localhost:11434/api/tags
```

---

*Need help? Open an issue on [GitHub](https://github.com/khaaliswooden-max/veyra/issues)*

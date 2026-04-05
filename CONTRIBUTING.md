# Contributing to Veyra

Thank you for your interest in contributing to Veyra! This document provides guidelines and instructions for contributing.

## Code of Conduct

Be respectful, inclusive, and constructive. We're building technology for high-stakes environments—professionalism matters.

## Getting Started

### Prerequisites

- Python 3.11+
- Git
- (Optional) Ollama for local LLM testing

### Development Setup

```bash
# Clone the repository
git clone https://github.com/khaaliswooden-max/veyra.git
cd veyra

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install with dev dependencies
pip install -e ".[dev]"

# Verify installation
pytest tests/
```

### Running Checks Locally

```bash
# Format code
black src/ tests/

# Type check
mypy src/

# Lint
ruff check src/ tests/

# Run tests with coverage
pytest --cov=src/veyra --cov-report=html tests/

# Security audit
pip-audit
```

## How to Contribute

### Reporting Bugs

1. Check existing issues first
2. Use the bug report template
3. Include:
   - Python version
   - OS and version
   - Steps to reproduce
   - Expected vs actual behavior
   - Error messages/logs

### Suggesting Features

1. Check existing issues/discussions
2. Use the feature request template
3. Explain the use case
4. Consider how it fits Veyra's mission (autonomy, safety, auditability)

### Pull Requests

#### Branch Naming

```
feat/short-description    # New feature
fix/issue-number-desc     # Bug fix
docs/what-changed         # Documentation
refactor/what-changed     # Code refactor
test/what-covered         # Test additions
ci/what-changed           # CI/CD changes
```

#### PR Process

1. **Fork** the repository
2. **Create** a feature branch from `main`
3. **Make** your changes
4. **Test** thoroughly
5. **Commit** with conventional commits
6. **Push** to your fork
7. **Open** a PR against `main`

#### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): description

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `ci`, `chore`

Examples:
```
feat(core): add retry logic to model backends
fix(audit): correct hash chain verification
docs(readme): update installation instructions
test(benchmarks): add CPLC edge case tests
```

#### PR Checklist

- [ ] Tests pass locally (`pytest tests/`)
- [ ] Code is formatted (`black src/ tests/`)
- [ ] Type hints added for new code
- [ ] Docstrings for public APIs
- [ ] CHANGELOG.md updated (if user-facing)
- [ ] No secrets/credentials committed

## Code Standards

### Python Style

- **Formatter**: Black (line length 88)
- **Linter**: Ruff
- **Type checker**: mypy (strict mode)
- **Docstrings**: Google style

### Example Code

```python
"""Module docstring explaining purpose."""

from typing import Optional

from veyra.config import VeyraConfig


def process_task(
    prompt: str,
    config: Optional[VeyraConfig] = None,
    *,
    timeout: float = 30.0,
) -> str:
    """
    Process a task with the given prompt.

    Args:
        prompt: The input prompt to process.
        config: Optional configuration override.
        timeout: Maximum execution time in seconds.

    Returns:
        The processed result as a string.

    Raises:
        ValueError: If prompt is empty.
        TimeoutError: If execution exceeds timeout.

    Example:
        >>> result = process_task("Analyze this data")
        >>> print(result)
    """
    if not prompt:
        raise ValueError("Prompt cannot be empty")

    # Implementation...
    return result
```

### Testing Standards

- **Framework**: pytest
- **Coverage target**: 70% minimum, 85% goal
- **Async tests**: Use `pytest-asyncio`
- **Mocking**: Use `unittest.mock` or `pytest-mock`

```python
import pytest
from unittest.mock import AsyncMock, patch


class TestFeature:
    """Test group description."""

    def test_happy_path(self):
        """Test normal operation."""
        result = function_under_test("valid input")
        assert result.success is True

    def test_edge_case(self):
        """Test boundary condition."""
        with pytest.raises(ValueError):
            function_under_test("")

    @pytest.mark.asyncio
    async def test_async_operation(self):
        """Test async functionality."""
        result = await async_function()
        assert result is not None
```

## Architecture Guidelines

### Adding a New Model Backend

1. Create `src/veyra/models/your_backend.py`
2. Inherit from `BaseModelBackend`
3. Implement `generate()` and `health_check()`
4. Register in `src/veyra/models/registry.py`
5. Add tests in `tests/test_models.py`
6. Document in README

```python
from veyra.models.base import BaseModelBackend, ModelResponse


class YourBackend(BaseModelBackend):
    name = "your_backend"

    async def generate(self, prompt: str, **kwargs) -> ModelResponse:
        # Implementation
        pass

    async def health_check(self) -> bool:
        # Implementation
        pass
```

### Adding a New Benchmark

1. Create `src/veyra/benchmarks/your_benchmark.py`
2. Inherit from `Benchmark`
3. Define `SCENARIOS` and `CRITERIA`
4. Implement `generate_tasks()` and `score_result()`
5. Add tests in `tests/test_benchmarks.py`

## Questions?

- **General questions**: Open a GitHub Discussion
- **Bug reports**: Open a GitHub Issue
- **Security issues**: Email security@zuup.org (see SECURITY.md)

## Recognition

Contributors are recognized in:
- CHANGELOG.md for significant contributions
- README.md contributors section (coming soon)
- Release notes

---

Thank you for contributing to Veyra! 🚀

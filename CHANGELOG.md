# Changelog

All notable changes to Veyra will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- LICENSE file (MIT)
- SECURITY.md with vulnerability disclosure policy
- CONTRIBUTING.md with contributor guidelines
- Comprehensive .gitignore
- This CHANGELOG.md

### Changed
- Enhanced CI/CD pipeline with coverage reporting
- Improved audit trail integration with VeyraCore

### Fixed
- Deprecated `asyncio.get_event_loop()` pattern in core.py
- Duplicate environment variable handling in config.py

### Security
- Added pip-audit to CI pipeline
- Added Bandit security scanning
- Added Dependabot for dependency updates

## [0.1.0] - 2024-12-03

### Added
- Initial release of Veyra
- VeyraCore main orchestration class
- Model backends: Mock, OpenAI, Anthropic
- Configuration management with YAML and environment variables
- Latency simulation for interplanetary scenarios
- CPLC benchmark (Cross-Planet Latency Cognition)
- Benchmark framework with scoring system
- Safety boundaries for tool operations
- Audit trail with hash-chaining
- Policy engine for governance
- CLI interface via `run_veyra.py`
- DevContainer support
- GitHub Actions CI workflow

### Architecture
- Five-layer architecture design
  - Layer 1: Hardware & Energy Awareness
  - Layer 2: Runtime & Orchestration
  - Layer 3: Model Layer
  - Layer 4: Tools & Agents
  - Layer 5: Governance & Observability

### Documentation
- README with project overview
- Inline docstrings for all public APIs

---

## Version History Summary

| Version | Date | Highlights |
|---------|------|------------|
| 0.1.0 | 2024-12-03 | Initial release, core architecture |

## Upgrade Notes

### Upgrading to 0.2.0 (upcoming)

No breaking changes expected. New features:
- Veyra Nano single-file mode
- SQLite-backed audit persistence
- Enhanced benchmark scoring

---

[Unreleased]: https://github.com/khaaliswooden-max/veyra/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/khaaliswooden-max/veyra/releases/tag/v0.1.0

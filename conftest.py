"""
Pytest configuration and fixtures for Veyra tests.
"""

import pytest
import tempfile
from pathlib import Path
from typing import Generator

from veyra import VeyraCore, VeyraConfig
from veyra.governance.audit import AuditTrail


@pytest.fixture
def default_config() -> VeyraConfig:
    """Create a default VeyraConfig for testing."""
    config = VeyraConfig()
    config.model.backend = "mock"
    config.governance.audit_enabled = True
    return config


@pytest.fixture
def veyra_instance(default_config: VeyraConfig) -> VeyraCore:
    """Create a VeyraCore instance with default test config."""
    return VeyraCore(config=default_config)


@pytest.fixture
def veyra_no_audit() -> VeyraCore:
    """Create a VeyraCore instance with audit disabled."""
    config = VeyraConfig()
    config.model.backend = "mock"
    config.governance.audit_enabled = False
    return VeyraCore(config=config)


@pytest.fixture
def audit_trail() -> AuditTrail:
    """Create an empty AuditTrail for testing."""
    return AuditTrail()


@pytest.fixture
def populated_audit_trail() -> AuditTrail:
    """Create an AuditTrail with some entries."""
    from veyra.governance.audit import AuditEventType
    
    audit = AuditTrail()
    audit.record(event_type=AuditEventType.SYSTEM, action="startup")
    audit.record(event_type=AuditEventType.EXECUTION, action="execute", outcome="success")
    audit.record(event_type=AuditEventType.EXECUTION, action="execute", outcome="success")
    audit.record(event_type=AuditEventType.SAFETY_CHECK, action="check", outcome="pass")
    return audit


@pytest.fixture
def tmp_audit_path(tmp_path: Path) -> Path:
    """Create a temporary path for audit persistence."""
    return tmp_path / "test_audit.jsonl"


@pytest.fixture
def config_with_latency() -> VeyraConfig:
    """Create a config with latency simulation enabled (short delays)."""
    config = VeyraConfig()
    config.model.backend = "mock"
    config.latency.simulate_latency = True
    config.latency.min_delay_seconds = 0.01  # 10ms for testing
    config.latency.max_delay_seconds = 0.05  # 50ms for testing
    return config


@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    """Return the path to test data directory."""
    return Path(__file__).parent / "data"


# Markers for test categorization
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "requires_api: marks tests that require actual API keys"
    )

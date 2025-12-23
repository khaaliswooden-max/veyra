"""
Tests for VeyraCore
"""

import pytest
import asyncio
from veyra import VeyraCore, VeyraConfig


class TestVeyraCore:
    """Test VeyraCore functionality."""

    def test_initialization_default(self):
        """Test default initialization."""
        veyra = VeyraCore()
        assert veyra.config is not None
        assert veyra.config.model.backend == "mock"

    def test_initialization_with_config(self):
        """Test initialization with custom config."""
        config = VeyraConfig()
        config.model.backend = "mock"
        config.environment = "mars"

        veyra = VeyraCore(config=config)
        assert veyra.config.environment == "mars"

    def test_execute_sync(self):
        """Test synchronous execution."""
        veyra = VeyraCore()
        result = veyra.execute("Hello Veyra")

        assert result.success
        assert len(result.content) > 0
        assert result.execution_id is not None

    def test_execute_with_dict(self):
        """Test execution with dict input."""
        veyra = VeyraCore()
        result = veyra.execute({"prompt": "Analyze this sensor data"})

        assert result.success
        assert len(result.content) > 0

    def test_execute_empty_prompt(self):
        """Test execution with empty prompt."""
        veyra = VeyraCore()
        result = veyra.execute("")

        assert not result.success
        assert "No prompt" in result.error

    @pytest.mark.asyncio
    async def test_execute_async(self):
        """Test asynchronous execution."""
        veyra = VeyraCore()
        result = await veyra.execute_async("Hello Veyra async")

        assert result.success
        assert len(result.content) > 0

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test health check."""
        veyra = VeyraCore()
        health = await veyra.health_check()

        assert health["status"] == "healthy"
        assert health["backend"]["healthy"]

    def test_audit_log(self):
        """Test audit log recording."""
        config = VeyraConfig()
        config.governance.audit_enabled = True
        veyra = VeyraCore(config=config)

        veyra.execute("Test prompt 1")
        veyra.execute("Test prompt 2")

        audit = veyra.get_audit_log()
        assert len(audit) == 2

    def test_result_to_dict(self):
        """Test result serialization."""
        veyra = VeyraCore()
        result = veyra.execute("Test")

        result_dict = result.to_dict()
        assert "content" in result_dict
        assert "success" in result_dict
        assert "execution_id" in result_dict
        assert "timestamp" in result_dict


class TestVeyraConfig:
    """Test VeyraConfig functionality."""

    def test_default_config(self):
        """Test default configuration values."""
        config = VeyraConfig()

        assert config.model.backend == "mock"
        assert config.model.temperature == 0.7
        assert config.environment == "earth"

    def test_from_dict(self):
        """Test creating config from dictionary."""
        data = {
            "system": {"name": "TestVeyra"},
            "environment": "mars",
        }
        config = VeyraConfig.from_dict(data)

        assert config.system_name == "TestVeyra"
        assert config.environment == "mars"

    def test_model_config(self):
        """Test model configuration."""
        config = VeyraConfig()
        config.model.backend = "openai"
        config.model.openai_model = "gpt-4"

        assert config.model.backend == "openai"
        assert config.model.openai_model == "gpt-4"

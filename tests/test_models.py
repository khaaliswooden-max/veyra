"""
Tests for Model Backends
"""

import pytest

from veyra.models import (
    MockBackend,
    ModelResponse,
    get_backend,
    list_backends,
)


class TestMockBackend:
    """Test MockBackend functionality."""

    @pytest.mark.asyncio
    async def test_generate_basic(self):
        """Test basic generation."""
        backend = MockBackend()
        response = await backend.generate("Hello")

        assert isinstance(response, ModelResponse)
        assert len(response.content) > 0
        assert response.backend == "mock"
        assert response.model == "veyra-mock-v1"

    @pytest.mark.asyncio
    async def test_generate_deterministic(self):
        """Test deterministic mode."""
        backend = MockBackend(deterministic=True)

        response1 = await backend.generate("Same prompt")
        response2 = await backend.generate("Same prompt")

        assert response1.content == response2.content

    @pytest.mark.asyncio
    async def test_generate_non_deterministic(self):
        """Test non-deterministic mode."""
        backend = MockBackend(deterministic=False)

        # Run multiple times, should get some variation
        responses = []
        for _ in range(5):
            response = await backend.generate("Test prompt")
            responses.append(response.content)

        # Not guaranteed to be different, but likely
        # Just check they all have content
        assert all(len(r) > 0 for r in responses)

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test health check."""
        backend = MockBackend()
        assert await backend.health_check()

    @pytest.mark.asyncio
    async def test_token_counts(self):
        """Test token count reporting."""
        backend = MockBackend()
        response = await backend.generate("A longer prompt with multiple words")

        assert response.prompt_tokens > 0
        assert response.completion_tokens > 0
        assert (
            response.total_tokens == response.prompt_tokens + response.completion_tokens
        )

    @pytest.mark.asyncio
    async def test_latency_reporting(self):
        """Test latency reporting."""
        backend = MockBackend(latency_range=(0.01, 0.02))
        response = await backend.generate("Quick test")

        assert response.latency_ms >= 10  # At least 10ms

    @pytest.mark.asyncio
    async def test_request_id(self):
        """Test request ID generation."""
        backend = MockBackend()
        response = await backend.generate("Test")

        assert response.request_id is not None
        assert len(response.request_id) > 0


class TestBackendRegistry:
    """Test backend registry functionality."""

    def test_list_backends(self):
        """Test listing available backends."""
        backends = list_backends()

        assert "mock" in backends
        assert "openai" in backends
        assert "anthropic" in backends

    def test_get_mock_backend(self):
        """Test getting mock backend."""
        backend = get_backend("mock")

        assert isinstance(backend, MockBackend)
        assert backend.name == "mock"

    def test_get_unknown_backend(self):
        """Test getting unknown backend raises error."""
        with pytest.raises(ValueError, match="Unknown backend"):
            get_backend("nonexistent")


class TestModelResponse:
    """Test ModelResponse functionality."""

    def test_to_dict(self):
        """Test response serialization."""
        response = ModelResponse(
            content="Test content",
            model="test-model",
            backend="test",
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30,
        )

        data = response.to_dict()

        assert data["content"] == "Test content"
        assert data["model"] == "test-model"
        assert data["backend"] == "test"
        assert data["total_tokens"] == 30

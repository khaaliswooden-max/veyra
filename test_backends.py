"""
Tests for model backends with mocked HTTP.

Tests OpenAI and Anthropic backends without requiring actual API keys.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from veyra.models.base import BaseModelBackend, ModelResponse
from veyra.models.mock import MockBackend
from veyra.models.registry import get_backend, register_backend


class TestMockBackend:
    """Tests for the MockBackend."""
    
    @pytest.mark.asyncio
    async def test_generate_returns_response(self):
        """Test that generate returns a valid ModelResponse."""
        backend = MockBackend()
        response = await backend.generate("Hello, world!")
        
        assert isinstance(response, ModelResponse)
        assert len(response.content) > 0
        assert response.backend == "mock"
        assert response.model == "veyra-mock"
    
    @pytest.mark.asyncio
    async def test_generate_with_system_prompt(self):
        """Test that system prompt is accepted."""
        backend = MockBackend()
        response = await backend.generate(
            "Test prompt",
            system_prompt="You are a helpful assistant.",
        )
        
        assert response.content is not None
    
    @pytest.mark.asyncio
    async def test_generate_with_parameters(self):
        """Test that parameters are accepted."""
        backend = MockBackend()
        response = await backend.generate(
            "Test prompt",
            temperature=0.5,
            max_tokens=100,
        )
        
        assert response.content is not None
    
    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test health check returns True."""
        backend = MockBackend()
        result = await backend.health_check()
        
        assert result is True
    
    def test_backend_name(self):
        """Test backend has correct name."""
        backend = MockBackend()
        assert backend.name == "mock"
    
    def test_repr(self):
        """Test string representation."""
        backend = MockBackend()
        repr_str = repr(backend)
        
        assert "MockBackend" in repr_str
        assert "mock" in repr_str


class TestOpenAIBackend:
    """Tests for the OpenAI backend with mocked HTTP."""
    
    @pytest.fixture
    def mock_openai_response(self):
        """Create a mock OpenAI API response."""
        return {
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "created": 1677652288,
            "model": "gpt-4-turbo-preview",
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "Hello! How can I help you today?",
                },
                "finish_reason": "stop",
            }],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 8,
                "total_tokens": 18,
            },
        }
    
    @pytest.mark.asyncio
    async def test_generate_success(self, mock_openai_response):
        """Test successful generation with mocked API."""
        with patch("veyra.models.openai_backend.AsyncOpenAI") as mock_client_class:
            # Setup mock
            mock_client = MagicMock()
            mock_client.chat.completions.create = AsyncMock(
                return_value=MagicMock(
                    choices=[MagicMock(
                        message=MagicMock(content="Hello! How can I help you?")
                    )],
                    usage=MagicMock(
                        prompt_tokens=10,
                        completion_tokens=8,
                        total_tokens=18,
                    ),
                    model="gpt-4-turbo-preview",
                    id="chatcmpl-123",
                )
            )
            mock_client_class.return_value = mock_client
            
            # Import after patching
            from veyra.models.openai_backend import OpenAIBackend
            
            backend = OpenAIBackend(api_key="test-key", model="gpt-4-turbo-preview")
            response = await backend.generate("Hello!")
            
            assert response.content == "Hello! How can I help you?"
            assert response.backend == "openai"
            assert response.prompt_tokens == 10
            assert response.completion_tokens == 8
    
    @pytest.mark.asyncio
    async def test_generate_with_system_prompt(self, mock_openai_response):
        """Test that system prompt is passed correctly."""
        with patch("veyra.models.openai_backend.AsyncOpenAI") as mock_client_class:
            mock_client = MagicMock()
            mock_create = AsyncMock(
                return_value=MagicMock(
                    choices=[MagicMock(message=MagicMock(content="Response"))],
                    usage=MagicMock(prompt_tokens=10, completion_tokens=5, total_tokens=15),
                    model="gpt-4",
                    id="test",
                )
            )
            mock_client.chat.completions.create = mock_create
            mock_client_class.return_value = mock_client
            
            from veyra.models.openai_backend import OpenAIBackend
            
            backend = OpenAIBackend(api_key="test-key")
            await backend.generate("Test", system_prompt="Be helpful")
            
            # Verify system prompt was passed
            call_args = mock_create.call_args
            messages = call_args.kwargs.get("messages", [])
            assert any(m.get("role") == "system" for m in messages)
    
    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test health check with working API."""
        with patch("veyra.models.openai_backend.AsyncOpenAI") as mock_client_class:
            mock_client = MagicMock()
            mock_client.models.list = AsyncMock(return_value=MagicMock())
            mock_client_class.return_value = mock_client
            
            from veyra.models.openai_backend import OpenAIBackend
            
            backend = OpenAIBackend(api_key="test-key")
            result = await backend.health_check()
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """Test health check with API error."""
        with patch("veyra.models.openai_backend.AsyncOpenAI") as mock_client_class:
            mock_client = MagicMock()
            mock_client.models.list = AsyncMock(side_effect=Exception("API Error"))
            mock_client_class.return_value = mock_client
            
            from veyra.models.openai_backend import OpenAIBackend
            
            backend = OpenAIBackend(api_key="test-key")
            result = await backend.health_check()
            
            assert result is False


class TestAnthropicBackend:
    """Tests for the Anthropic backend with mocked HTTP."""
    
    @pytest.mark.asyncio
    async def test_generate_success(self):
        """Test successful generation with mocked API."""
        with patch("veyra.models.anthropic_backend.AsyncAnthropic") as mock_client_class:
            mock_client = MagicMock()
            mock_client.messages.create = AsyncMock(
                return_value=MagicMock(
                    content=[MagicMock(text="Hello from Claude!")],
                    usage=MagicMock(input_tokens=10, output_tokens=5),
                    model="claude-3-opus-20240229",
                    id="msg-123",
                )
            )
            mock_client_class.return_value = mock_client
            
            from veyra.models.anthropic_backend import AnthropicBackend
            
            backend = AnthropicBackend(api_key="test-key", model="claude-3-opus-20240229")
            response = await backend.generate("Hello!")
            
            assert response.content == "Hello from Claude!"
            assert response.backend == "anthropic"
            assert response.prompt_tokens == 10
            assert response.completion_tokens == 5
    
    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test health check with working API."""
        with patch("veyra.models.anthropic_backend.AsyncAnthropic") as mock_client_class:
            mock_client = MagicMock()
            mock_client.messages.create = AsyncMock(
                return_value=MagicMock(
                    content=[MagicMock(text="OK")],
                    usage=MagicMock(input_tokens=1, output_tokens=1),
                    model="claude-3-opus",
                    id="test",
                )
            )
            mock_client_class.return_value = mock_client
            
            from veyra.models.anthropic_backend import AnthropicBackend
            
            backend = AnthropicBackend(api_key="test-key")
            result = await backend.health_check()
            
            assert result is True


class TestBackendRegistry:
    """Tests for the backend registry."""
    
    def test_get_mock_backend(self):
        """Test getting mock backend."""
        backend = get_backend("mock")
        
        assert isinstance(backend, MockBackend)
        assert backend.name == "mock"
    
    def test_get_unknown_backend_raises(self):
        """Test that unknown backend raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            get_backend("unknown_backend")
        
        assert "unknown_backend" in str(exc_info.value).lower()
    
    def test_register_custom_backend(self):
        """Test registering a custom backend."""
        class CustomBackend(BaseModelBackend):
            name = "custom"
            
            async def generate(self, prompt, **kwargs):
                return ModelResponse(
                    content="Custom response",
                    model="custom-model",
                    backend="custom",
                )
            
            async def health_check(self):
                return True
        
        register_backend("custom", CustomBackend)
        backend = get_backend("custom")
        
        assert backend.name == "custom"


class TestModelResponse:
    """Tests for ModelResponse dataclass."""
    
    def test_to_dict(self):
        """Test serialization to dictionary."""
        response = ModelResponse(
            content="Hello",
            model="test-model",
            backend="test",
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15,
            request_id="req-123",
        )
        
        data = response.to_dict()
        
        assert data["content"] == "Hello"
        assert data["model"] == "test-model"
        assert data["backend"] == "test"
        assert data["prompt_tokens"] == 10
        assert data["completion_tokens"] == 5
        assert data["total_tokens"] == 15
        assert data["request_id"] == "req-123"
        assert "created_at" in data
    
    def test_defaults(self):
        """Test default values."""
        response = ModelResponse(
            content="Test",
            model="test",
            backend="test",
        )
        
        assert response.prompt_tokens == 0
        assert response.completion_tokens == 0
        assert response.total_tokens == 0
        assert response.request_id is None
        assert response.latency_ms == 0.0

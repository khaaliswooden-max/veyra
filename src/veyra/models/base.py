"""
Base Model Backend Interface

Defines the abstract interface that all model backends must implement.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional
from datetime import datetime


@dataclass
class ModelResponse:
    """Standardized response from any model backend."""
    content: str
    model: str
    backend: str
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    latency_ms: float = 0.0
    
    # Token usage
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    
    # Audit trail
    request_id: Optional[str] = None
    trace_id: Optional[str] = None
    
    # Raw response for debugging
    raw_response: Optional[dict[str, Any]] = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "content": self.content,
            "model": self.model,
            "backend": self.backend,
            "created_at": self.created_at.isoformat(),
            "latency_ms": self.latency_ms,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "request_id": self.request_id,
            "trace_id": self.trace_id,
        }


class BaseModelBackend(ABC):
    """Abstract base class for model backends."""
    
    name: str = "base"
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        *,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> ModelResponse:
        """
        Generate a response from the model.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional backend-specific parameters
            
        Returns:
            ModelResponse with the generated content
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the backend is healthy and available.
        
        Returns:
            True if backend is available, False otherwise
        """
        pass
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name}>"


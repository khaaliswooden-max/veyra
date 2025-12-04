"""
Anthropic Model Backend

Adapter for Anthropic's Claude models.
"""

import os
import uuid
from datetime import datetime
from typing import Any, Optional

from veyra.models.base import BaseModelBackend, ModelResponse


class AnthropicBackend(BaseModelBackend):
    """
    Anthropic API backend supporting Claude models.
    
    Requires:
        - anthropic package: pip install veyra[anthropic]
        - ANTHROPIC_API_KEY environment variable
    """
    
    name = "anthropic"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-opus-20240229",
    ):
        """
        Initialize Anthropic backend.
        
        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Model name to use
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model
        self._client: Any = None
    
    def _get_client(self) -> Any:
        """Lazy-load the Anthropic client."""
        if self._client is None:
            try:
                from anthropic import AsyncAnthropic
            except ImportError:
                raise ImportError(
                    "Anthropic package not installed. "
                    "Install with: pip install veyra[anthropic]"
                )
            
            if not self.api_key:
                raise ValueError(
                    "Anthropic API key not found. "
                    "Set ANTHROPIC_API_KEY environment variable or pass api_key parameter."
                )
            
            self._client = AsyncAnthropic(api_key=self.api_key)
        
        return self._client
    
    async def generate(
        self,
        prompt: str,
        *,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> ModelResponse:
        """Generate a response using Anthropic API."""
        client = self._get_client()
        start_time = datetime.utcnow()
        
        # Build request
        request_kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        
        if system_prompt:
            request_kwargs["system"] = system_prompt
        
        # Only add temperature if not default (Anthropic is sensitive to this)
        if temperature != 1.0:
            request_kwargs["temperature"] = temperature
        
        response = await client.messages.create(**request_kwargs)
        
        end_time = datetime.utcnow()
        latency_ms = (end_time - start_time).total_seconds() * 1000
        
        # Extract content from response
        content = ""
        if response.content:
            content = response.content[0].text if response.content else ""
        
        return ModelResponse(
            content=content,
            model=response.model,
            backend=self.name,
            created_at=end_time,
            latency_ms=latency_ms,
            prompt_tokens=response.usage.input_tokens,
            completion_tokens=response.usage.output_tokens,
            total_tokens=response.usage.input_tokens + response.usage.output_tokens,
            request_id=response.id,
            trace_id=str(uuid.uuid4()),
            raw_response=response.model_dump() if hasattr(response, 'model_dump') else None,
        )
    
    async def health_check(self) -> bool:
        """Check if Anthropic API is accessible."""
        try:
            # Try a minimal generation to check connectivity
            client = self._get_client()
            await client.messages.create(
                model=self.model,
                max_tokens=10,
                messages=[{"role": "user", "content": "ping"}],
            )
            return True
        except Exception:
            return False


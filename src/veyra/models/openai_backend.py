"""
OpenAI Model Backend

Adapter for OpenAI's GPT models.
"""

import os
import uuid
from datetime import datetime
from typing import Any, Optional

from veyra.models.base import BaseModelBackend, ModelResponse


class OpenAIBackend(BaseModelBackend):
    """
    OpenAI API backend supporting GPT-4 and other models.
    
    Requires:
        - openai package: pip install veyra[openai]
        - OPENAI_API_KEY environment variable
    """
    
    name = "openai"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4-turbo-preview",
        organization: Optional[str] = None,
    ):
        """
        Initialize OpenAI backend.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Model name to use
            organization: Optional organization ID
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.organization = organization or os.getenv("OPENAI_ORG_ID")
        self._client: Any = None
    
    def _get_client(self) -> Any:
        """Lazy-load the OpenAI client."""
        if self._client is None:
            try:
                from openai import AsyncOpenAI
            except ImportError:
                raise ImportError(
                    "OpenAI package not installed. "
                    "Install with: pip install veyra[openai]"
                )
            
            if not self.api_key:
                raise ValueError(
                    "OpenAI API key not found. "
                    "Set OPENAI_API_KEY environment variable or pass api_key parameter."
                )
            
            self._client = AsyncOpenAI(
                api_key=self.api_key,
                organization=self.organization,
            )
        
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
        """Generate a response using OpenAI API."""
        client = self._get_client()
        start_time = datetime.utcnow()
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = await client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        
        end_time = datetime.utcnow()
        latency_ms = (end_time - start_time).total_seconds() * 1000
        
        choice = response.choices[0]
        usage = response.usage
        
        return ModelResponse(
            content=choice.message.content or "",
            model=response.model,
            backend=self.name,
            created_at=end_time,
            latency_ms=latency_ms,
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
            total_tokens=usage.total_tokens if usage else 0,
            request_id=response.id,
            trace_id=str(uuid.uuid4()),
            raw_response=response.model_dump() if hasattr(response, 'model_dump') else None,
        )
    
    async def health_check(self) -> bool:
        """Check if OpenAI API is accessible."""
        try:
            client = self._get_client()
            # Use a minimal API call to check connectivity
            await client.models.list()
            return True
        except Exception:
            return False


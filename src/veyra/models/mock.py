"""
Mock Model Backend

A deterministic mock backend for testing and development.
No API keys required.
"""

import asyncio
import hashlib
import random
import uuid
from datetime import UTC, datetime
from typing import Any

from veyra.models.base import BaseModelBackend, ModelResponse


class MockBackend(BaseModelBackend):
    """
    Mock backend that generates deterministic responses for testing.

    Useful for:
    - Development without API keys
    - Testing pipeline logic
    - Benchmarking infrastructure
    - Demos and documentation
    """

    name = "mock"

    def __init__(
        self,
        latency_range: tuple[float, float] = (0.1, 0.5),
        deterministic: bool = True,
    ):
        """
        Initialize mock backend.

        Args:
            latency_range: Min/max simulated latency in seconds
            deterministic: If True, same prompt gives same response
        """
        self.latency_range = latency_range
        self.deterministic = deterministic

        # Response templates for different query types
        self._templates = {
            "analyze": "Analysis complete. Based on the provided data, I've identified {count} key patterns. The primary finding is that {finding}. Confidence level: {confidence}%.",
            "recommend": "Recommendation: {action}. This approach is optimal given the constraints. Expected outcome: {outcome}. Risk assessment: {risk}.",
            "plan": "Strategic Plan:\n1. {step1}\n2. {step2}\n3. {step3}\n\nTimeline: {timeline}\nResource requirements: {resources}",
            "default": "Veyra Mock Response:\n\nProcessed input successfully. Key observations:\n- Input length: {input_len} characters\n- Complexity: {complexity}\n- Suggested action: {action}\n\nThis is a mock response for development and testing purposes.",
        }

        self._findings = [
            "temporal correlation between events",
            "anomalous sensor readings in sector 7",
            "resource optimization opportunity",
            "communication latency exceeds threshold",
            "system stability within normal parameters",
        ]

        self._actions = [
            "proceed with caution",
            "increase monitoring frequency",
            "initiate backup protocols",
            "continue current operations",
            "escalate to human oversight",
        ]

    async def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> ModelResponse:
        """Generate a mock response."""
        # Unused parameters (for interface compatibility)
        _ = system_prompt, temperature, max_tokens, kwargs

        start_time = datetime.now(UTC)

        # Simulate network latency
        latency = random.uniform(*self.latency_range)
        await asyncio.sleep(latency)

        # Generate deterministic seed from prompt if needed
        if self.deterministic:
            seed = int(hashlib.md5(prompt.encode()).hexdigest()[:8], 16)
            rng = random.Random(seed)
        else:
            rng = random.Random()

        # Select template based on prompt keywords
        template_key = "default"
        prompt_lower = prompt.lower()
        if any(word in prompt_lower for word in ["analyze", "analysis", "examine"]):
            template_key = "analyze"
        elif any(word in prompt_lower for word in ["recommend", "suggest", "advise"]):
            template_key = "recommend"
        elif any(word in prompt_lower for word in ["plan", "strategy", "schedule"]):
            template_key = "plan"

        # Generate response content
        template = self._templates[template_key]
        content = template.format(
            count=rng.randint(2, 7),
            finding=rng.choice(self._findings),
            confidence=rng.randint(70, 99),
            action=rng.choice(self._actions),
            outcome="positive trajectory with manageable risk",
            risk="low to moderate",
            step1="Establish baseline measurements",
            step2="Implement monitoring protocols",
            step3="Execute optimization sequence",
            timeline=f"{rng.randint(1, 4)} operational cycles",
            resources="standard allocation",
            input_len=len(prompt),
            complexity=rng.choice(["low", "moderate", "high"]),
        )

        # Calculate simulated token counts
        prompt_tokens = len(prompt.split()) * 2  # Rough approximation
        completion_tokens = len(content.split()) * 2

        end_time = datetime.now(UTC)
        latency_ms = (end_time - start_time).total_seconds() * 1000

        return ModelResponse(
            content=content,
            model="veyra-mock",
            backend=self.name,
            created_at=end_time,
            latency_ms=latency_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            request_id=str(uuid.uuid4()),
        )

    async def health_check(self) -> bool:
        """Mock backend is always healthy."""
        return True

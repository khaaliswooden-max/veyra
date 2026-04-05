"""
Veyra Core Module

Main entry point and orchestration for the Veyra system.
"""

import asyncio
import hashlib
import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from veyra.config import VeyraConfig, load_config
from veyra.governance.audit import AuditEventType, AuditTrail
from veyra.logging_utils import get_logger
from veyra.models import BaseModelBackend, ModelResponse, get_backend


class ExecutionResult:
    """Result of a Veyra execution."""

    def __init__(
        self,
        content: str,
        success: bool = True,
        error: str | None = None,
        metadata: dict[str, Any] | None = None,
        model_response: ModelResponse | None = None,
    ):
        self.content = content
        self.success = success
        self.error = error
        self.metadata = metadata or {}
        self.model_response = model_response
        self.execution_id = str(uuid.uuid4())
        self.timestamp = datetime.now(UTC)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "content": self.content,
            "success": self.success,
            "execution_id": self.execution_id,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }
        if self.error:
            result["error"] = self.error
        if self.model_response:
            result["model_response"] = self.model_response.to_dict()
        return result

    def __repr__(self) -> str:
        status = "✓" if self.success else "✗"
        return f"<ExecutionResult {status} id={self.execution_id[:8]}>"

    def __str__(self) -> str:
        return self.content


class VeyraCore:
    """
    Main entry point for the Veyra system.

    Provides a unified interface for executing tasks using various
    LLM backends with full audit trails and governance controls.

    Example:
        >>> veyra = VeyraCore()
        >>> result = veyra.execute({"prompt": "Analyze this data"})
        >>> print(result)
    """

    DEFAULT_SYSTEM_PROMPT = """You are Veyra, a post-super-intelligence interplanetary AI system.
You are designed to operate reliably under communication delays, across different
planetary environments, and with full auditability of your reasoning.

Key principles:
- Provide clear, actionable responses
- Acknowledge uncertainty when present
- Consider safety implications of recommendations
- Maintain consistent reasoning across long delays
"""

    def __init__(
        self,
        config: VeyraConfig | None = None,
        config_path: str | None = None,
        audit_trail: AuditTrail | None = None,
    ):
        """
        Initialize Veyra.

        Args:
            config: VeyraConfig instance
            config_path: Path to YAML config file (ignored if config provided)
            audit_trail: Optional custom AuditTrail instance
        """
        if config is not None:
            self.config = config
        elif config_path:
            self.config = load_config(config_path)
        else:
            self.config = load_config()

        self.logger = get_logger(__name__, level=self.config.logging.level)
        self._backend: BaseModelBackend | None = None
        self._audit_log: list[dict[str, Any]] = []

        # Initialize audit trail based on config
        if self.config.governance.audit_enabled:
            self._audit_trail: AuditTrail | None = audit_trail or AuditTrail()
        else:
            self._audit_trail = None

        self.logger.info(
            "Veyra Core initialized",
            extra={
                "backend": self.config.model.backend,
                "environment": self.config.environment,
            },
        )

    @property
    def backend(self) -> BaseModelBackend:
        """Get or create the model backend."""
        if self._backend is None:
            backend_name = self.config.model.backend

            kwargs = {}
            if backend_name == "openai":
                kwargs["model"] = self.config.model.openai_model
            elif backend_name == "anthropic":
                kwargs["model"] = self.config.model.anthropic_model

            self._backend = get_backend(backend_name, **kwargs)
            self.logger.debug(f"Created backend: {self._backend}")

        return self._backend

    @property
    def audit_trail(self) -> AuditTrail | None:
        """Get the audit trail instance (None if audit disabled)."""
        return self._audit_trail

    def get_audit_trail(self) -> AuditTrail | None:
        """Get the audit trail instance."""
        return self._audit_trail

    def verify_audit_integrity(self) -> tuple[bool, str | None]:
        """
        Verify the integrity of the audit trail.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if self._audit_trail is None:
            return True, None
        return self._audit_trail.verify_integrity()

    @staticmethod
    def _hash_input(input_data: str) -> str:
        """Create a hash summary of input data for audit purposes."""
        input_hash = hashlib.sha256(input_data.encode()).hexdigest()[:16]
        return f"hash:{input_hash}:len:{len(input_data)}"

    def execute(
        self,
        task: dict[str, Any] | str,
        *,
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> ExecutionResult:
        """
        Execute a task synchronously.

        Args:
            task: Task specification (dict with 'prompt' key or string)
            system_prompt: Override system prompt
            **kwargs: Additional parameters passed to model

        Returns:
            ExecutionResult with the response
        """
        return asyncio.run(
            self.execute_async(task, system_prompt=system_prompt, **kwargs)
        )

    async def execute_async(
        self,
        task: dict[str, Any] | str,
        *,
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> ExecutionResult:
        """
        Execute a task asynchronously.

        Args:
            task: Task specification (dict with 'prompt' key or string)
            system_prompt: Override system prompt
            **kwargs: Additional parameters passed to model

        Returns:
            ExecutionResult with the response
        """
        # Normalize task input
        if isinstance(task, str):
            prompt = task
            task_metadata = {}
        else:
            prompt = task.get("prompt", "")
            task_metadata = {k: v for k, v in task.items() if k != "prompt"}

        if not prompt:
            return ExecutionResult(
                content="",
                success=False,
                error="No prompt provided",
            )

        execution_id = str(uuid.uuid4())
        start_time = datetime.now(UTC)

        self.logger.info(
            "Executing task",
            extra={"execution_id": execution_id, "prompt_length": len(prompt)},
        )

        # Simulate interplanetary latency if enabled
        if self.config.latency.simulate_latency:
            import random

            delay = random.uniform(
                self.config.latency.min_delay_seconds,
                self.config.latency.max_delay_seconds,
            )
            self.logger.debug(f"Simulating {delay:.1f}s interplanetary delay")
            await asyncio.sleep(delay)

        try:
            # Generate response
            response = await self.backend.generate(
                prompt,
                system_prompt=system_prompt or self.DEFAULT_SYSTEM_PROMPT,
                temperature=self.config.model.temperature,
                max_tokens=self.config.model.max_tokens,
                **kwargs,
            )

            result = ExecutionResult(
                content=response.content,
                success=True,
                metadata={
                    "execution_id": execution_id,
                    "backend": self.config.model.backend,
                    "environment": self.config.environment,
                    **task_metadata,
                },
                model_response=response,
            )

        except Exception as e:
            self.logger.error(f"Execution failed: {e}", exc_info=True)
            result = ExecutionResult(
                content="",
                success=False,
                error=str(e),
                metadata={"execution_id": execution_id},
            )

        # Record audit trail
        end_time = datetime.now(UTC)
        audit_entry = {
            "execution_id": execution_id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_ms": (end_time - start_time).total_seconds() * 1000,
            "success": result.success,
            "prompt_length": len(prompt),
            "response_length": len(result.content),
            "backend": self.config.model.backend,
        }

        if self.config.governance.audit_enabled:
            self._audit_log.append(audit_entry)

            # Also record in the new audit trail system
            if self._audit_trail is not None:
                self._audit_trail.record(
                    event_type=AuditEventType.EXECUTION,
                    action="execute",
                    resource="veyra-core",
                    outcome="success" if result.success else "failure",
                    input_summary=self._hash_input(prompt),
                    output_summary=f"len:{len(result.content)}",
                    metadata={
                        "execution_id": execution_id,
                        "backend": self.config.model.backend,
                        "duration_ms": audit_entry["duration_ms"],
                    },
                )

        self.logger.info(
            "Execution complete",
            extra=audit_entry,
        )

        return result

    async def health_check(self) -> dict[str, Any]:
        """
        Check system health.

        Returns:
            Health status dictionary
        """
        backend_healthy = await self.backend.health_check()

        result: dict[str, Any] = {
            "status": "healthy" if backend_healthy else "degraded",
            "backend": {
                "name": self.backend.name,
                "healthy": backend_healthy,
            },
            "config": {
                "environment": self.config.environment,
                "latency_simulation": self.config.latency.simulate_latency,
                "audit_enabled": self.config.governance.audit_enabled,
            },
            "timestamp": datetime.now(UTC).isoformat(),
        }

        # Add audit information if enabled
        if self.config.governance.audit_enabled and self._audit_trail is not None:
            is_valid, _ = self._audit_trail.verify_integrity()
            result["audit"] = {
                "enabled": True,
                "integrity_valid": is_valid,
                "entry_count": len(self._audit_trail),
            }

        return result

    def get_audit_log(self) -> list[dict[str, Any]]:
        """Get the audit log of all executions."""
        return self._audit_log.copy()

    def export_audit_log(self, path: str | Path) -> None:
        """Export audit log to a JSON file."""
        path = Path(path)
        with open(path, "w") as f:
            json.dump(self._audit_log, f, indent=2)
        self.logger.info(f"Exported audit log to {path}")

    def run(self) -> None:
        """
        Execute the Veyra system (legacy interface).
        """
        print("Veyra Core Initialized")
        print(f"  Backend: {self.config.model.backend}")
        print(f"  Environment: {self.config.environment}")
        print(f"  Version: {self.config.version}")

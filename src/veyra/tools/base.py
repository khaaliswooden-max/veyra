"""
Base Tool Infrastructure

Defines the interface for tools that can be invoked by Veyra.
"""

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional


class ToolCategory(Enum):
    """Categories of tools."""

    ANALYSIS = "analysis"
    COMMUNICATION = "communication"
    COMPUTATION = "computation"
    DATA = "data"
    SYSTEM = "system"
    EXTERNAL = "external"


@dataclass
class ToolCapability:
    """Declares a tool's capabilities and constraints."""

    name: str
    description: str
    category: ToolCategory

    # Safety properties
    reversible: bool = True
    requires_confirmation: bool = False
    max_execution_time: float = 60.0

    # Input/output schemas
    input_schema: Optional[dict[str, Any]] = None
    output_schema: Optional[dict[str, Any]] = None


@dataclass
class ToolResult:
    """Result of a tool invocation."""

    success: bool
    output: Any
    error: Optional[str] = None

    tool_name: str = ""
    invocation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    execution_time_ms: float = 0.0

    # Audit trail
    input_hash: Optional[str] = None
    output_hash: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "tool_name": self.tool_name,
            "invocation_id": self.invocation_id,
            "timestamp": self.timestamp.isoformat(),
            "execution_time_ms": self.execution_time_ms,
        }


class Tool(ABC):
    """
    Abstract base class for tools.

    Tools are discrete units of functionality that can be invoked
    by Veyra with full audit trails and safety checks.
    """

    @property
    @abstractmethod
    def capability(self) -> ToolCapability:
        """Get tool capability declaration."""
        pass

    @abstractmethod
    async def invoke(self, **kwargs: Any) -> ToolResult:
        """
        Invoke the tool.

        Args:
            **kwargs: Tool-specific parameters

        Returns:
            ToolResult with output or error
        """
        pass

    async def validate_input(self, **kwargs: Any) -> tuple[bool, Optional[str]]:
        """
        Validate input before execution.

        Returns:
            Tuple of (is_valid, error_message)
        """
        return True, None

    def __repr__(self) -> str:
        return f"<Tool {self.capability.name}>"


class ToolRegistry:
    """
    Registry for managing available tools.

    Provides discovery, validation, and invocation of registered tools.
    """

    def __init__(self):
        self._tools: dict[str, Tool] = {}
        self._invocation_log: list[dict[str, Any]] = []

    def register(self, tool: Tool) -> None:
        """Register a tool."""
        self._tools[tool.capability.name] = tool

    def unregister(self, name: str) -> bool:
        """Unregister a tool."""
        if name in self._tools:
            del self._tools[name]
            return True
        return False

    def get(self, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> list[ToolCapability]:
        """List all registered tool capabilities."""
        return [t.capability for t in self._tools.values()]

    def list_by_category(self, category: ToolCategory) -> list[ToolCapability]:
        """List tools by category."""
        return [
            t.capability
            for t in self._tools.values()
            if t.capability.category == category
        ]

    async def invoke(
        self,
        tool_name: str,
        **kwargs: Any,
    ) -> ToolResult:
        """
        Invoke a tool by name.

        Args:
            tool_name: Name of tool to invoke
            **kwargs: Tool parameters

        Returns:
            ToolResult
        """
        tool = self._tools.get(tool_name)
        if not tool:
            return ToolResult(
                success=False,
                output=None,
                error=f"Tool not found: {tool_name}",
                tool_name=tool_name,
            )

        # Validate input
        is_valid, error = await tool.validate_input(**kwargs)
        if not is_valid:
            return ToolResult(
                success=False,
                output=None,
                error=f"Invalid input: {error}",
                tool_name=tool_name,
            )

        # Execute
        start_time = datetime.utcnow()
        result = await tool.invoke(**kwargs)
        end_time = datetime.utcnow()

        result.tool_name = tool_name
        result.execution_time_ms = (end_time - start_time).total_seconds() * 1000

        # Log invocation
        self._invocation_log.append(
            {
                "tool_name": tool_name,
                "invocation_id": result.invocation_id,
                "timestamp": result.timestamp.isoformat(),
                "success": result.success,
                "execution_time_ms": result.execution_time_ms,
            }
        )

        return result

    def get_invocation_log(self) -> list[dict[str, Any]]:
        """Get the invocation audit log."""
        return self._invocation_log.copy()

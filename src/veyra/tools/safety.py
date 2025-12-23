"""
Tool Safety Boundaries

Implements safety checks and constraints for tool execution.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class SafetyLevel(Enum):
    """Safety levels for operations."""

    SAFE = "safe"  # No restrictions
    CAUTION = "caution"  # Requires logging
    RESTRICTED = "restricted"  # Requires confirmation
    PROHIBITED = "prohibited"  # Not allowed


@dataclass
class SafetyViolation:
    """Records a safety boundary violation."""

    level: SafetyLevel
    rule: str
    description: str
    context: dict[str, Any] | None = None


class SafetyBoundary:
    """
    Enforces safety boundaries for tool operations.

    Implements hard limits and soft warnings based on
    configured safety rules.
    """

    def __init__(
        self,
        reversible_only: bool = False,
        require_confirmation: bool = False,
        prohibited_operations: set[str] | None = None,
    ):
        """
        Initialize safety boundary.

        Args:
            reversible_only: Only allow reversible operations
            require_confirmation: Require confirmation for all operations
            prohibited_operations: Set of prohibited operation names
        """
        self.reversible_only = reversible_only
        self.require_confirmation = require_confirmation
        self.prohibited_operations = prohibited_operations or set()

        self._violations: list[SafetyViolation] = []

    def check_operation(
        self,
        operation_name: str,
        is_reversible: bool = True,
        context: dict[str, Any] | None = None,
    ) -> tuple[SafetyLevel, SafetyViolation | None]:
        """
        Check if an operation is allowed.

        Args:
            operation_name: Name of the operation
            is_reversible: Whether the operation is reversible
            context: Additional context for the check

        Returns:
            Tuple of (safety_level, violation if any)
        """
        # Check prohibited operations
        if operation_name in self.prohibited_operations:
            violation = SafetyViolation(
                level=SafetyLevel.PROHIBITED,
                rule="prohibited_operation",
                description=f"Operation '{operation_name}' is prohibited",
                context=context,
            )
            self._violations.append(violation)
            return SafetyLevel.PROHIBITED, violation

        # Check reversibility
        if self.reversible_only and not is_reversible:
            violation = SafetyViolation(
                level=SafetyLevel.PROHIBITED,
                rule="reversible_only",
                description=f"Operation '{operation_name}' is not reversible",
                context=context,
            )
            self._violations.append(violation)
            return SafetyLevel.PROHIBITED, violation

        # Check confirmation requirement
        if self.require_confirmation:
            return SafetyLevel.RESTRICTED, None

        return SafetyLevel.SAFE, None

    def get_violations(self) -> list[SafetyViolation]:
        """Get all recorded violations."""
        return self._violations.copy()

    def clear_violations(self) -> None:
        """Clear recorded violations."""
        self._violations.clear()

    def add_prohibited_operation(self, operation_name: str) -> None:
        """Add an operation to the prohibited list."""
        self.prohibited_operations.add(operation_name)

    def remove_prohibited_operation(self, operation_name: str) -> None:
        """Remove an operation from the prohibited list."""
        self.prohibited_operations.discard(operation_name)

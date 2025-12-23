"""
Policy Engine

Implements multi-stakeholder policy framework for governance decisions.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional


class PolicyDecision(Enum):
    """Policy decision outcomes."""

    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"
    AUDIT = "audit"  # Allow but audit


@dataclass
class PolicyResult:
    """Result of a policy evaluation."""

    decision: PolicyDecision
    policy_name: str
    reason: str
    conditions: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Policy:
    """
    A governance policy.

    Policies define rules that are evaluated for actions,
    supporting multi-stakeholder governance.
    """

    name: str
    description: str

    # Policy function: takes context, returns PolicyDecision
    evaluate: Callable[[dict[str, Any]], PolicyDecision]

    # Policy metadata
    priority: int = 0  # Higher priority evaluated first
    jurisdiction: str = "global"  # Which jurisdiction this applies to
    enabled: bool = True

    # Conditions
    applies_to: list[str] = field(default_factory=list)  # Action types

    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


class PolicyEngine:
    """
    Evaluates policies for governance decisions.

    Supports:
    - Multiple policies with priority ordering
    - Jurisdiction-specific policies
    - Multi-stakeholder policy composition
    """

    def __init__(self, default_decision: PolicyDecision = PolicyDecision.ALLOW):
        """
        Initialize policy engine.

        Args:
            default_decision: Decision when no policies match
        """
        self._policies: list[Policy] = []
        self.default_decision = default_decision

    def add_policy(self, policy: Policy) -> None:
        """Add a policy to the engine."""
        self._policies.append(policy)
        # Sort by priority (descending)
        self._policies.sort(key=lambda p: p.priority, reverse=True)

    def remove_policy(self, name: str) -> bool:
        """Remove a policy by name."""
        original_len = len(self._policies)
        self._policies = [p for p in self._policies if p.name != name]
        return len(self._policies) < original_len

    def evaluate(
        self,
        action: str,
        context: dict[str, Any],
        jurisdiction: str = "global",
    ) -> PolicyResult:
        """
        Evaluate policies for an action.

        Args:
            action: The action being performed
            context: Context for policy evaluation
            jurisdiction: Jurisdiction for policy selection

        Returns:
            PolicyResult with decision and reasoning
        """
        # Find applicable policies
        applicable = [
            p
            for p in self._policies
            if p.enabled
            and (not p.applies_to or action in p.applies_to)
            and (p.jurisdiction in ("global", jurisdiction))
        ]

        if not applicable:
            return PolicyResult(
                decision=self.default_decision,
                policy_name="default",
                reason="No applicable policies found",
            )

        # Evaluate policies in priority order
        deny_reasons: list[str] = []
        audit_policies: list[str] = []

        for policy in applicable:
            try:
                decision = policy.evaluate(context)

                if decision == PolicyDecision.DENY:
                    return PolicyResult(
                        decision=PolicyDecision.DENY,
                        policy_name=policy.name,
                        reason=f"Denied by policy: {policy.description}",
                    )
                elif decision == PolicyDecision.REQUIRE_APPROVAL:
                    return PolicyResult(
                        decision=PolicyDecision.REQUIRE_APPROVAL,
                        policy_name=policy.name,
                        reason=f"Requires approval: {policy.description}",
                    )
                elif decision == PolicyDecision.AUDIT:
                    audit_policies.append(policy.name)

            except Exception as e:
                # Policy evaluation errors default to deny for safety
                return PolicyResult(
                    decision=PolicyDecision.DENY,
                    policy_name=policy.name,
                    reason=f"Policy evaluation error: {str(e)}",
                )

        # If we get here, action is allowed
        decision = PolicyDecision.AUDIT if audit_policies else PolicyDecision.ALLOW

        return PolicyResult(
            decision=decision,
            policy_name=applicable[0].name if applicable else "default",
            reason="Action permitted by all applicable policies",
            conditions=audit_policies,
        )

    def list_policies(
        self,
        jurisdiction: Optional[str] = None,
        enabled_only: bool = True,
    ) -> list[Policy]:
        """List registered policies."""
        policies = self._policies

        if jurisdiction:
            policies = [
                p for p in policies if p.jurisdiction in ("global", jurisdiction)
            ]

        if enabled_only:
            policies = [p for p in policies if p.enabled]

        return policies


# Pre-built common policies


def create_rate_limit_policy(
    name: str,
    max_requests: int,
    window_seconds: int,
) -> Policy:
    """Create a rate limiting policy."""
    request_times: list[datetime] = []

    def evaluate(context: dict[str, Any]) -> PolicyDecision:
        now = datetime.utcnow()
        # Clean old requests
        cutoff = now.timestamp() - window_seconds
        request_times[:] = [t for t in request_times if t.timestamp() > cutoff]

        if len(request_times) >= max_requests:
            return PolicyDecision.DENY

        request_times.append(now)
        return PolicyDecision.ALLOW

    return Policy(
        name=name,
        description=f"Rate limit: {max_requests} requests per {window_seconds}s",
        evaluate=evaluate,
        priority=100,
    )


def create_content_filter_policy(
    name: str,
    blocked_patterns: list[str],
) -> Policy:
    """Create a content filtering policy."""
    import re

    patterns = [re.compile(p, re.IGNORECASE) for p in blocked_patterns]

    def evaluate(context: dict[str, Any]) -> PolicyDecision:
        content = str(context.get("content", ""))
        for pattern in patterns:
            if pattern.search(content):
                return PolicyDecision.DENY
        return PolicyDecision.ALLOW

    return Policy(
        name=name,
        description="Content filter policy",
        evaluate=evaluate,
        priority=90,
    )

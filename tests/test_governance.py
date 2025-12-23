"""
Tests for Governance Layer
"""

from datetime import UTC, datetime

from veyra.governance import (
    AuditEntry,
    AuditTrail,
    Policy,
    PolicyDecision,
    PolicyEngine,
)
from veyra.governance.audit import AuditEventType


class TestAuditTrail:
    """Test AuditTrail functionality."""

    def test_record_event(self):
        """Test recording an audit event."""
        trail = AuditTrail()
        entry = trail.record(
            event_type=AuditEventType.EXECUTION,
            action="execute",
            resource="test_task",
        )

        assert entry.event_type == AuditEventType.EXECUTION
        assert entry.action == "execute"
        assert entry.entry_hash is not None

    def test_hash_chain(self):
        """Test hash chain integrity."""
        trail = AuditTrail()

        trail.record(AuditEventType.EXECUTION, "action1")
        trail.record(AuditEventType.EXECUTION, "action2")
        trail.record(AuditEventType.EXECUTION, "action3")

        is_valid, error = trail.verify_integrity()
        assert is_valid
        assert error is None

    def test_get_entries(self):
        """Test querying entries."""
        trail = AuditTrail()

        trail.record(AuditEventType.EXECUTION, "exec1")
        trail.record(AuditEventType.TOOL_INVOCATION, "tool1")
        trail.record(AuditEventType.EXECUTION, "exec2")

        exec_entries = trail.get_entries(event_type=AuditEventType.EXECUTION)
        assert len(exec_entries) == 2

    def test_entry_to_dict(self):
        """Test entry serialization."""
        entry = AuditEntry(
            event_type=AuditEventType.EXECUTION,
            timestamp=datetime.now(UTC),
            action="test",
            resource="resource",
        )

        data = entry.to_dict()
        assert "event_type" in data
        assert "timestamp" in data
        assert data["action"] == "test"


class TestPolicyEngine:
    """Test PolicyEngine functionality."""

    def test_no_policies(self):
        """Test evaluation with no policies."""
        engine = PolicyEngine()
        result = engine.evaluate("test_action", {})

        assert result.decision == PolicyDecision.ALLOW

    def test_deny_policy(self):
        """Test deny policy."""
        engine = PolicyEngine()

        policy = Policy(
            name="deny_all",
            description="Deny all actions",
            evaluate=lambda _ctx: PolicyDecision.DENY,
        )
        engine.add_policy(policy)

        result = engine.evaluate("test", {})
        assert result.decision == PolicyDecision.DENY

    def test_allow_policy(self):
        """Test allow policy."""
        engine = PolicyEngine()

        policy = Policy(
            name="allow_all",
            description="Allow all actions",
            evaluate=lambda _ctx: PolicyDecision.ALLOW,
        )
        engine.add_policy(policy)

        result = engine.evaluate("test", {})
        assert result.decision == PolicyDecision.ALLOW

    def test_policy_priority(self):
        """Test policy priority ordering."""
        engine = PolicyEngine()

        # Lower priority allow
        allow_policy = Policy(
            name="allow",
            description="Allow",
            evaluate=lambda _ctx: PolicyDecision.ALLOW,
            priority=1,
        )

        # Higher priority deny
        deny_policy = Policy(
            name="deny",
            description="Deny",
            evaluate=lambda _ctx: PolicyDecision.DENY,
            priority=10,
        )

        engine.add_policy(allow_policy)
        engine.add_policy(deny_policy)

        result = engine.evaluate("test", {})
        assert result.decision == PolicyDecision.DENY

    def test_list_policies(self):
        """Test listing policies."""
        engine = PolicyEngine()

        policy = Policy(
            name="test",
            description="Test policy",
            evaluate=lambda _ctx: PolicyDecision.ALLOW,
        )
        engine.add_policy(policy)

        policies = engine.list_policies()
        assert len(policies) == 1
        assert policies[0].name == "test"

    def test_remove_policy(self):
        """Test removing a policy."""
        engine = PolicyEngine()

        policy = Policy(
            name="removable",
            description="To be removed",
            evaluate=lambda _ctx: PolicyDecision.DENY,
        )
        engine.add_policy(policy)

        # Policy should exist
        assert len(engine.list_policies()) == 1

        # Remove it
        removed = engine.remove_policy("removable")
        assert removed is True
        assert len(engine.list_policies()) == 0

    def test_remove_nonexistent_policy(self):
        """Test removing a policy that doesn't exist."""
        engine = PolicyEngine()
        removed = engine.remove_policy("nonexistent")
        assert removed is False

    def test_require_approval_policy(self):
        """Test require_approval policy decision."""
        engine = PolicyEngine()

        policy = Policy(
            name="needs_approval",
            description="Requires human approval",
            evaluate=lambda _ctx: PolicyDecision.REQUIRE_APPROVAL,
        )
        engine.add_policy(policy)

        result = engine.evaluate("sensitive_action", {})
        assert result.decision == PolicyDecision.REQUIRE_APPROVAL
        assert "Requires approval" in result.reason

    def test_audit_policy(self):
        """Test audit policy decision."""
        engine = PolicyEngine()

        policy = Policy(
            name="audit_only",
            description="Audit this action",
            evaluate=lambda _ctx: PolicyDecision.AUDIT,
        )
        engine.add_policy(policy)

        result = engine.evaluate("tracked_action", {})
        assert result.decision == PolicyDecision.AUDIT
        assert "audit_only" in result.conditions

    def test_multiple_audit_policies(self):
        """Test multiple audit policies accumulate."""
        engine = PolicyEngine()

        policy1 = Policy(
            name="audit1",
            description="First audit",
            evaluate=lambda _ctx: PolicyDecision.AUDIT,
            priority=10,
        )
        policy2 = Policy(
            name="audit2",
            description="Second audit",
            evaluate=lambda _ctx: PolicyDecision.AUDIT,
            priority=5,
        )

        engine.add_policy(policy1)
        engine.add_policy(policy2)

        result = engine.evaluate("test", {})
        assert result.decision == PolicyDecision.AUDIT
        assert "audit1" in result.conditions
        assert "audit2" in result.conditions

    def test_policy_error_defaults_to_deny(self):
        """Test that policy evaluation errors default to deny."""
        engine = PolicyEngine()

        def failing_evaluate(_ctx):
            raise RuntimeError("Policy evaluation failed")

        policy = Policy(
            name="broken",
            description="Broken policy",
            evaluate=failing_evaluate,
        )
        engine.add_policy(policy)

        result = engine.evaluate("test", {})
        assert result.decision == PolicyDecision.DENY
        assert "evaluation error" in result.reason

    def test_policy_applies_to_filter(self):
        """Test policy applies_to filtering."""
        engine = PolicyEngine()

        policy = Policy(
            name="specific",
            description="Only applies to specific action",
            evaluate=lambda _ctx: PolicyDecision.DENY,
            applies_to=["restricted_action"],
        )
        engine.add_policy(policy)

        # Should not apply to other actions
        result = engine.evaluate("other_action", {})
        assert result.decision == PolicyDecision.ALLOW

        # Should apply to restricted action
        result = engine.evaluate("restricted_action", {})
        assert result.decision == PolicyDecision.DENY

    def test_policy_jurisdiction_filter(self):
        """Test policy jurisdiction filtering."""
        engine = PolicyEngine()

        policy = Policy(
            name="mars_only",
            description="Mars-specific policy",
            evaluate=lambda _ctx: PolicyDecision.DENY,
            jurisdiction="mars",
        )
        engine.add_policy(policy)

        # Should not apply to Earth
        result = engine.evaluate("action", {}, jurisdiction="earth")
        assert result.decision == PolicyDecision.ALLOW

        # Should apply to Mars
        result = engine.evaluate("action", {}, jurisdiction="mars")
        assert result.decision == PolicyDecision.DENY

    def test_global_jurisdiction_applies_everywhere(self):
        """Test global jurisdiction applies to all locations."""
        engine = PolicyEngine()

        policy = Policy(
            name="global_rule",
            description="Global policy",
            evaluate=lambda _ctx: PolicyDecision.AUDIT,
            jurisdiction="global",
        )
        engine.add_policy(policy)

        # Should apply everywhere
        result = engine.evaluate("action", {}, jurisdiction="earth")
        assert result.decision == PolicyDecision.AUDIT

        result = engine.evaluate("action", {}, jurisdiction="mars")
        assert result.decision == PolicyDecision.AUDIT

    def test_disabled_policy_not_evaluated(self):
        """Test disabled policies are skipped."""
        engine = PolicyEngine()

        policy = Policy(
            name="disabled",
            description="Disabled policy",
            evaluate=lambda _ctx: PolicyDecision.DENY,
            enabled=False,
        )
        engine.add_policy(policy)

        # Disabled policy should not affect result
        result = engine.evaluate("action", {})
        assert result.decision == PolicyDecision.ALLOW

    def test_list_policies_by_jurisdiction(self):
        """Test listing policies filtered by jurisdiction."""
        engine = PolicyEngine()

        global_policy = Policy(
            name="global",
            description="Global",
            evaluate=lambda _ctx: PolicyDecision.ALLOW,
            jurisdiction="global",
        )
        mars_policy = Policy(
            name="mars",
            description="Mars",
            evaluate=lambda _ctx: PolicyDecision.ALLOW,
            jurisdiction="mars",
        )

        engine.add_policy(global_policy)
        engine.add_policy(mars_policy)

        # Mars should see both global and mars
        mars_policies = engine.list_policies(jurisdiction="mars")
        assert len(mars_policies) == 2

        # Earth should only see global
        earth_policies = engine.list_policies(jurisdiction="earth")
        assert len(earth_policies) == 1
        assert earth_policies[0].name == "global"

    def test_list_policies_enabled_only_false(self):
        """Test listing all policies including disabled."""
        engine = PolicyEngine()

        enabled_policy = Policy(
            name="enabled",
            description="Enabled",
            evaluate=lambda _ctx: PolicyDecision.ALLOW,
            enabled=True,
        )
        disabled_policy = Policy(
            name="disabled",
            description="Disabled",
            evaluate=lambda _ctx: PolicyDecision.ALLOW,
            enabled=False,
        )

        engine.add_policy(enabled_policy)
        engine.add_policy(disabled_policy)

        # Default should only show enabled
        enabled_list = engine.list_policies()
        assert len(enabled_list) == 1

        # With enabled_only=False should show all
        all_policies = engine.list_policies(enabled_only=False)
        assert len(all_policies) == 2

    def test_default_decision_deny(self):
        """Test custom default decision."""
        engine = PolicyEngine(default_decision=PolicyDecision.DENY)

        # No policies, should use default
        result = engine.evaluate("action", {})
        assert result.decision == PolicyDecision.DENY


class TestPrebuiltPolicies:
    """Test pre-built policy factories."""

    def test_create_rate_limit_policy(self):
        """Test rate limiting policy."""
        from veyra.governance.policy import create_rate_limit_policy

        policy = create_rate_limit_policy(
            name="rate_limit",
            max_requests=3,
            window_seconds=10,
        )

        engine = PolicyEngine()
        engine.add_policy(policy)

        # First 3 requests should pass
        for _ in range(3):
            result = engine.evaluate("action", {})
            assert result.decision == PolicyDecision.ALLOW

        # 4th request should be denied
        result = engine.evaluate("action", {})
        assert result.decision == PolicyDecision.DENY

    def test_create_content_filter_policy(self):
        """Test content filtering policy."""
        from veyra.governance.policy import create_content_filter_policy

        policy = create_content_filter_policy(
            name="content_filter",
            blocked_patterns=["dangerous", r"secret\d+"],
        )

        engine = PolicyEngine()
        engine.add_policy(policy)

        # Safe content should pass
        result = engine.evaluate("action", {"content": "safe content"})
        assert result.decision == PolicyDecision.ALLOW

        # Blocked content should be denied
        result = engine.evaluate("action", {"content": "this is dangerous"})
        assert result.decision == PolicyDecision.DENY

        # Regex pattern should match
        result = engine.evaluate("action", {"content": "secret123"})
        assert result.decision == PolicyDecision.DENY
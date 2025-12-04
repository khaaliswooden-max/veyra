"""
Tests for Governance Layer
"""

import pytest
from datetime import datetime
from veyra.governance import (
    AuditTrail,
    AuditEntry,
    Policy,
    PolicyEngine,
    PolicyDecision,
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
            timestamp=datetime.utcnow(),
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
            evaluate=lambda ctx: PolicyDecision.DENY,
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
            evaluate=lambda ctx: PolicyDecision.ALLOW,
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
            evaluate=lambda ctx: PolicyDecision.ALLOW,
            priority=1,
        )
        
        # Higher priority deny
        deny_policy = Policy(
            name="deny",
            description="Deny",
            evaluate=lambda ctx: PolicyDecision.DENY,
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
            evaluate=lambda ctx: PolicyDecision.ALLOW,
        )
        engine.add_policy(policy)
        
        policies = engine.list_policies()
        assert len(policies) == 1
        assert policies[0].name == "test"


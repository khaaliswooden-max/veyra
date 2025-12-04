"""
Tests for Tools Layer
"""

import pytest
from veyra.tools import (
    Tool,
    ToolResult,
    ToolRegistry,
    SafetyBoundary,
    SafetyLevel,
)
from veyra.tools.base import ToolCapability, ToolCategory


class MockTool(Tool):
    """Mock tool for testing."""
    
    def __init__(self, name: str = "mock_tool"):
        self._capability = ToolCapability(
            name=name,
            description="A mock tool for testing",
            category=ToolCategory.ANALYSIS,
        )
    
    @property
    def capability(self) -> ToolCapability:
        return self._capability
    
    async def invoke(self, **kwargs) -> ToolResult:
        return ToolResult(
            success=True,
            output=f"Mock output: {kwargs}",
        )


class FailingTool(Tool):
    """Tool that always fails."""
    
    @property
    def capability(self) -> ToolCapability:
        return ToolCapability(
            name="failing_tool",
            description="A tool that fails",
            category=ToolCategory.SYSTEM,
        )
    
    async def invoke(self, **kwargs) -> ToolResult:
        return ToolResult(
            success=False,
            output=None,
            error="Always fails",
        )


class TestToolRegistry:
    """Test ToolRegistry functionality."""
    
    def test_register_tool(self):
        """Test tool registration."""
        registry = ToolRegistry()
        tool = MockTool()
        
        registry.register(tool)
        
        assert registry.get("mock_tool") is not None
    
    def test_list_tools(self):
        """Test listing tools."""
        registry = ToolRegistry()
        registry.register(MockTool("tool1"))
        registry.register(MockTool("tool2"))
        
        tools = registry.list_tools()
        assert len(tools) == 2
    
    @pytest.mark.asyncio
    async def test_invoke_tool(self):
        """Test invoking a tool."""
        registry = ToolRegistry()
        registry.register(MockTool())
        
        result = await registry.invoke("mock_tool", param1="value1")
        
        assert result.success
        assert "value1" in result.output
    
    @pytest.mark.asyncio
    async def test_invoke_missing_tool(self):
        """Test invoking a non-existent tool."""
        registry = ToolRegistry()
        
        result = await registry.invoke("nonexistent")
        
        assert not result.success
        assert "not found" in result.error
    
    def test_invocation_log(self):
        """Test invocation logging."""
        registry = ToolRegistry()
        registry.register(MockTool())
        
        import asyncio
        asyncio.get_event_loop().run_until_complete(
            registry.invoke("mock_tool")
        )
        
        log = registry.get_invocation_log()
        assert len(log) == 1
        assert log[0]["tool_name"] == "mock_tool"


class TestSafetyBoundary:
    """Test SafetyBoundary functionality."""
    
    def test_allow_operation(self):
        """Test allowing an operation."""
        boundary = SafetyBoundary()
        
        level, violation = boundary.check_operation("safe_op")
        
        assert level == SafetyLevel.SAFE
        assert violation is None
    
    def test_prohibited_operation(self):
        """Test prohibiting an operation."""
        boundary = SafetyBoundary(
            prohibited_operations={"dangerous_op"}
        )
        
        level, violation = boundary.check_operation("dangerous_op")
        
        assert level == SafetyLevel.PROHIBITED
        assert violation is not None
        assert "prohibited" in violation.description.lower()
    
    def test_reversible_only(self):
        """Test reversible-only mode."""
        boundary = SafetyBoundary(reversible_only=True)
        
        # Non-reversible operation should be blocked
        level, violation = boundary.check_operation(
            "irreversible_op",
            is_reversible=False,
        )
        
        assert level == SafetyLevel.PROHIBITED
        assert violation is not None
    
    def test_require_confirmation(self):
        """Test confirmation requirement."""
        boundary = SafetyBoundary(require_confirmation=True)
        
        level, _ = boundary.check_operation("any_op")
        
        assert level == SafetyLevel.RESTRICTED
    
    def test_add_prohibited(self):
        """Test adding prohibited operations."""
        boundary = SafetyBoundary()
        boundary.add_prohibited_operation("new_dangerous")
        
        level, _ = boundary.check_operation("new_dangerous")
        
        assert level == SafetyLevel.PROHIBITED


class TestToolResult:
    """Test ToolResult functionality."""
    
    def test_success_result(self):
        """Test successful result."""
        result = ToolResult(
            success=True,
            output="Test output",
        )
        
        assert result.success
        assert result.output == "Test output"
        assert result.error is None
    
    def test_failure_result(self):
        """Test failure result."""
        result = ToolResult(
            success=False,
            output=None,
            error="Something went wrong",
        )
        
        assert not result.success
        assert result.error == "Something went wrong"
    
    def test_to_dict(self):
        """Test result serialization."""
        result = ToolResult(
            success=True,
            output="Test",
            tool_name="test_tool",
        )
        
        data = result.to_dict()
        assert data["success"]
        assert data["output"] == "Test"
        assert data["tool_name"] == "test_tool"


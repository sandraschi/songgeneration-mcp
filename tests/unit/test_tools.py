"""Unit tests for songgeneration_mcp tools."""
import pytest
from songgeneration_mcp.mcp_server import app


def test_help_tool_exists():
    """Test that help tool exists."""
    tools = [tool.name for tool in app.list_tools()]
    assert "help" in tools


def test_status_tool_exists():
    """Test that status tool exists."""
    tools = [tool.name for tool in app.list_tools()]
    assert "status" in tools

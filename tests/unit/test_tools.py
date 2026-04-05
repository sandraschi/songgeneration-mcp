"""Unit tests for songgeneration_mcp tools."""

import pytest

from songgeneration_mcp.mcp_server import app


@pytest.mark.asyncio
async def test_help_tool_exists():
    """Test that help tool exists."""
    tools = await app.list_tools()
    names = [tool.name for tool in tools]
    assert "help" in names


@pytest.mark.asyncio
async def test_get_status_tool_exists():
    """Test that get_status tool exists."""
    tools = await app.list_tools()
    names = [tool.name for tool in tools]
    assert "get_status" in names

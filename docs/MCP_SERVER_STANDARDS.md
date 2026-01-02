# MCP Server Standards

## FastMCP 2.13+ Requirements

### Required Components
- FastMCP 2.13.1 or later
- Help tool (`help()`)
- Status tool (`status()`)
- Proper docstrings with Args/Returns/Examples
- No `description=` parameters (docstrings only)

### Tool Documentation
All tools must have comprehensive docstrings:
```python
@app.tool()
async def my_tool(param: str) -> str:
    """Tool description.
    
    Args:
        param: Parameter description
    
    Returns:
        Return value description
    
    Examples:
        >>> await my_tool("example")
        "result"
    """
    pass
```

### SOTA Compliance Checklist
- ✅ FastMCP 2.13.1+
- ✅ Help tool
- ✅ Status tool
- ✅ Proper docstrings
- ✅ CI/CD workflow
- ✅ Test directory
- ✅ Ruff linting
- ✅ DXT packaging (manifest.json)

## Portmanteau Pattern

For servers with >15 tools, use portmanteau pattern:
- Consolidate related operations into single tools
- Use `operation` parameter to route to specific functionality
- Reduces tool count and improves discoverability

See: https://github.com/jlowin/fastmcp

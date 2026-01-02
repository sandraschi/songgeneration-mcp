# MCPB Standards

## MCPB Packaging

MCPB (MCP Bundle) is the standard packaging format for MCP servers.

### manifest.json

Required fields:
- `name`: Server name
- `description`: Server description
- `version`: Version number
- `mcp.command`: Command to run server
- `mcp.args`: Command arguments

### Distribution

1. Build package: `mcpb build`
2. Publish to registry: `mcpb publish`
3. Install: `mcpb install <package-name>`

See: https://modelcontextprotocol.io/packaging

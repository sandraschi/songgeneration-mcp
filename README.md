# SonggenerationMcp

AI-powered song generation server using Tencent AI Lab's LeVo model. Supports lyrics, style control, and stem separation.

## Installation

```bash
pip install -e .
```

## Usage

```bash
python -m songgeneration_mcp.mcp_server
```

## Claude Desktop Configuration

Add to `~/.config/claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "songgeneration-mcp": {
      "command": "python",
      "args": ["-m", "songgeneration_mcp", "mcp_server"],
      "cwd": "/path/to/songgeneration-mcp"
    }
  }
}
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check .

# Format
ruff format .
```

## License

See LICENSE file for details.

## Author

MCP Studio

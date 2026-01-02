# Claude Desktop Integration

## Configuration

Add to `~/.config/claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "server-name": {
      "command": "python",
      "args": ["-m", "package_name", "mcp_server"],
      "cwd": "/path/to/server"
    }
  }
}
```

## Troubleshooting

- Check Python path is correct
- Verify dependencies are installed
- Check logs in Claude Desktop

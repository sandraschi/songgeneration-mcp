# songgeneration_mcp (MCPB Bundle)

SongGeneration v2 (LeVo 2 / SG2) MCP server: local open-weight music LM via SongGeneration-Studio; dual-track output and SG2 tags.

## Usage

Add to \claude_desktop_config.json\:
\\\json
{
  "mcpServers": {
    "songgeneration_mcp": {
      "command": "uv",
      "args": ["run", "--directory", "\D:\Dev\repos", "python", "-m", "songgeneration_mcp"],
      "env": { "PYTHONPATH": "\D:\Dev\repos/src" }
    }
  }
}
\\\

## Tools

- **songgeneration_mcp**: SongGeneration v2 (LeVo 2 / SG2) MCP server: local open-weight music LM via SongGeneration-Studio; dual-track output and SG2 tags.

## Requirements

- Python 3.12+
- uv

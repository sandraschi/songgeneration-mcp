set windows-shell := ["pwsh.exe", "-NoLogo", "-Command"]
import 'scripts/just/fleet.just'

default:
    @just --list

# Install all music generation backends
install-all:
    Set-Location '{{justfile_directory()}}'
    pwsh -NoProfile -File scripts/install-music-deps.ps1 -All

# Install minimal (Studio API only)
install-minimal:
    Set-Location '{{justfile_directory()}}'
    pwsh -NoProfile -File scripts/install-music-deps.ps1 -Minimal

# Serve the API server
serve:
    Set-Location '{{justfile_directory()}}'
    uv run uvicorn songgeneration_mcp.server:app --host 127.0.0.1 --port 10885 --reload

# Serve MCP (stdio)
serve-mcp:
    Set-Location '{{justfile_directory()}}'
    uv run python -m songgeneration_mcp.mcp_server

# Run tests
test:
    Set-Location '{{justfile_directory()}}'
    uv run pytest tests/ -q

# Lint
lint:
    Set-Location '{{justfile_directory()}}'
    uv run ruff check src/
    Set-Location '{{justfile_directory()}}\web_sota'
    npx @biomejs/biome ci .

# Fix
fix:
    Set-Location '{{justfile_directory()}}'
    uv run ruff check src/ --fix --unsafe-fixes
    uv run ruff format src/
    Set-Location '{{justfile_directory()}}\web_sota'
    npx @biomejs/biome check --write .

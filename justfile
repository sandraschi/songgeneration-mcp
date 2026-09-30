set windows-shell := ["powershell.exe", "-NoProfile", "-Command"]
import 'scripts/just/fleet.just'

default:
    @just --list

# NOTE (assfix 2026-10-01): just runs each recipe LINE in its own shell, so a
# bare `Set-Location` line is lost before the next line runs. Every recipe
# below keeps dir-change and command on ONE line separated by `;`.

# Install all music generation backends
install-all:
    Set-Location '{{justfile_directory()}}'; powershell.exe -NoProfile -File scripts/install-music-deps.ps1 -All

# Install minimal (Studio API only)
install-minimal:
    Set-Location '{{justfile_directory()}}'; powershell.exe -NoProfile -File scripts/install-music-deps.ps1 -Minimal

# Serve the API server
serve:
    Set-Location '{{justfile_directory()}}'; uv run uvicorn songgeneration_mcp.server:app --host 127.0.0.1 --port 10885 --reload

# Serve MCP (stdio)
serve-mcp:
    Set-Location '{{justfile_directory()}}'; uv run python -m songgeneration_mcp.mcp_server

# Run tests
test:
    Set-Location '{{justfile_directory()}}'; uv run pytest tests/ -q

# Lint
lint:
    Set-Location '{{justfile_directory()}}'; uv run ruff check src/; Set-Location '{{justfile_directory()}}\web_sota'; npx @biomejs/biome ci .

# Fix
fix:
    Set-Location '{{justfile_directory()}}'; uv run ruff check src/ --fix --unsafe-fixes; uv run ruff format src/; Set-Location '{{justfile_directory()}}\web_sota'; npx @biomejs/biome check --write .

# Format check (CI gate)
fmt:
    Set-Location '{{justfile_directory()}}'; uv run ruff format --check src/

# End-to-end verification (integration tests: API boot + health)
e2e:
    Set-Location '{{justfile_directory()}}'; uv run pytest tests/integration -q

# Bootstrap: install dev extras + pre-commit hook (dev is an extra, not a group)
bootstrap:
    Set-Location '{{justfile_directory()}}'; uv sync --extra dev; uv run pre-commit install; Write-Host "Pre-commit hooks installed." -ForegroundColor Green

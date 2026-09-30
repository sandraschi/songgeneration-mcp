# Development — songgeneration-mcp

```powershell
uv sync --extra dev          # runtime + pytest/respx/ruff
just serve                   # API on :10885 (uvicorn --reload)
just serve-mcp               # stdio for Claude Desktop
just test                    # pytest tests/ -q (24 passed 2026-10-01)
just e2e                     # pytest tests/integration -q
just lint                    # ruff check + biome ci
just fix                     # ruff fix + format + biome write
just fmt                     # ruff format --check (CI gate)
just bootstrap               # sync dev extras + pre-commit
just install-all             # music backends (MusicGen/Stable Audio/py deps)
```

Layout: `src/songgeneration_mcp/server.py` (Starlette REST + `/mcp` mount),
`mcp_server.py` (8 MCP tools), `logic.py` (Studio bridge), `acestep.py`
(ACE-Step bridge), `repository.py` (song store), `settings_store.py`.
Backends tried in order: Lyria → ACE-Step → MusicGen → Stable Audio → Studio.
Coverage gate: `fail_under = 50` (`[tool.coverage.report]`).
Do not use `Test-Path ".git"` for repo checks; use `git rev-parse --git-dir`.

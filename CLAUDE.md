# CLAUDE.md — songgeneration-mcp

Fleet Standard MCP server (FastMCP 3.4+, Starlette REST :10885, webapp :10884).

## Entry points
- `just serve` backend · `just serve-mcp` stdio · `just test` / `just e2e` / `just lint`
- Backends order: Lyria → ACE-Step (:8001) → MusicGen → Stable Audio → Studio (:10930)

## Standards that bite here
- Portmanteau tools + Annotated params + `## Return Format`/`## Examples` docstrings
- `GET /api/capabilities` is the REST contract; keep it current when adding routes
- Never fake: unreachable backends return honest empties/errors (see `api_llm_providers`)
- Batch rule: ≤5 files per commit; `.bak` first on 3+ file edits

## Key files
`src/songgeneration_mcp/server.py` (routes) · `mcp_server.py` (8 tools) ·
`logic.py` + `acestep.py` (bridges) · `docs/BACKENDS.md` · `docs/ONBOARDING.md`

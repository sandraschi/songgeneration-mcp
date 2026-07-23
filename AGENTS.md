# songgeneration-mcp Agent Context

Fleet MCP server for AI music generation. See `justfile` for available recipes.

## Quick Ref

```powershell
uv sync                    # Install deps
just serve                 # Start API on :10885
just dev                   # Start webapp on :10884
just test                  # Run tests
just lint                  # Ruff + Biome
just install-all           # Install all music backends
```

## Ports
| Service | Port |
|---------|------|
| API backend | 10885 |
| Webapp frontend | 10884 |

## Architecture
FastMCP 3.4+ server with Starlette REST API. 4 music generation backends tried in order:
Lyria (Vertex AI) → Stable Audio Open (diffusers) → MusicGen (transformers) → Studio SG2 (local API).

## Tools
- `song_generate` — generate music from prompt
- `song_list` — list generated tracks
- `song_export` — export to Plex/Reaper/VirtualDJ

## Key Files
| File | Purpose |
|------|---------|
| `src/songgeneration_mcp/server.py` | Starlette app + all routes |
| `src/songgeneration_mcp/logic.py` | Studio API client |
| `web_sota/src/pages/quick.tsx` | Quick Generate page |
| `docs/BACKENDS.md` | Backend comparison |

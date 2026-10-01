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
FastMCP 3.4+ server with Starlette REST API. 5 music generation backends tried in order:
Lyria (Vertex AI) → ACE-Step 1.5 (:8001) → MusicGen (transformers) → Stable Audio Open (diffusers) → Studio SG2 (:10930).

## Tools
- `generate_song` — generate a song from lyrics + style
- `list_models` — list models available in Studio
- `get_status` — GPU VRAM and queue state
- `cancel_generation` — stop an active task
- `unload_models` — free VRAM
- `diagnostics` — server diagnostic report
- `shutdown` — shut down the server process
- `show_status_card` / `show_models_card` — Prefab in-chat cards
- `help` — server help (levels + lyria topic)

## Key Files
| File | Purpose |
|------|---------|
| `src/songgeneration_mcp/server.py` | Starlette app + all routes |
| `src/songgeneration_mcp/logic.py` | Studio API client |
| `web_sota/src/pages/quick.tsx` | Quick Generate page |
| `docs/BACKENDS.md` | Backend comparison |

# songgeneration-mcp

<div align="center">
  <p><strong>AI Music Generation Server</strong> — 4 backends, one API</p>

  [![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
  [![FastMCP](https://img.shields.io/badge/FastMCP-3.4+-purple?style=flat-square)](https://github.com/jlowin/fastmcp)
  [![License](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](LICENSE)
</div>

Generate music from text prompts. Four backends tried in order — the first available wins:

| Backend | Quality | Requires | First load |
|---------|---------|----------|------------|
| **Lyria 3 Pro** (Vertex AI) | Best | `GOOGLE_CLOUD_PROJECT` env | API call |
| **Stable Audio Open 1.0** | Good (instrumentals) | `diffusers` | ~3GB download |
| **MusicGen-small** (Meta) | Fair | `transformers` | ~2GB download |
| **Studio API** (SG2) | Variable | SongGeneration Studio | Port 10930 |

## Quick Start

```powershell
uv sync
uv run uvicorn songgeneration_mcp.server:app --port 10885
curl http://127.0.0.1:10885/api/v1/generate -d '{"prompt":"tech house 128 BPM"}'
```

## Install Backends

```powershell
# All local backends (recommended)
just install-all

# Or step by step:
uv add transformers scipy              # MusicGen
uv add diffusers soundfile             # Stable Audio Open
uv add google-genai                    # Lyria (requires GCP project)
```

## API

`POST /api/v1/generate` — `{"prompt": "...", "duration": 30}`

Returns `{"success": true, "file": "/tmp/...wav", "backend": "lyria|stableaudio|musicgen|studio", "model": "..."}`

## Documentation

- [Installation](docs/INSTALL.md) — detailed setup, backends, troubleshooting
- [Backends](docs/BACKENDS.md) — comparison, requirements, tips
- [Webapp](docs/WEBAPP.md) — React UI guide
- [MCP Tools](docs/MCP_TOOLS.md) — FastMCP tool reference
- [Architecture](docs/ARCHITECTURE.md) — system design, API, data flow

## Webapp

```powershell
cd web_sota && bun install && bun run dev
```

Opens at `http://127.0.0.1:10884` — generate, preview, export to Mixxx/Plex/Reaper.

## Companion MCP

Exported tracks can be loaded to mixx-dj-mcp decks via REST handoff:
`POST http://127.0.0.1:11116/api/v1/deck/1/load {"track_path": "/tmp/gen.wav"}`

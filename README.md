<div align="center">

# songgeneration-mcp

**One prompt. Several song engines. The first one that works wins.**

An MCP server and React webapp that generate music from text prompts by
trying **four different song-generation tools** in order - Lyria (Vertex
AI), ACE-Step 1.5, Stable Audio 3 and the Studio SG2 API - and returning
the first result that succeeds. Install the backends you want; the server
routes every prompt to the best one you have.

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastMCP](https://img.shields.io/badge/FastMCP-3.4+-purple?style=flat-square)](https://github.com/jlowin/fastmcp)
[![License](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](LICENSE)
[![Backends](https://img.shields.io/badge/backends-4-orange?style=flat-square)](docs/BACKENDS.md)
[![Webapp](https://img.shields.io/badge/webapp-React%20%2B%20Vite%20(dark)-informational?style=flat-square)](docs/WEBAPP.md)

</div>

## Not one model - a toolchain

songgeneration-mcp is a **multi-backend aggregator**, not a single model.
One common API (REST + MCP tools + webapp) fronts several different song
generation tools. Every prompt is tried against the backends **in order**
and the first available one wins:

| Backend | Quality | Requires | First load |
|---------|---------|----------|------------|
| **Lyria 3 Pro** (Vertex AI) | Best | `GOOGLE_CLOUD_PROJECT` env | API call |
| **ACE-Step 1.5** (local API) | Very good - full songs w/ vocals, MIT | `uv run acestep-api` on :8001 | ~2GB |
| **Stable Audio 3** (Stability AI) | Good - fast instrumentals | `uv add --optional full stable-audio-3` | ~2GB |
| **Studio API** (SG2) | Variable | SongGeneration Studio | Port 10930 |

So with Lyria configured you get the best quality, with only local backends
you still get full songs from ACE-Step, and with nothing installed the API
tells you exactly which backend to install - it never fails silently. See
[docs/BACKENDS.md](docs/BACKENDS.md) for the full comparison.

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
uv add --optional full stable-audio-3    # Stable Audio 3 (local)
git clone https://github.com/ACE-Step/ACE-Step-1.5  # ACE-Step server (local, MIT)
uv add google-genai                    # Lyria (requires GCP project)
```

## API

`POST /api/v1/generate` - `{"prompt": "...", "duration": 30}`

Returns `{"success": true, "file": "/tmp/...wav", "backend": "lyria|acestep|stableaudio|studio", "model": "..."}`

## Documentation

- [Installation](docs/INSTALL.md) - detailed setup, backends, troubleshooting
- [Backends](docs/BACKENDS.md) - comparison, requirements, tips
- [Webapp](docs/WEBAPP.md) - React UI guide
- [MCP Tools](docs/MCP_TOOLS.md) - FastMCP tool reference
- [Architecture](docs/ARCHITECTURE.md) - system design, API, data flow

## Webapp

```powershell
cd web_sota && bun install && bun run dev
```

Opens at `http://127.0.0.1:10884` - generate, preview, export to Mixxx/Plex/Reaper.

## Companion MCP

Exported tracks can be loaded to mixx-dj-mcp decks via REST handoff:
`POST http://127.0.0.1:11116/api/v1/deck/1/load {"track_path": "/tmp/gen.wav"}`

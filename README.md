<div align="center">

# songgeneration-mcp

**One prompt. Several song engines. The first one that works wins.**

An MCP server and React webapp that generate music from text prompts by
trying local and cloud engines in order and returning the first result
that succeeds. The chain is Lyria, ACE-Step 1.5, [audio-studio-mcp](https://github.com/kanaworksai-hue/audio-studio-mcp)
(Stable Audio 3 on an NVIDIA GPU), the local Stable Audio 3 CPU service,
MusicGen, Stable Audio Open 1.0, then Studio SG2. See
[docs/AUDIO_STUDIO.md](docs/AUDIO_STUDIO.md).

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
| **Lyria 3 Pro** (Vertex AI) | Best, with vocals | `GOOGLE_CLOUD_PROJECT` | API call |
| **ACE-Step 1.5** (local API) | Full songs with vocals, MIT | `uv run acestep-api` on port 8001 | ~2GB |
| **audio-studio-mcp** | Stable Audio 3 medium, instrumental | NVIDIA GPU, `install.ps1`, HTTP MCP | ~5 GB VRAM |
| **SA3 CPU service** | Stable Audio 3 small, instrumental | `stable-audio-spike` on port 11250 | ~2 GB RAM |
| **MusicGen-small** | Simple loops | `uv sync --extra full` | ~2GB |
| **Stable Audio Open 1.0** | Old instrumental model, CUDA only | gated HF repo, `uv sync --extra full` | ~3GB |
| **Studio API** (SG2) | Variable, with vocals | SongGeneration Studio | Port 10930 |

Lyria and ACE-Step are the vocal paths. With neither of those running, an
instrumental still comes back from audio-studio-mcp or the CPU service on
port 11250. Stable Audio Open 1.0 is the old CUDA-only model and is not
that path. See [docs/BACKENDS.md](docs/BACKENDS.md).

## Quick Start

```powershell
uv sync
uv run uvicorn songgeneration_mcp.server:app --port 10885
curl http://127.0.0.1:10885/api/v1/generate -d '{"prompt":"tech house 128 BPM"}'
```

## Install Backends

```powershell
# CPU Stable Audio 3 (already the working instrumental path on this machine)
# from D:\Dev\repos\stable-audio-spike
service\start.ps1

# NVIDIA Stable Audio 3 medium (audio-studio-mcp). Gated weights, HF login.
git clone https://github.com/kanaworksai-hue/audio-studio-mcp.git
git clone https://github.com/ACE-Step/ACE-Step-1.5  # ACE-Step server (local, MIT)
```

## API

`POST /api/v1/generate` - `{"prompt": "...", "duration": 30}`

Returns `{"success": true, "file": "<wav path>", "backend": "lyria|acestep|audiostudio|sa3|musicgen|stableaudio|studio", "model": "..."}`

## Documentation

- [Installation](docs/INSTALL.md) - detailed setup, backends, troubleshooting
- [Backends](docs/BACKENDS.md) - comparison, requirements, tips
- [Stable Audio 3](docs/AUDIO_STUDIO.md) - why generation was a no-op, and the two local engines
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

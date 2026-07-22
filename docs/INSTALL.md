# Installation

## Prerequisites

- Python 3.12+
- uv (package manager)
- CUDA-capable GPU recommended (RTX 4090 works) for local models

## Quick Install

```powershell
git clone https://github.com/sandraschi/songgeneration-mcp
cd songgeneration-mcp
uv sync
```

## Backend-Specific Setup

### All Local Backends (recommended)

```powershell
just install-all
```

This installs transformers (MusicGen), diffusers (Stable Audio), and google-genai (Lyria if GCP configured).

### Individual Backends

| Backend | Command | First-load size |
|---------|---------|-----------------|
| MusicGen | `uv add transformers scipy` | ~2GB |
| Stable Audio Open | `uv add diffusers soundfile` | ~3GB |
| Lyria | `uv add google-genai` + set `GOOGLE_CLOUD_PROJECT` | None (API) |
| Studio API | Install SongGeneration-Studio separately | ~5GB |

### Lyria (Google Vertex AI)

```powershell
$env:GOOGLE_CLOUD_PROJECT = "your-gcp-project"
uv add google-genai
```

Requires a Google Cloud Project with Vertex AI enabled. The model "lyria-3-pro-preview" must be accessible.

### Studio API

The Studio API runs on port 10930. Install SongGeneration-Studio separately:

```powershell
git clone https://github.com/BazedFrog/SongGeneration-Studio
cd SongGeneration-Studio && uv sync
uv run python app.py
```

## Verification

```powershell
uv run uvicorn songgeneration_mcp.server:app --port 10885
curl http://127.0.0.1:10885/api/v1/generate -d '{"prompt":"test","duration":5}'
```

If any backend is missing, the server logs a warning and skips it.

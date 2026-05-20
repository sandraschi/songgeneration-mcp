# songgeneration-mcp

<p align="center">
  <a href="https://github.com/casey/just"><img src="https://img.shields.io/badge/just-ready_to_go-7c5cfc?style=flat-square&logo=just&logoColor=white" alt="Just"></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.13+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://github.com/PrefectHQ/fastmcp"><img src="https://img.shields.io/badge/FastMCP-3.2-7c5cfc?style=flat-square" alt="FastMCP"></a>
</p>

**Repository:** [github.com/sandraschi/songgeneration-mcp](https://github.com/sandraschi/songgeneration-mcp)

MCP server for **Tencent SongGeneration v2 (LeVo 2 / SG2)** via [SongGeneration-Studio](https://github.com/BazedFrog/SongGeneration-Studio). Local open-weight music generation: SG2 structural length tags, dual-track output (`vocal.wav` + `inst.wav`), optional style-clone from a reference audio clip.

---

## Architecture

```
Claude Desktop / any MCP client
        │  MCP (stdio or streamable-HTTP /mcp)
        ▼
songgeneration-mcp  (this repo)
  ├── FastMCP server  — tools, resources, prompts
  ├── Starlette ASGI  — REST API + web dashboard (port 10885)
  └── Web dashboard   — React/Vite (port 10884)
        │  HTTP REST  (default http://localhost:10930)
        ▼
SongGeneration-Studio  (separate repo — BazedFrog/SongGeneration-Studio)
  ├── Gradio + REST API
  ├── model-server subprocess  (tencent/SongGeneration weights)
  └── GPU inference  (RTX 3090/4090, ~22 GB VRAM for v2-large bfloat16)
```

**SongGeneration-Studio is a separate project** — not included when you clone this repo. Clone [github.com/BazedFrog/SongGeneration-Studio](https://github.com/BazedFrog/SongGeneration-Studio) and follow its setup instructions. This MCP repo is the **control plane**; Studio is the **GPU inference process**.

---

## Quick Start

```powershell
git clone https://github.com/sandraschi/songgeneration-mcp
cd songgeneration-mcp
just
```

This opens an interactive dashboard showing all available commands. Run `just bootstrap` to install dependencies, then `just serve` or `just dev` to start.

### Manual Setup

If you don't have `just` installed:


## Installation

### Prerequisites
- [uv](https://docs.astral.sh/uv/) (recommended)
- Python 3.12+
- SongGeneration-Studio (see above)

### Quick start via uvx
```bash
uvx songgeneration-mcp
```

### Claude Desktop integration
Add to `claude_desktop_config.json`:
```json
"mcpServers": {
  "songgeneration-mcp": {
    "command": "uv",
    "args": ["--directory", "D:/Dev/repos/songgeneration-mcp", "run", "songgeneration-mcp"]
  }
}
```

### Studio location
- Default: `D:\Dev\repos\external\SongGeneration-Studio`
- Override: set `SONGGEN_STUDIO_DIR` env var, or configure `studio_dir` in Settings
- Remote-only: set `studio_url` to a Studio instance on another host; no local checkout needed

---

## Web dashboard

React + Vite app in `web_sota/` on port **10884**; MCP HTTP on **10885**. Start: `web_sota\start.ps1`.

Pages: Home, Tools, Status, App Hub, Generate, Listen, Local LLM, Chat, Logger, Help (tabbed deep docs), Settings.

**Logs:** `GET /api/logs` — real in-process ring buffer of Python `logging` output (size `SONGGEN_LOG_BUFFER_LINES`, default 500). `POST /api/logs/clear` clears it.

Short guide: [web_sota/README.md](web_sota/README.md) · Route map: [web_sota/docs/PAGES.md](web_sota/docs/PAGES.md)

---

## Studio auto-start

The MCP backend auto-starts Studio for local URLs when `uv` is on `PATH` (disable: `SONGGEN_STUDIO_AUTO_START=0`). `web_sota\start.ps1` does the same: if nothing is listening on port 10930 and `main.py` exists under the Studio directory, it launches Studio before starting the dashboard.

Studio URL override env vars (in priority order):
1. `SONGGENERATION_STUDIO_URL`
2. `SONGGEN_STUDIO_BASE_URL`
3. Default: `http://localhost:10930`

---

## SG2 defaults (LeVo 2)

| Setting | Default |
| --- | --- |
| Model repo | `tencent/SongGeneration` |
| Weights | `v2-large` |
| Max length | 270 seconds (4.5 min) |
| dtype | `bfloat16` (~22 GB VRAM) |
| Output | 48 kHz stereo dual-track (`vocal.wav` + `inst.wav`) |

---

## Lyrics format (SG2)

SG2 uses `;` as section separator and optional length tags embedded in the lyric string:

```
[intro-medium] ; [verse] The strings arise in the Konzerthaus hall. ; [chorus] Rise and fall. ; [inst-short] ; [outro-short]
```

**Length tags** (embed in lyrics for section timing):
- `[intro-short]` (0–10s) · `[intro-medium]` (10–20s)
- `[inst-short]` · `[inst-medium]`
- `[outro-short]` · `[outro-medium]`

**English rule:** each English line should end with `.` before `;`. Enable `auto_fix_english_punctuation=True` (default) to have the server insert missing periods automatically.

MCP resource `sg2://structural-tags` has the full tag reference.

---

## `generate_song` parameters

| Parameter | Default | Notes |
| --- | --- | --- |
| `lyrics` | required | Full lyrics with SG2 tags |
| `genre` | `Pop` | |
| `mood` | `Happy` | |
| `tempo` | `120` | BPM |
| `voice` | `Female` | `Male` or `Female` |
| `separate_stems` | `True` | Dual-track output |
| `model_repo` | `tencent/SongGeneration` | |
| `model_weights` | `v2-large` | |
| `max_length_seconds` | `270` | |
| `torch_dtype` | `bfloat16` | |
| `style_audio_prompt_path` | `None` | Path on Studio host to ~10s WAV for style cloning |
| `mix_dual_tracks` | `False` | Prefer single mixed master |
| `auto_fix_english_punctuation` | `True` | Insert `.` before `;` for English segments |

---

## Local media, Plex, and DAW export

- Generated audio is downloaded to local storage and served from `GET /api/media/{file_path}`
- Optional MP3 transcode (`transcode_to_mp3`) via system `ffmpeg` or `imageio-ffmpeg`
- **Plex:** `POST /api/export/plex` — copies local MP3 to configured Plex import folder
- **VirtualDJ:** `POST /api/export/virtualdj` — loads track to deck, with `auto_play`, `sync_to_master`, `cue_at_start` options
- **Reaper:** `POST /api/export/reaper` — copies to Reaper drop dir and optionally triggers import

---

## SG2 vs Gemini Lyria 3 Pro

| | **LeVo 2 / SG2** (this MCP) | **Gemini Lyria 3 Pro** |
| --- | --- | --- |
| **Model type** | Discrete-codec transformer | Diffusion-based |
| **Weights** | Open (Hugging Face) | Closed, cloud-only |
| **Where it runs** | Local GPU | Google cloud |
| **Cost** | Hardware + electricity; no per-song meter | ~$0.08/track in typical Gemini credits (verify) |
| **Stems at generation** | `vocal.wav` + `inst.wav` natively | Single mix |
| **Section control** | SG2 length tags in lyrics | Prompt wording only |
| **Training priors** | Tencent catalog, C-pop, broader genres | Google-licensed, Western pop/rock |
| **Latency** | 2–10 min (RTX 4090) | Seconds to ~2 min |
| **VRAM** | ~22 GB (v2-large bfloat16) | None (cloud) |

**Practical split:** Lyria for fast iteration and mainstream Western polish; SG2 for stems, structural timing, non-Western priors, on-prem sovereignty, or style-cloning from a reference clip. Many workflows use both.

Full comparison: [`docs/LYRIA_VS_SG2.md`](docs/LYRIA_VS_SG2.md) · MCP resource `docs://lyria-vs-sg2` · `help(topic="lyria")`

---

## MCP resources

| Resource URI | Contents |
| --- | --- |
| `sg2://structural-tags` | SG2 length tags and dual-track output reference |
| `docs://lyria-vs-sg2` | Full SG2 vs Lyria 3 Pro technical comparison |
| `api://song-request-schema` | JSON schema for generation requests |
| `system://gpu-status` | Real-time GPU/VRAM telemetry |

---

## Development

```bash
# Install dev dependencies
uv sync --extra dev

# Lint / format
just lint
just fix

# Run tests
just test

# Start dev server (MCP HTTP + web dashboard)
just dev
```

---

## Quality stack

- **Python:** [Ruff](https://astral.sh/ruff) linting + formatting. Zero-tolerance `T201` (no `print` in handlers).
- **Frontend:** [Biome](https://biomejs.dev/) with strict `noConsoleLog`.
- **Protocol:** hardened stdout/stderr isolation for crash-resistant JSON-RPC.
- **Automation:** [Justfile](./justfile) for all fleet ops.
- **Security:** `bandit` + `safety` audits.

## License

See LICENSE file.

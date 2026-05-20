# SonggenerationMcp

[![FastMCP Version](https://img.shields.io/badge/FastMCP-3.1.0-blue?style=flat-square&logo=python&logoColor=white)](https://github.com/sandraschi/fastmcp) [![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff) [![Linted with Biome](https://img.shields.io/badge/Linted_with-Biome-60a5fa?style=flat-square&logo=biome&logoColor=white)](https://biomejs.dev/) [![Built with Just](https://img.shields.io/badge/Built_with-Just-000000?style=flat-square&logo=gnu-bash&logoColor=white)](https://github.com/casey/just)

**Repository:** [github.com/sandraschi/songgeneration-mcp](https://github.com/sandraschi/songgeneration-mcp)

Tencent SongGeneration v2 (LeVo 2 / SG2) MCP server via SongGeneration-Studio.
Supports SG2 structural tags, dual-track output (`vocal.wav` + `inst.wav`), and optional style-cloning prompt audio.

##  Installation

### Prerequisites
- [uv](https://docs.astral.sh/uv/) installed (RECOMMENDED)
- Python 3.12+

### SongGeneration-Studio (not in this repo)

**SongGeneration-Studio is a separate project** — it is **not** included when you clone [sandraschi/songgeneration-mcp](https://github.com/sandraschi/songgeneration-mcp). Upstream Studio repo: **[github.com/BazedFrog/SongGeneration-Studio](https://github.com/BazedFrog/SongGeneration-Studio)**. Clone that (or use any checkout whose root has `main.py` for the Studio HTTP server). This MCP repo is only the **control plane**; Studio is the **GPU inference / audio** process (default URL `http://localhost:10930`).

- Point the MCP server at Studio with **`SONGGENERATION_STUDIO_URL`** / **`studio_url`** in settings, or rely on the default.
- **`web_sota\start.ps1`** and backend auto-start use **`SONGGEN_STUDIO_DIR`** when set; otherwise the default checkout path is **`D:\Dev\repos\external\SongGeneration-Studio`** (clone [SongGeneration-Studio](https://github.com/BazedFrog/SongGeneration-Studio) there, or set the env var to your path).
- Remote-only: set **`studio_url`** to a Studio instance elsewhere; no local checkout required.

###  Quick Start
Run immediately via `uvx`:
```bash
uvx songgeneration-mcp
```

###  Claude Desktop Integration
Add to your `claude_desktop_config.json`:
```json
"mcpServers": {
  "songgeneration-mcp": {
    "command": "uv",
    "args": ["--directory", "D:/Dev/repos/songgeneration-mcp", "run", "songgeneration-mcp"]
  }
}
```
## Usage

```bash
python -m songgeneration_mcp.mcp_server
```

## Web dashboard (fleet UI)

React + Vite app in **`web_sota/`**: Home, Tools, Status, App Hub, **Generate**, **Listen**, **Local LLM**, **Chat**, **Logger**, **Help** (tabbed deep docs), Settings. Ports **10884** (frontend) / **10885** (MCP HTTP)  run `web_sota\start.ps1`. Short guide: [web_sota/README.md](web_sota/README.md); route map: [web_sota/docs/PAGES.md](web_sota/docs/PAGES.md).

**Logs:** The dashboard reads **`GET /api/logs`**  a real in-process ring buffer of Python `logging` output (size `SONGGEN_LOG_BUFFER_LINES`, default 500). `POST /api/logs/clear` clears that buffer. This does not include SongGeneration-Studio logs unless you forward them into this process.

## Studio target (local-first, cloud-capable)

- Default Studio URL is **`http://localhost:10930`** (non-colliding fleet port).
- Override with:
  - `SONGGENERATION_STUDIO_URL`
  - `SONGGEN_STUDIO_BASE_URL`
- The app supports both deployment modes:
  - **Local GPU**: Studio on the user machine.
  - **Remote GPU/cloud**: Studio on a remote host.
- Web settings and API:
  - `GET/POST /api/settings` includes `studio_url` and `plex_export_dir`
  - `GET /api/studio/info` exposes Studio URL + reachability + direct UI link.
- Auto-start behavior (local default):
  - The MCP backend can auto-start Studio for local URLs via **`uv run --directory <studio> python main.py …`** when `uv` is on `PATH` (disable with `SONGGEN_STUDIO_AUTO_START=0`). If `uv` is missing, it falls back to `SONGGEN_STUDIO_PYTHON`, then `python`, then `py -3`.
  - **`web_sota\start.ps1`** starts SongGeneration-Studio the same way (if nothing is already listening on **10930** and `main.py` exists under `SONGGEN_STUDIO_DIR` / default `D:\Dev\repos\external\SongGeneration-Studio`). Remote-only setups: point `studio_url` at your Studio host and skip local Studio.

## Local media storage and Plex export

- Generated source audio URLs are downloaded to local storage when reachable and served from:
  - `GET /api/media/{file_path}`
- Optional MP3 transcode (`transcode_to_mp3`) writes local MP3 files (uses system `ffmpeg` or dependency `imageio-ffmpeg`).
- Listen page provides comfortable playback and export:
  - `POST /api/export/plex` copies local MP3 files to configured Plex import folder.

## VirtualDJ handoff (deck workflow)

- Listen page supports deck handoff to `virtualdj-mcp` with:
  - deck selector (`1-4`)
  - auto-play toggle
  - sync-to-master toggle
  - cue-at-start toggle
- Backend flow (`POST /api/export/virtualdj`) now supports:
  - `deck`
  - `auto_play`
  - `sync_to_master`
  - `cue_at_start`
- Status endpoint:
  - `GET /api/export/virtualdj/status` checks VirtualDJ API reachability.

## SG2 Defaults (LeVo 2)

- Model repo: `tencent/SongGeneration`
- Weights: `v2-large`
- Max length: `270` seconds (4.5 minutes)
- Dtype: `bfloat16`
- Output target: 48 kHz stereo dual-track tokens (`vocal.wav`, `inst.wav`)

## Lyrics Rules (SG2)

- Use structural tags when needed: `[intro-short]`, `[intro-medium]`, `[inst-short]`, `[inst-medium]`, `[outro-short]`, `[outro-medium]`
- English lines should end with `.` before section separator `;`
- Example: `[verse] The strings arise in the Konzerthaus hall. ; [chorus]`

## `generate_song` (new SG2 args)

Additional tool args now supported:
- `model_repo`
- `model_weights`
- `max_length_seconds`
- `torch_dtype`
- `style_audio_prompt_path` (for ~10s style cloning prompt)
- `mix_dual_tracks`
- `auto_fix_english_punctuation`

Server resource:
- `sg2://structural-tags` for quick SG2 tag/output reference.
- `docs://lyria-vs-sg2`  **LeVo 2 (SG2)** vs **Gemini Lyria 3 Pro** (pricing fit, local vs cloud).

## Landscape: SG2 vs Gemini Lyria 3 Pro (~March 2026)

| | **LeVo 2 / SG2** (this MCP) | **Gemini Lyria 3 Pro** |
| --- | --- | --- |
| **Where it runs** | **Local** (SongGeneration-Studio + your GPU) | **Cloud** (Gemini / Google AI) |
| **Cost** | Hardware + electricity; no per-song cloud fee | Often **~$0.08 per song** in typical Gemini credit economics (**verify** in-app) |
| **Sweet spot** | **Classical**, **rubato**, **instrumental** nuance; SG2 length tags | Fast iteration, polish, **Google AI** ecosystem integration |

**Takeaway:** Lyria is a bargain for shipped demos; SG2 is the open-weight, section-precise option when you want **sovereignty** or nonUS-default musical priorswithout dismissing Googles AI push (many teams use **both**).

More detail: `docs/LYRIA_VS_SG2.md`, `docs/PRD.md`, or MCP `help(topic="lyria")`.

## Claude Desktop Configuration

Add to `~/.config/claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "songgeneration-mcp": {
      "command": "python",
      "args": ["-m", "songgeneration_mcp", "mcp_server"],
      "cwd": "/path/to/songgeneration-mcp"
    }
  }
}
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check .

# Format
ruff format .
```


## 🛡️ Industrial Quality Stack

This project adheres to **SOTA 14.1** industrial standards for high-fidelity agentic orchestration:

- **Python (Core)**: [Ruff](https://astral.sh/ruff) for linting and formatting. Zero-tolerance for `print` statements in core handlers (`T201`).
- **Webapp (UI)**: [Biome](https://biomejs.dev/) for sub-millisecond linting. Strict `noConsoleLog` enforcement.
- **Protocol Compliance**: Hardened `stdout/stderr` isolation to ensure crash-resistant JSON-RPC communication.
- **Automation**: [Justfile](./justfile) recipes for all fleet operations (`just lint`, `just fix`, `just dev`).
- **Security**: Automated audits via `bandit` and `safety`.

## License

See LICENSE file for details.

## Author

MCP Studio

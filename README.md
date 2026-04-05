# SonggenerationMcp

**Repository:** [github.com/sandraschi/songgeneration-mcp](https://github.com/sandraschi/songgeneration-mcp)

Tencent SongGeneration v2 (LeVo 2 / SG2) MCP server via SongGeneration-Studio.
Supports SG2 structural tags, dual-track output (`vocal.wav` + `inst.wav`), and optional style-cloning prompt audio.

##  Installation

### Prerequisites
- [uv](https://docs.astral.sh/uv/) installed (RECOMMENDED)
- Python 3.12+

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

React + Vite app in **`web_sota/`**: Overview, Tools, Status, App Hub, **Generate**, **Listen**, **Local LLM**, **Chat**, **Logger**, **Help** (tabbed deep docs), Settings. Ports **10884** (frontend) / **10885** (MCP HTTP)  run `web_sota\start.ps1`. Short guide: [web_sota/README.md](web_sota/README.md); route map: [web_sota/docs/PAGES.md](web_sota/docs/PAGES.md).

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
  - backend attempts to auto-start Studio for local URLs before status/generate calls.
  - `web_sota\start.ps1` also auto-launches Studio from `D:\Dev\repos\external\SongGeneration-Studio` (override with `SONGGEN_STUDIO_DIR`).
  - disable backend auto-start with `SONGGEN_STUDIO_AUTO_START=0`.

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

## License

See LICENSE file for details.

## Author

MCP Studio

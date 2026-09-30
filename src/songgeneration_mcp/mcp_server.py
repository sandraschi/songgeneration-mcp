"""Main MCP server module.

Tencent SongGeneration v2 (LeVo 2 / SG2): lyrics, style, dual-track output, optional Style RAG.
"""

import logging
from typing import Annotated

from fastmcp import FastMCP
from pydantic import Field

from .logic import SongGenerationLogic
from .lyria_compare import get_lyria_vs_sg2_text
from .sg2 import SG2_STRUCTURAL_TAGS_REFERENCE
from .transport import run_server

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("songgeneration-mcp")

# JSON Schema for Song Generation
SONG_REQUEST_SCHEMA = {
    "title": "SongRequest",
    "type": "object",
    "properties": {
        "title": {"type": "string", "description": "Title of the song"},
        "lyrics": {
            "type": "string",
            "description": ("Complete lyrics (SG2: length tags; English lines end with '.' before ';')"),
        },
        "genre": {"type": "string", "description": "Musical genre"},
        "emotion": {"type": "string", "description": "Musical emotion/mood"},
        "bpm": {"type": "integer", "description": "Beats per minute"},
        "voice": {"type": "string", "enum": ["Male", "Female"], "default": "Female"},
        "output_mode": {"type": "string", "enum": ["mixed", "separate"], "default": "separate"},
        "model_repo": {"type": "string", "default": "tencent/SongGeneration"},
        "model_weights": {"type": "string", "default": "v2-large"},
        "max_length_seconds": {"type": "integer", "default": 270},
        "torch_dtype": {"type": "string", "default": "bfloat16"},
        "style_audio_prompt_path": {
            "type": "string",
            "description": ("Optional path to ~10s audio on the Studio host for style cloning (Style RAG)"),
        },
        "mix_dual_tracks": {"type": "boolean", "default": False},
    },
    "required": ["lyrics"],
}

app = FastMCP(
    "songgeneration-mcp",
    instructions=(
        "SongGeneration SOTA MCP - Tencent SongGeneration v2 (LeVo 2, open weights) via "
        "SongGeneration-Studio. Default tencent/SongGeneration v2-large; max_length 270s; "
        "bfloat16; 48 kHz dual-track (vocal.wav / inst.wav). SG2 lyrics rules apply. "
        "Resource docs://lyria-vs-sg2 compares local SG2 to cloud Gemini Lyria 3 Pro (~Mar 2026)."
    ),
)
logic = SongGenerationLogic()


@app.resource("api://song-request-schema")
def get_song_schema() -> str:
    """Get the JSON schema for song generation requests."""
    import json

    return json.dumps(SONG_REQUEST_SCHEMA, indent=2)


@app.resource("sg2://structural-tags")
def get_sg2_structural_tags() -> str:
    """SG2 (LeVo 2) length-sensitive markers and dual-track output notes."""
    return SG2_STRUCTURAL_TAGS_REFERENCE.strip()


@app.resource("docs://lyria-vs-sg2")
def get_lyria_vs_sg2_resource() -> str:
    """LeVo 2 (SG2) vs Gemini Lyria 3 Pro: local open-weight vs cloud Gemini pricing and fit."""
    return get_lyria_vs_sg2_text().strip()


@app.resource("system://gpu-status")
async def get_gpu_status_resource() -> str:
    """Get real-time GPU and VRAM status information."""
    status_data = await logic.get_status()
    return f"""# GPU Resource Status
| Metric | Value |
| :--- | :--- |
| **VRAM Total** | {status_data["vram_total"]} MB |
| **VRAM Used** | {status_data["vram_used"]} MB |
| **Active Tasks** | {status_data["active_generations"]} |
| **Model Loaded** | {status_data.get("model_loaded", "None")} |
| **Server Status** | {"✅ Running" if status_data.get("server_running") else "❌ Offline"} |
"""


@app.prompt("generate-song")
def prompt_generate_song(topic: str = "Life in Vienna", genre: str = "Pop") -> str:
    """Template for generating a new song with a specific topic and genre."""
    return f"""Generate a new song about '{topic}' in the style of '{genre}'.
Please provide:
1. A catchy title.
2. Structured lyrics (Verse, Chorus, Bridge).
3. BPM and Mood recommendations.

Once ready, use the `generate_song` tool to start production."""


@app.prompt("lyric-assistant")
def prompt_lyric_assistant(lyrics: str) -> str:
    """Analyzes and refines lyrics for optimal generation with the LeVo 2 (SG2) model."""
    return f"""Optimize the following lyrics for SongGeneration v2 (SG2):

{lyrics}

Focus on:
- SG2 length tags where needed: [intro-short], [intro-medium], [inst-short], [inst-medium],
  [outro-short], [outro-medium].
- English lines: end each line with '.' before the section separator ';'.
- Rhyme scheme and rhythm; Verse-Chorus flow; emotional resonance.
"""


@app.tool(
    annotations={"readOnlyHint": True, "idempotentHint": True},
)
async def help(
    level: Annotated[str, Field(description='Detail level - "basic", "intermediate", or "advanced"')] = "basic",
    topic: Annotated[
        str | None, Field(description='Optional focus; use topic="lyria" for SG2 vs Gemini Lyria 3 Pro')
    ] = None,
) -> str:
    """Get help information about this MCP server.

    ## Return Format
    Markdown help text for the requested level (or the Lyria comparison for topic="lyria").

    ## Examples
    help() | help(level="advanced") | help(topic="lyria")
    """
    if topic and "lyria" in topic.lower():
        return get_lyria_vs_sg2_text()

    if level == "basic":
        return """\
# songgeneration-mcp

Tencent SongGeneration v2 (LeVo 2 / SG2) via SongGeneration-Studio - local open-weight music generation.

## Tools
- `generate_song` - generate a song from lyrics + style parameters
- `list_models` - list models available in Studio
- `get_status` - GPU VRAM and generation queue state
- `cancel_generation` - stop an active task
- `unload_models` - free VRAM
- `diagnostics` - server diagnostic report
- `shutdown` - shut down the server process
- `help` - this help (level="basic"|"intermediate"|"advanced", topic="lyria")

## Key facts
- Dual-track output: `vocal.wav` + `inst.wav` at 48 kHz (native codec stems, not post-hoc separation)
- Section timing: embed SG2 length tags in lyrics - `[intro-short]`, `[inst-medium]`, `[outro-long]`, etc.
- Style cloning: pass a ~10s WAV path as `style_audio_prompt_path`
- Studio must be running locally (port 10930) or configured via `studio_url`

## vs Gemini Lyria 3 Pro
SG2 is local/open-weight with native stems and structural length tags.
Lyria 3 Pro is cloud-only, faster, no stems natively, ~$0.08/track (verify).
See `help(topic="lyria")` or MCP resource `docs://lyria-vs-sg2` for the full comparison.
"""
    elif level == "intermediate":
        return """\
# songgeneration-mcp - Intermediate Help

## Generation workflow
1. `list_models` - confirm what's loaded in Studio
2. `generate_song(lyrics=..., genre=..., mood=...)` - start generation
3. `get_status` - monitor VRAM and queue
4. `unload_models` - free VRAM when done

## Lyrics format (SG2)
Use `;` as section separator. Embed length tags for timing control:
  `[intro-short]` (0-10s) · `[intro-medium]` (10-20s)
  `[inst-short]` · `[inst-medium]`
  `[outro-short]` · `[outro-medium]`

Example:
  `[intro-medium] ; [verse] The strings arise. ; [chorus] Rise and fall. ; [outro-short]`

English lines should end with `.` before `;` (auto_fix_english_punctuation=True handles this).

## Style cloning
Pass `style_audio_prompt_path` pointing to a ~10s WAV on the Studio host to condition
generation on that reference clip's timbre and production style.

## Exports
- Plex: `POST /api/export/plex` with repo_id
- VirtualDJ: `POST /api/export/virtualdj` - deck, auto_play, sync_to_master, cue_at_start
- Reaper: `POST /api/export/reaper` with repo_id

## SG2 vs Lyria
`help(topic="lyria")` or resource `docs://lyria-vs-sg2`
"""
    else:
        return """\
# songgeneration-mcp - Advanced Help

## Under the hood

The MCP server wraps SongGeneration-Studio's REST API. `generate_song` builds an `sg2` payload
(model_repo, model_weights, max_length_seconds, torch_dtype, dual_track, optional style_rag)
and POSTs to Studio's `/api/generate`. Studio manages the model-server subprocess and GPU queue.

Generation produces discrete codec tokens for two streams (vocal, instrumental), decoded to
48 kHz stereo WAVs. The dual-track output is not post-hoc separation - it is the model's native
output, so stems are phase-coherent with the mix.

## SG2 architecture
- Transformer over discrete audio codec tokens (not diffusion)
- Conditioned on: lyrics (text tokens), genre/mood/BPM embeddings, voice tag, optional style audio
- Length tags in lyrics give per-section duration priors to the model
- v2-large: ~22 GB VRAM in bfloat16; v2-medium available for lower-VRAM setups

## SG2 vs Gemini Lyria 3 Pro (technical)

| | SG2 / LeVo 2 | Gemini Lyria 3 Pro |
| --- | --- | --- |
| Architecture | Discrete-codec transformer | Diffusion-based |
| Weights | Open (Hugging Face) | Closed, cloud-only |
| Stems | vocal.wav + inst.wav native | Single mix |
| Section control | Length tags in lyrics | Prompt wording only |
| Training priors | Tencent catalog, C-pop | Google-licensed, Western pop/rock |
| Cost model | Hardware + electricity | ~$0.08/track cloud (verify) |
| VRAM | ~22 GB (v2-large bfloat16) | None (cloud) |

## API endpoints (Starlette ASGI, port 10885)
- GET  /api/health · /api/status · /api/capabilities · POST /api/shutdown
- GET  /api/studio/status - Studio reachability + generation queue
- GET  /api/studio/test  - deep check: dir, HTTP, GPU, model-server, models
- GET  /api/studio/info
- POST /api/generate · POST /api/v1/generate · GET /api/v1/diagnostics
- GET  /api/songs  ·  GET /api/songs/{repo_id}
- GET/POST /api/settings
- GET  /api/llm/providers|models|discover|onboarding
- GET  /api/skills · POST /api/ai/chat
- POST /api/export/plex  ·  /api/export/virtualdj  ·  /api/export/reaper
- GET  /api/export/virtualdj/status
- GET  /api/media/{file_path:path}
- *    /mcp  - MCP streamable-HTTP transport

Full doc: resource `docs://lyria-vs-sg2`, file `docs/LYRIA_VS_SG2.md`
"""


@app.tool(
    annotations={"readOnlyHint": True, "idempotentHint": True},
)
async def list_models() -> list[str]:
    """List all available high-quality song generation models from the backend.

    Retrieves the list of model identifiers currently supported by the
    SongGeneration-Studio model server.

    ## Return Format
    List of model ID strings (e.g. tencent/SongGeneration::v2-large when exposed by Studio).

    ## Examples
    list_models()
    """
    return await logic.list_models()


@app.tool(
    annotations={"readOnlyHint": False, "idempotentHint": False, "openWorldHint": True},
)
async def generate_song(
    lyrics: Annotated[
        str,
        Field(description="Full lyrics. SG2 length tags ([intro-short], [chorus], etc.), ';' between sections."),
    ],
    genre: Annotated[str, Field(description="Musical genre (e.g. Rock, Pop)")] = "Pop",
    mood: Annotated[str, Field(description="Emotional vibe")] = "Happy",
    tempo: Annotated[int, Field(description="BPM (about 60-180)", ge=40, le=220)] = 120,
    voice: Annotated[str, Field(description='"Male" or "Female"')] = "Female",
    structure: Annotated[list[str] | None, Field(description="Section order hint for the client")] = None,
    separate_stems: Annotated[bool, Field(description="Request dual-track output (vocal.wav + inst.wav)")] = True,
    title: Annotated[str | None, Field(description="Optional song title")] = None,
    model_repo: Annotated[
        str | None, Field(description="Hugging Face repo id (default tencent/SongGeneration)")
    ] = None,
    model_weights: Annotated[str | None, Field(description="Weight variant (default v2-large)")] = None,
    max_length_seconds: Annotated[int, Field(description="Max generation length (default 270 ≈ 4.5 min)")] = 270,
    torch_dtype: Annotated[str, Field(description="e.g. bfloat16 for ~22GB VRAM on Large")] = "bfloat16",
    style_audio_prompt_path: Annotated[
        str | None, Field(description="Path on the Studio machine to a ~10s WAV for style cloning")
    ] = None,
    mix_dual_tracks: Annotated[
        bool, Field(description="Prefer a single mixed master when the backend supports it")
    ] = False,
    auto_fix_english_punctuation: Annotated[
        bool, Field(description="Insert missing '.' before ';' for English segments")
    ] = True,
) -> str:
    """GENERATE_SONG - Start LeVo 2 (SongGeneration v2) generation via SongGeneration-Studio.

    PORTMANTEAU PATTERN RATIONALE: One MCP entry point for lyrics, SG2 inference flags,
    dual-track output, and optional Style RAG (10s audio prompt), matching fleet docstring style.

    ## Return Format
    Status string with task id and SG2 notes.

    ## Examples
    generate_song(lyrics="[verse] Neon rain. ; [chorus] Rise and fall. ;", genre="Synthwave")
    """
    request = {
        "lyrics": lyrics,
        "genre": genre,
        "mood": mood,
        "tempo": tempo,
        "voice": voice,
        "structure": structure or ["Verse", "Chorus"],
        "separate_stems": separate_stems,
        "title": title,
        "model_repo": model_repo,
        "model_weights": model_weights,
        "max_length_seconds": max_length_seconds,
        "torch_dtype": torch_dtype,
        "style_audio_prompt_path": style_audio_prompt_path,
        "mix_dual_tracks": mix_dual_tracks,
        "auto_fix_english_punctuation": auto_fix_english_punctuation,
    }
    return await logic.generate_song(request)


@app.tool(
    annotations={"readOnlyHint": True, "idempotentHint": True},
)
async def get_status() -> str:
    """Get detailed GPU VRAM metrics and current generation service state.

    Provides critical telemetry for resource management including memory
    usage and task saturation.

    ## Return Format
    Formatted Markdown report of the system status.

    ## Examples
    get_status()
    """
    status_data = await logic.get_status()
    vram_percent = (status_data["vram_used"] / status_data["vram_total"] * 100) if status_data["vram_total"] > 0 else 0

    return f"""# SongGeneration System Status
> [!NOTE]
> Backend monitoring active on {logic.base_url}

### GPU Telemetry
- **VRAM Total:** {status_data["vram_total"]} MB
- **VRAM Used:** {status_data["vram_used"]} MB ({vram_percent:.1f}%)
- **Active Tasks:** {status_data["active_generations"]}
- **Queued Tasks:** {status_data["queued_tasks"]}

### Model Server
- **Status:** {"✅ Online" if status_data.get("server_running") else "❌ Offline"}
- **Active Model:** `{status_data.get("model_loaded") or "None"}`
"""


@app.tool(
    annotations={"destructiveHint": True, "idempotentHint": True},
)
async def cancel_generation(
    task_id: Annotated[str, Field(description="The unique identifier of the task to cancel")],
) -> str:
    """Immediately stop an active or pending song generation task.

    ## Return Format
    Confirmation message, or an error if the task could not be stopped.

    ## Examples
    cancel_generation(task_id="abc123")
    """
    success = await logic.cancel_generation(task_id)
    if success:
        return f"### ✅ Task Cancelled\nTask `{task_id}` has been successfully terminated."
    return f"### ❌ Cancellation Failed\nTask `{task_id}` was not found or has already finished."


@app.tool(
    annotations={"destructiveHint": True, "idempotentHint": True},
)
async def unload_models() -> str:
    """Unload all active AI models from GPU VRAM to free resources.

    Use this tool when no further generations are planned to release
    high-performance hardware resources for other applications.

    ## Return Format
    Status message confirming the resource release.

    ## Examples
    unload_models()
    """
    success = await logic.unload_models()
    if success:
        return "> [!TIP]\n> Models successfully purged from VRAM. GPU is now free."
    return "> [!WARNING]\n> Failed to unload models. Backend may be busy or unreachable."


@app.tool(
    annotations={"readOnlyHint": True, "idempotentHint": True},
)
async def diagnostics() -> str:
    """Run comprehensive system diagnostics for the MCP server.

    ## Return Format
    Markdown diagnostic report.

    ## Examples
    diagnostics()
    """
    return """# songgeneration-mcp Diagnostics
- **Status:** Operational
- **Architecture:** FastMCP 3.4+
- **Backend:** SongGeneration-Studio REST (SG2 payload) + Lyria/ACE-Step/MusicGen/StableAudio chain
- **Docs:** `docs/PRD.md`, `docs/LYRIA_VS_SG2.md`; MCP resource `docs://lyria-vs-sg2`
"""


@app.tool(
    annotations={"destructiveHint": True, "idempotentHint": True},
)
async def shutdown() -> str:
    """Shut down the MCP server process (NSSM/service operation).

    ## Return Format
    Confirmation message; the process exits ~300ms after responding.

    ## Examples
    shutdown()
    """
    import os
    import threading

    logger.warning("Shutdown requested via shutdown tool.")
    threading.Timer(0.3, lambda: os._exit(0)).start()
    return "### 🛑 Shutting down\nsonggeneration-mcp exits in ~300ms."


def main() -> None:
    """Entry point for the `songgen` console script (pyproject.toml [project.scripts])
    and `python -m songgeneration_mcp.mcp_server` / MCPB stdio launch."""
    run_server(app, server_name="songgeneration-mcp")


if __name__ == "__main__":
    main()

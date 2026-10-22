"""Local Stable Audio 3 bridges.

Two processes, neither imported into this server:

1. ``audio-studio-mcp`` (https://github.com/kanaworksai-hue/audio-studio-mcp)
   streamable-HTTP MCP. NVIDIA PyTorch build of Stable Audio 3 medium.
   ``SONGGEN_AUDIO_STUDIO_URL`` (default ``http://127.0.0.1:8765/mcp``).
2. The CPU TFLite service in ``stable-audio-spike`` (small models).
   ``SONGGEN_SA3_URL`` (default ``http://127.0.0.1:11250``).
   ``POST /api/generate`` returns ``{success, file}``.

Set either URL to ``off`` to skip that process. A refused connection is a
skip, not a failure. Stable Audio 3 does not sing.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger("songgeneration-mcp.audio_studio")

_OFF = {"", "off", "0", "false", "none"}
_AUDIO_STUDIO_DEFAULT = "http://127.0.0.1:8765/mcp"
_SA3_DEFAULT = "http://127.0.0.1:11250"


def _enabled(url: str) -> bool:
    return url.strip().lower() not in _OFF


def prompt_from_generate_body(body: dict[str, Any]) -> str:
    """Text for the local chain. An explicit prompt wins. Otherwise genre, mood, and a short lyric line."""
    explicit = str(body.get("prompt") or "").strip()
    if explicit:
        return explicit
    genre = str(body.get("genre") or "").strip()
    mood = str(body.get("mood") or "").strip()
    lyrics = " ".join(str(body.get("lyrics") or "").split())[:180]
    return ", ".join(part for part in (genre, mood, lyrics) if part)


def audio_studio_url() -> str:
    """Configured audio-studio-mcp streamable-HTTP endpoint."""
    return os.getenv("SONGGEN_AUDIO_STUDIO_URL", _AUDIO_STUDIO_DEFAULT).strip()


def sa3_url() -> str:
    """Configured stable-audio-spike REST base URL."""
    return os.getenv("SONGGEN_SA3_URL", _SA3_DEFAULT).strip()


def studio_result_to_payload(data: dict[str, Any], prompt: str, duration: int) -> dict[str, object]:
    """Map an audio-studio ``generate_audio`` result onto our generate payload."""
    candidates = data.get("candidates") or []
    if not isinstance(candidates, list) or not candidates:
        return {"success": False, "error": "audio-studio returned no candidates", "backend": "audiostudio"}
    first = candidates[0] if isinstance(candidates[0], dict) else {}
    path = str(first.get("path") or "")
    if not path or not Path(path).is_file():
        return {
            "success": False,
            "error": f"audio-studio reported a file that is not on disk: {path}",
            "backend": "audiostudio",
        }
    model = str(data.get("model") or "stable-audio-3")
    return {
        "success": True,
        "file": path,
        "duration": data.get("seconds", duration),
        "prompt": prompt,
        "model": model,
        "backend": "audiostudio",
        "message": f"Instrumental from audio-studio-mcp ({model}): {path}",
    }


class Sa3Client:
    """HTTP client for the local Stable Audio 3 CPU service."""

    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url if base_url is not None else sa3_url()).rstrip("/")

    async def health(self) -> tuple[bool, dict[str, Any]]:
        """Reachability probe. Never raises. Second item is the JSON body or an error."""
        if not _enabled(self.base_url):
            return False, {"detail": "disabled"}
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(f"{self.base_url}/api/health")
            if response.status_code != 200:
                return False, {"detail": f"HTTP {response.status_code}"}
            body = response.json()
            return True, body if isinstance(body, dict) else {"detail": "non-object health"}
        except Exception as exc:
            logger.debug("SA3 health probe failed: %s", exc)
            return False, {"detail": str(exc) or type(exc).__name__}

    async def generate(self, prompt: str, duration: int) -> dict[str, object]:
        """Generate one instrumental. The service writes the WAV and returns its path."""
        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={"prompt": prompt, "duration": int(duration)},
                )
            response.raise_for_status()
            data = response.json()
        except Exception as exc:
            return {"success": False, "error": str(exc) or type(exc).__name__, "backend": "sa3"}
        if not isinstance(data, dict) or not data.get("success"):
            err = data.get("error") if isinstance(data, dict) else "non-object response"
            return {"success": False, "error": str(err or "sa3 generate failed"), "backend": "sa3"}
        path = str(data.get("file") or "")
        if not path or not Path(path).is_file():
            return {"success": False, "error": f"sa3 reported success but file missing: {path}", "backend": "sa3"}
        model = str(data.get("backend") or "stable-audio-3 sm-music")
        return {
            "success": True,
            "file": path,
            "duration": duration,
            "prompt": prompt,
            "model": model,
            "backend": "sa3",
            "cached": bool(data.get("cached")),
            "message": f"Instrumental from local Stable Audio 3 ({model}): {path}",
        }


async def audio_studio_reachable(url: str) -> bool:
    """True when the MCP HTTP endpoint accepts a connection. Never raises."""
    if not _enabled(url):
        return False
    try:
        async with httpx.AsyncClient(timeout=0.8) as client:
            response = await client.get(url)
        return response.status_code < 500
    except Exception as exc:
        logger.debug("audio-studio reachability probe failed: %s", exc)
        return False


def _tool_text(result: Any) -> str:
    parts: list[str] = []
    for block in getattr(result, "content", None) or []:
        text = getattr(block, "text", None)
        if isinstance(text, str) and text:
            parts.append(text)
    return "\n".join(parts)


async def generate_audio_studio(prompt: str, duration: int, url: str | None = None) -> dict[str, object]:
    """Call ``generate_audio`` on a running audio-studio-mcp HTTP server."""
    endpoint = (url if url is not None else audio_studio_url()).strip()
    if not _enabled(endpoint):
        return {"success": False, "error": "audio-studio disabled", "backend": "audiostudio"}
    try:
        from mcp import ClientSession
        from mcp.client.streamable_http import streamablehttp_client
    except ImportError as exc:
        return {"success": False, "error": f"mcp client missing: {exc}", "backend": "audiostudio"}

    seconds = float(max(1, min(int(duration), 380)))
    try:
        async with streamablehttp_client(endpoint, timeout=30, sse_read_timeout=300) as (read, write, _session_id):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "generate_audio",
                    {
                        "prompt": prompt,
                        "audio_type": "music",
                        "duration_seconds": seconds,
                        "variations": 1,
                        "original_idea": prompt,
                    },
                )
    except Exception as exc:
        return {"success": False, "error": str(exc) or type(exc).__name__, "backend": "audiostudio"}

    if getattr(result, "isError", False):
        return {"success": False, "error": _tool_text(result) or "audio-studio tool error", "backend": "audiostudio"}

    data = getattr(result, "structuredContent", None)
    if not isinstance(data, dict):
        raw = _tool_text(result)
        try:
            parsed = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            parsed = None
        data = parsed if isinstance(parsed, dict) else {}
    return studio_result_to_payload(data, prompt, duration)


async def try_stable_audio3(prompt: str, duration: int) -> tuple[dict[str, object] | None, dict[str, str]]:
    """Try audio-studio-mcp, then the CPU service. Skip either when it is down."""
    errors: dict[str, str] = {}

    studio = audio_studio_url()
    if _enabled(studio):
        if await audio_studio_reachable(studio):
            payload = await generate_audio_studio(prompt, duration, studio)
            if payload.get("success"):
                return payload, errors
            errors["audiostudio"] = str(payload.get("error") or "generate failed")
        else:
            logger.info("audio-studio skipped: nothing at %s", studio)

    sa3 = Sa3Client()
    if _enabled(sa3.base_url):
        ok, _detail = await sa3.health()
        if ok:
            payload = await sa3.generate(prompt, duration)
            if payload.get("success"):
                return payload, errors
            errors["sa3"] = str(payload.get("error") or "generate failed")
        else:
            logger.info("SA3 CPU service skipped: nothing at %s", sa3.base_url)

    return None, errors


async def audio_status() -> dict[str, object]:
    """Status for both local Stable Audio 3 processes. Does not generate."""
    studio = audio_studio_url()
    sa3 = Sa3Client()
    studio_up = await audio_studio_reachable(studio) if _enabled(studio) else False
    sa3_up, sa3_body = await sa3.health()
    return {
        "audiostudio": {
            "url": studio,
            "enabled": _enabled(studio),
            "reachable": studio_up,
            "note": "audio-studio-mcp streamable HTTP. NVIDIA Stable Audio 3 medium.",
        },
        "sa3": {
            "url": sa3.base_url,
            "enabled": _enabled(sa3.base_url),
            "reachable": sa3_up,
            "health": sa3_body,
            "note": "stable-audio-spike TFLite CPU service, small music and sfx models.",
        },
    }

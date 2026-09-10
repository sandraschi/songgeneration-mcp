"""ACE-Step 1.5 REST bridge - local open-weight music generation (MIT, ACE Studio + StepFun).

ACE-Step 1.5 runs as a standalone API server (``uv run acestep-api``, default port 8001,
see https://github.com/ACE-Step/ACE-Step-1.5). This module mirrors the SongGeneration-Studio
bridge pattern: HTTP client only, no heavy in-process dependencies. The API is async:
``/release_task`` queues a job, ``/query_result`` polls it, ``/v1/audio`` downloads the WAV.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import tempfile
import time
from pathlib import Path

import httpx

logger = logging.getLogger("songgeneration-mcp.acestep")

_DEFAULT_URL = "http://localhost:8001"
_DEFAULT_MODEL = "acestep-v15-turbo"
_POLL_INTERVAL_S = 2.0
_POLL_TIMEOUT_S = 600.0


class AcestepClient:
    """HTTP bridge to a local ACE-Step 1.5 API server."""

    def __init__(self, base_url: str | None = None) -> None:
        env_url = os.getenv("SONGGEN_ACESTEP_URL")
        self.base_url = (base_url or env_url or _DEFAULT_URL).rstrip("/")
        self.api_key = os.getenv("ACESTEP_API_KEY") or ""
        self._client: httpx.AsyncClient | None = None

    async def get_client(self) -> httpx.AsyncClient:
        """Get or create the httpx client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)
        return self._client

    async def close(self) -> None:
        """Close the httpx client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    def _headers(self) -> dict[str, str]:
        if not self.api_key:
            return {}
        return {"Authorization": f"Bearer {self.api_key}"}

    async def health(self) -> bool:
        """Reachability probe (never raises)."""
        try:
            client = await self.get_client()
            response = await client.get("/health", headers=self._headers())
            return response.status_code == 200
        except Exception as exc:
            logger.debug("ACE-Step health probe failed: %s", exc)
            return False

    async def list_models(self) -> list[str]:
        """List DiT models exposed by the server."""
        try:
            client = await self.get_client()
            response = await client.get("/v1/models", headers=self._headers())
            response.raise_for_status()
            data = response.json().get("data") or {}
            return [m["name"] for m in data.get("models", [])]
        except Exception as exc:
            logger.error("Failed to list ACE-Step models: %s", exc)
            return []

    async def generate(
        self,
        prompt: str,
        duration: int = 30,
        lyrics: str = "",
        model: str | None = None,
        thinking: bool = True,
        timeout_s: float = _POLL_TIMEOUT_S,
    ) -> dict:
        """Generate a full song: release_task → poll → download.

        ## Return Format
        {"success": bool, "file": str, "model": str, "duration": int, "error": str}

        ## Examples
        await client.generate("upbeat pop song", duration=30)
        await client.generate("soft ballad", duration=90, lyrics="[Verse 1]...", thinking=False)
        """
        audio_duration = max(10, min(int(duration), 600))
        payload: dict[str, object] = {
            "prompt": prompt,
            "audio_duration": audio_duration,
            "thinking": thinking,
            "batch_size": 1,
            "audio_format": "wav",
            "inference_steps": 8,
        }
        if lyrics:
            payload["lyrics"] = lyrics
        if model:
            payload["model"] = model

        client = await self.get_client()
        try:
            response = await client.post("/release_task", json=payload, headers=self._headers())
            response.raise_for_status()
            task_id = (response.json().get("data") or {}).get("task_id")
            if not task_id:
                return {"success": False, "error": "release_task returned no task_id"}
        except Exception as exc:
            return {"success": False, "error": f"release_task failed: {exc}"}

        result_url: str | None = None
        model_used = model or _DEFAULT_MODEL
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            await asyncio.sleep(_POLL_INTERVAL_S)
            try:
                query = await client.post("/query_result", json={"task_id_list": [task_id]}, headers=self._headers())
                query.raise_for_status()
                items = query.json().get("data") or []
                if not items:
                    continue
                entry = items[0]
                status = entry.get("status")
                if status == 1:
                    parsed = json.loads(entry.get("result") or "[]")
                    if isinstance(parsed, list) and parsed:
                        parsed = parsed[0]
                    if isinstance(parsed, dict):
                        result_url = parsed.get("file")
                        model_used = parsed.get("dit_model") or model_used
                    break
                if status == 2:
                    return {"success": False, "error": f"generation failed (task {task_id})"}
            except Exception as exc:
                logger.debug("query_result poll error: %s", exc)
                continue
        else:
            return {"success": False, "error": f"timeout waiting for task {task_id}"}

        if not result_url:
            return {"success": False, "error": "no audio file in task result"}

        out_dir = tempfile.mkdtemp(prefix="songgen-acestep-")
        out_path = os.path.join(out_dir, "acestep.wav")
        try:
            download = await client.get(result_url, headers=self._headers())
            download.raise_for_status()
            Path(out_path).write_bytes(download.content)
        except Exception as exc:
            return {"success": False, "error": f"audio download failed: {exc}"}

        return {"success": True, "file": out_path, "model": model_used, "duration": audio_duration}

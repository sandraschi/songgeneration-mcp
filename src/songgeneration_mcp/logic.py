import asyncio
import logging
import os
from typing import Any

import httpx

from .repository import extract_audio_urls
from .sg2 import normalize_sg2_english_before_semicolons

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("songgeneration-mcp.logic")

_DEFAULT_STUDIO = "http://localhost:10930"
_DEFAULT_MODEL_REPO = "tencent/SongGeneration"
_DEFAULT_WEIGHTS = "v2-large"
_DEFAULT_MAX_LENGTH_S = 270
_DEFAULT_DTYPE = "bfloat16"
_DEFAULT_GENERATE_TIMEOUT_S = 600.0
_DEFAULT_STUDIO_POLL_INTERVAL_S = 2.0


class SongGenerationLogic:
    """HTTP bridge to SongGeneration-Studio with SG2 (LeVo 2) inference hints."""

    def __init__(self, base_url: str | None = None) -> None:
        env_url = os.getenv("SONGGENERATION_STUDIO_URL") or os.getenv("SONGGEN_STUDIO_BASE_URL")
        self.base_url = (base_url or env_url or _DEFAULT_STUDIO).rstrip("/")
        self.api_url = f"{self.base_url}/api"
        self._client: httpx.AsyncClient | None = None

    async def get_client(self) -> httpx.AsyncClient:
        """Get or create the httpx client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(base_url=self.api_url, timeout=30.0)
        return self._client

    async def close(self) -> None:
        """Close the httpx client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def list_models(self) -> list[str]:
        """List all available models from the backend."""
        try:
            client = await self.get_client()
            response = await client.get("/models")
            response.raise_for_status()
            data = response.json()
            return [m["id"] for m in data.get("models", [])]
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []

    async def get_status(self) -> dict[str, Any]:
        """Get GPU and model server status from the backend."""
        try:
            client = await self.get_client()

            gpu_resp = await client.get("/gpu")
            gpu_resp.raise_for_status()
            gpu_data = gpu_resp.json()

            server_resp = await client.get("/model-server/status")
            server_resp.raise_for_status()
            state_data = server_resp.json()

            return {
                "vram_total": gpu_data.get("total", 0),
                "vram_used": gpu_data.get("used", 0),
                "active_generations": state_data.get("active_count", 0),
                "queued_tasks": state_data.get("queued_count", 0),
                "server_running": state_data.get("running", False),
                "model_loaded": state_data.get("model_id") if state_data.get("loaded") else None,
            }
        except Exception as e:
            logger.error(f"Failed to get status: {e}")
            return {
                "vram_total": 0,
                "vram_used": 0,
                "active_generations": 0,
                "queued_tasks": 0,
                "error": str(e),
            }

    def _build_studio_request(self, request_data: dict[str, Any]) -> dict[str, Any]:
        """Map MCP args + SG2 defaults to the Studio JSON body (forward-compatible)."""
        auto_fix = bool(request_data.get("auto_fix_english_punctuation", True))
        raw_lyrics = request_data.get("lyrics") or ""
        lyrics_norm, punct_notes = normalize_sg2_english_before_semicolons(
            raw_lyrics, auto_fix=auto_fix
        )

        separate = bool(request_data.get("separate_stems", True))
        mix_dual = bool(request_data.get("mix_dual_tracks", False))

        model_repo = (
            request_data.get("model_repo") or os.getenv("SONGGEN_MODEL_REPO") or _DEFAULT_MODEL_REPO
        )
        weights = (
            request_data.get("model_weights")
            or os.getenv("SONGGEN_MODEL_WEIGHTS")
            or _DEFAULT_WEIGHTS
        )
        max_length_seconds = int(
            request_data.get("max_length_seconds")
            or os.getenv("SONGGEN_MAX_LENGTH_SECONDS")
            or _DEFAULT_MAX_LENGTH_S
        )
        torch_dtype = (
            request_data.get("torch_dtype") or os.getenv("SONGGEN_TORCH_DTYPE") or _DEFAULT_DTYPE
        )

        style_path = request_data.get("style_audio_prompt_path")

        studio_request: dict[str, Any] = {
            "title": request_data.get("title") or f"MCP-Gen-{request_data.get('genre', 'Song')}",
            "sections": [{"type": "verse", "lyrics": lyrics_norm}],
            "gender": str(request_data.get("voice", "female")).lower(),
            "genre": request_data.get("genre", ""),
            "emotion": request_data.get("mood", ""),
            "bpm": request_data.get("tempo", 120),
            "output_mode": "separate" if separate and not mix_dual else "mixed",
            "custom_style": request_data.get("mood", ""),
            "sg2": {
                "model_repo": model_repo,
                "weights": weights,
                "max_length_seconds": max_length_seconds,
                "torch_dtype": torch_dtype,
                "codec": {
                    "sample_rate_hz": 48000,
                    "channels": 2,
                    "dual_track_tokens": True,
                },
                "output": {
                    "dual_tracks": separate,
                    "vocal_wav": "vocal.wav",
                    "instrumental_wav": "inst.wav",
                    "mix_down": mix_dual,
                },
                "style_rag": (
                    {
                        "audio_prompt_path": style_path,
                        "max_prompt_duration_seconds": 10,
                    }
                    if style_path
                    else None
                ),
            },
        }
        if punct_notes:
            studio_request["_mcp_punctuation_notes"] = punct_notes
        return studio_request

    async def _post_generate(
        self, request_data: dict[str, Any]
    ) -> tuple[dict[str, Any], list[str] | None, dict[str, Any]]:
        """POST /generate to Studio.

        Returns (response_json, punctuation_notes, studio_request_copy).
        """
        client = await self.get_client()
        studio_request = self._build_studio_request(request_data)
        punct_notes = studio_request.pop("_mcp_punctuation_notes", None)
        timeout = float(os.getenv("SONGGEN_GENERATE_TIMEOUT_S") or _DEFAULT_GENERATE_TIMEOUT_S)
        response = await client.post("/generate", json=studio_request, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        return data, punct_notes, studio_request

    async def _poll_studio_generation_until_terminal(self, gen_id: str) -> tuple[dict[str, Any], bool]:
        """Poll ``GET /generation/{gen_id}`` until completed / failed / stopped or timeout.

        Returns ``(last_json, timed_out)``.
        """
        interval = float(os.getenv("SONGGEN_STUDIO_POLL_INTERVAL_S") or _DEFAULT_STUDIO_POLL_INTERVAL_S)
        max_wait = float(
            os.getenv("SONGGEN_STUDIO_POLL_MAX_WAIT_S")
            or os.getenv("SONGGEN_GENERATE_TIMEOUT_S")
            or _DEFAULT_GENERATE_TIMEOUT_S
        )
        loop = asyncio.get_event_loop()
        deadline = loop.time() + max_wait
        client = await self.get_client()
        last: dict[str, Any] = {}
        while loop.time() < deadline:
            try:
                response = await client.get(f"/generation/{gen_id}", timeout=30.0)
                response.raise_for_status()
                last = response.json()
            except Exception as e:
                logger.warning("Studio poll failed for %s: %s", gen_id, e)
                await asyncio.sleep(interval)
                continue
            st = str(last.get("status") or "")
            if st in ("completed", "failed", "stopped"):
                return last, False
            await asyncio.sleep(interval)
        return last, True

    async def generate_song_result(self, request_data: dict[str, Any]) -> dict[str, Any]:
        """Structured result for HTTP API (same payload as MCP ``generate_song``)."""
        try:
            data, punct_notes, studio_request = await self._post_generate(request_data)
            gen_id = data.get("generation_id")
            merged: dict[str, Any] = dict(data) if isinstance(data, dict) else {}
            timed_out = False

            if gen_id and not extract_audio_urls(merged):
                polled, timed_out = await self._poll_studio_generation_until_terminal(str(gen_id))
                merged = {**merged, **polled}

            if timed_out:
                return {
                    "success": False,
                    "error": f"Timed out waiting for Studio generation {gen_id} to finish",
                    "studio_response": merged,
                    "punctuation_notes": punct_notes or [],
                }

            st = str(merged.get("status") or "")
            if gen_id and st == "failed":
                return {
                    "success": False,
                    "error": str(merged.get("message") or "Studio reported generation failed"),
                    "studio_response": merged,
                    "punctuation_notes": punct_notes or [],
                }
            if gen_id and st == "stopped":
                return {
                    "success": False,
                    "error": str(merged.get("message") or "Studio generation was stopped"),
                    "studio_response": merged,
                    "punctuation_notes": punct_notes or [],
                }

            resolved = extract_audio_urls(merged, studio_base_url=self.base_url)
            if gen_id and not resolved:
                return {
                    "success": False,
                    "error": "Studio response had no downloadable audio URLs after generation finished",
                    "studio_response": merged,
                    "punctuation_notes": punct_notes or [],
                }

            if gen_id:
                msg = f"Generation finished. Task ID: {gen_id}. Audio ready. Studio: {self.base_url}"
            else:
                msg = "Generation request accepted."
            if studio_request.get("sg2", {}).get("output", {}).get("dual_tracks"):
                msg += (
                    " SG2 dual-track: expect vocal.wav and inst.wav (48 kHz); "
                    "set mix_dual_tracks=true for a single mixed render if the backend supports it."
                )
            out: dict[str, Any] = {
                "success": True,
                "generation_id": gen_id,
                "message": msg,
                "studio_response": merged,
                "punctuation_notes": punct_notes or [],
            }
            return out
        except Exception as e:
            logger.exception("generate_song_result failed")
            return {"success": False, "error": str(e)}

    async def generate_song(self, request_data: dict[str, Any]) -> str:
        """Submit a song generation request (LeVo 2 / SG2-aware). MCP string return."""
        res = await self.generate_song_result(request_data)
        if res.get("success"):
            msg = str(res.get("message", ""))
            notes = res.get("punctuation_notes") or []
            if notes:
                msg += "\n\nNotes:\n- " + "\n- ".join(notes)
            return msg
        return f"Error: Failed to start generation - {res.get('error', 'unknown')}"

    async def cancel_generation(self, task_id: str) -> bool:
        """Cancel a pending generation task."""
        try:
            client = await self.get_client()
            response = await client.post(f"/stop/{task_id}")
            if response.status_code == 200:
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to cancel generation {task_id}: {e}")
            return False

    async def unload_models(self) -> bool:
        """Unload models from GPU VRAM."""
        try:
            client = await self.get_client()
            response = await client.post("/model-server/unload")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to unload models: {e}")
            return False

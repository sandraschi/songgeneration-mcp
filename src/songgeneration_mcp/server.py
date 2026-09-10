"""ASGI app for uvicorn (web_sota backend on fleet port 10885).

Exposes MCP streamable HTTP at ``/mcp``, JSON helpers for logs/health, and REST
for the web UI: generate, Studio status, song repository.
"""

from __future__ import annotations

import asyncio
import logging
import mimetypes
import os
import shutil
from pathlib import Path

import httpx
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse
from starlette.routing import Mount, Route

from songgeneration_mcp.log_buffer import clear_buffer, get_recent_lines, setup_process_log_buffer
from songgeneration_mcp.logic import SongGenerationLogic
from songgeneration_mcp.mcp_server import app as mcp
from songgeneration_mcp.mp3 import download_audio_urls_to_local, transcode_audio_urls_to_mp3
from songgeneration_mcp.plex_export import export_all_with_mp3, export_repo_entry
from songgeneration_mcp.reaper_export import export_repo_entry_to_reaper
from songgeneration_mcp.repository import (
    add_generation_entry,
    get_entry,
    list_entries,
    media_dir,
    update_entry,
)
from songgeneration_mcp.settings_store import load_settings, save_settings
from songgeneration_mcp.studio_boot import ensure_studio_available
from songgeneration_mcp.virtualdj_export import export_repo_entry_to_virtualdj

setup_process_log_buffer()

_boot_settings = load_settings()
_logic = SongGenerationLogic(base_url=_boot_settings.get("studio_url"))

# MCP streamable HTTP (fleet dashboard expects ``/mcp``; see transport.ENV_PATH)
_mcp_http = mcp.http_app(path="/mcp", transport="streamable-http")


async def api_health(_request: Request) -> JSONResponse:
    return JSONResponse(
        {
            "ok": True,
            "service": "songgeneration-mcp",
            "version": "0.1.0",
            "mcp_path": "/mcp",
        }
    )


async def api_logs_get(request: Request) -> JSONResponse:
    raw = request.query_params.get("limit", "300")
    try:
        limit = int(raw)
    except ValueError:
        limit = 300
    limit = min(max(limit, 1), 5000)
    lines = get_recent_lines(limit)
    return JSONResponse({"lines": lines, "count": len(lines)})


async def api_logs_clear(_request: Request) -> JSONResponse:
    removed = clear_buffer()
    logging.getLogger(__name__).warning("Log buffer cleared by operator (%s entries removed).", removed)
    return JSONResponse({"cleared": removed})


async def api_studio_status(_request: Request) -> JSONResponse:
    settings = load_settings()
    await ensure_studio_available(_logic.base_url, studio_dir=settings.get("studio_dir"))
    data = await _logic.get_status()
    return JSONResponse(data)


async def api_studio_test(_request: Request) -> JSONResponse:
    """Deep connectivity test: checks Studio process, HTTP reachability, GPU, and model-server."""
    import os
    from pathlib import Path as _Path

    settings = load_settings()
    studio_url = _logic.base_url
    studio_dir = settings.get("studio_dir") or os.getenv("SONGGEN_STUDIO_DIR", "")

    checks: list[dict] = []

    # 1. Directory exists and has main.py
    dir_ok = False
    if studio_dir:
        main_py = _Path(studio_dir) / "main.py"
        dir_ok = main_py.is_file()
    checks.append(
        {
            "name": "studio_dir",
            "ok": dir_ok,
            "detail": studio_dir if studio_dir else "not configured",
        }
    )

    # 2. HTTP reachable - /api/health
    import httpx as _httpx

    health_ok = False
    health_detail = ""
    try:
        async with _httpx.AsyncClient(timeout=4.0) as c:
            r = await c.get(f"{studio_url}/api/health")
            health_ok = r.status_code == 200
            health_detail = f"HTTP {r.status_code}"
    except Exception as exc:
        health_detail = str(exc)
    checks.append({"name": "http_reachable", "ok": health_ok, "detail": health_detail})

    # 3. GPU info
    gpu_ok = False
    gpu_detail = ""
    if health_ok:
        try:
            async with _httpx.AsyncClient(timeout=4.0) as c:
                r = await c.get(f"{studio_url}/api/gpu")
                if r.status_code == 200:
                    gd = r.json()
                    gpu_ok = gd.get("available", False)
                    if gpu_ok:
                        g = gd.get("gpu", {})
                        gpu_detail = (
                            f"{g.get('name', '?')} - "
                            f"{g.get('free_gb', '?')} GB free / {g.get('total_gb', '?')} GB total"
                        )
                    else:
                        gpu_detail = gd.get("error") or "GPU not available"
        except Exception as exc:
            gpu_detail = str(exc)
    checks.append({"name": "gpu", "ok": gpu_ok, "detail": gpu_detail})

    # 4. Model server process
    ms_ok = False
    ms_detail = ""
    if health_ok:
        try:
            async with _httpx.AsyncClient(timeout=4.0) as c:
                r = await c.get(f"{studio_url}/api/model-server/status")
                if r.status_code == 200:
                    ms = r.json()
                    ms_ok = ms.get("running", False)
                    if ms_ok:
                        loaded = ms.get("model_id") if ms.get("loaded") else None
                        ms_detail = f"running - model: {loaded or 'none loaded'}"
                    else:
                        ms_detail = ms.get("error") or "not running"
        except Exception as exc:
            ms_detail = str(exc)
    checks.append({"name": "model_server", "ok": ms_ok, "detail": ms_detail})

    # 5. At least one model ready
    model_ok = False
    model_detail = ""
    if health_ok:
        try:
            async with _httpx.AsyncClient(timeout=4.0) as c:
                r = await c.get(f"{studio_url}/api/models")
                if r.status_code == 200:
                    md = r.json()
                    ready = [m["id"] for m in md.get("models", []) if m.get("status") == "ready"]
                    model_ok = len(ready) > 0
                    model_detail = ", ".join(ready) if ready else "no models downloaded"
        except Exception as exc:
            model_detail = str(exc)
    checks.append({"name": "models_ready", "ok": model_ok, "detail": model_detail})

    overall = all(c["ok"] for c in checks)
    return JSONResponse(
        {
            "ok": overall,
            "studio_url": studio_url,
            "checks": checks,
        }
    )


async def api_studio_info(_request: Request) -> JSONResponse:
    settings = load_settings()
    reachable = await ensure_studio_available(_logic.base_url, studio_dir=settings.get("studio_dir"))
    status = await _logic.get_status()
    return JSONResponse(
        {
            "studio_url": _logic.base_url,
            "ui_url": _logic.base_url,
            "reachable": reachable and "error" not in status,
            "status_error": status.get("error"),
        }
    )


def _check_lyria_adc() -> tuple[bool, str, str | None]:
    """Blocking check: do valid Application Default Credentials exist?

    Runs a real token refresh (free -- no Vertex AI call) so an expired or
    revoked ADC shows up as not-ready, not just "a file exists somewhere".

    Fast-paths the common "nothing configured yet" case: with no ADC file and
    no GOOGLE_APPLICATION_CREDENTIALS, google.auth.default() still falls
    through to probing the GCE metadata server, which takes ~10s+ to time out
    on a non-cloud machine. Skip straight to "not found" instead of making
    every Settings-page load (and every Recheck click) eat that wait.
    """
    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        try:
            from google.auth import _cloud_sdk

            if not os.path.isfile(_cloud_sdk.get_application_default_credentials_path()):
                return False, "no Application Default Credentials file found", None
        except Exception:
            pass  # internal helper unavailable/changed -- fall through to the real check
    try:
        import google.auth
        from google.auth.transport.requests import Request as _GoogleAuthRequest

        creds, adc_project = google.auth.default()
        creds.refresh(_GoogleAuthRequest())
        return True, f"valid ({type(creds).__name__})", adc_project
    except Exception as e:
        return False, str(e) or type(e).__name__, None


async def api_lyria_status(_request: Request) -> JSONResponse:
    """Onboarding-wizard status: what's configured, what's missing, why."""
    settings = load_settings()
    project = settings.get("google_cloud_project") or os.environ.get("GOOGLE_CLOUD_PROJECT")
    lyria_model = settings.get("lyria_model") or os.environ.get("SONGGEN_LYRIA_MODEL") or "lyria-002"
    gcloud_installed = shutil.which("gcloud") is not None
    adc_found, adc_detail, adc_project = await asyncio.to_thread(_check_lyria_adc)
    return JSONResponse(
        {
            "gcloud_installed": gcloud_installed,
            "project": project,
            "project_configured": bool(project),
            "adc_found": adc_found,
            "adc_detail": adc_detail,
            "adc_project": adc_project,
            "lyria_model": lyria_model,
            "ready": bool(project) and adc_found,
        }
    )


def _check_hf_token(token: str | None) -> tuple[bool, str]:
    """Blocking check: does this Hugging Face token authenticate, and can it
    reach the gated Stable Audio Open repo? Both are free API calls."""
    if not token:
        return False, "no token configured"
    try:
        from huggingface_hub import HfApi

        api = HfApi(token=token)
        who = api.whoami()
        try:
            api.model_info("stabilityai/stable-audio-open-1.0", token=token)
        except Exception as e:
            return False, f"token valid ({who.get('name', '?')}) but no access to stable-audio-open-1.0: {e}"
        return True, f"valid ({who.get('name', '?')}), gated model access confirmed"
    except Exception as e:
        return False, str(e) or type(e).__name__


async def api_huggingface_status(_request: Request) -> JSONResponse:
    """Onboarding-wizard status for the Stable Audio Open gated model."""
    settings = load_settings()
    token = settings.get("hf_token") or os.environ.get("HF_TOKEN")
    token_configured = bool(token)
    ok, detail = await asyncio.to_thread(_check_hf_token, token)
    return JSONResponse(
        {
            "token_configured": token_configured,
            "token_valid": ok,
            "detail": detail,
            "ready": ok,
        }
    )


def _run_lyria_sync(prompt: str, duration: int, project: str, lyria_model: str) -> dict[str, object]:
    """Blocking: one Vertex AI Lyria call. Raises on any failure."""
    from google import genai
    from google.genai import types as _genai_types

    client = genai.Client(vertexai=True, project=project, location="global")
    import tempfile

    # GenerateContentConfig has no `output_audio_format` field (verified against the
    # installed google-genai SDK); audio output is requested via response_modalities.
    response = client.models.generate_content(
        model=lyria_model,
        contents=prompt,
        config=_genai_types.GenerateContentConfig(audio_timestamp=True, response_modalities=["AUDIO"]),
    )
    audio_blob = None
    if response.candidates and response.candidates[0].content:
        for part in response.candidates[0].content.parts or []:
            if part.inline_data and part.inline_data.data:
                audio_blob = part.inline_data
                break
    if audio_blob is None:
        raise ValueError("no audio part in response")
    ext = mimetypes.guess_extension((audio_blob.mime_type or "").split(";")[0].strip()) or ".wav"
    out_dir = tempfile.mkdtemp()
    out_path = os.path.join(out_dir, f"lyria{ext}")
    with open(out_path, "wb") as f:
        f.write(audio_blob.data)
    return {
        "success": True,
        "file": out_path,
        "duration": duration,
        "prompt": prompt,
        "model": lyria_model,
        "backend": "lyria",
    }


def _run_musicgen_sync(prompt: str, duration: int) -> dict[str, object]:
    """Blocking: local MusicGen inference (first call downloads ~2GB). Raises on failure."""
    import tempfile

    import scipy.io.wavfile
    import torch
    from transformers import AutoProcessor, MusicgenForConditionalGeneration

    processor = AutoProcessor.from_pretrained("facebook/musicgen-small")
    model = MusicgenForConditionalGeneration.from_pretrained("facebook/musicgen-small")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = model.to(device)
    inputs = processor(text=[prompt], padding=True, return_tensors="pt").to(device)
    audio_values = model.generate(**inputs, do_sample=True, guidance_scale=3.0, max_new_tokens=duration * 50)
    out_dir = tempfile.mkdtemp()
    out_path = os.path.join(out_dir, "generated.wav")
    sampling_rate = model.config.audio_encoder.sampling_rate
    scipy.io.wavfile.write(out_path, rate=sampling_rate, data=audio_values[0, 0].cpu().numpy())
    return {
        "success": True,
        "file": out_path,
        "duration": duration,
        "prompt": prompt,
        "model": "musicgen-small",
        "backend": "musicgen",
    }


def _run_stableaudio_sync(prompt: str, duration: int, hf_token: str | None) -> dict[str, object]:
    """Blocking: local Stable Audio Open inference (first load ~3GB, gated model). Raises on failure."""
    import tempfile

    import soundfile as sf
    import torch
    from diffusers import StableAudioPipeline

    pipe = StableAudioPipeline.from_pretrained(
        "stabilityai/stable-audio-open-1.0", dtype=torch.float16, variant="fp16", token=hf_token
    ).to("cuda")
    generator = torch.Generator("cuda").manual_seed(0)
    audio = pipe(
        prompt,
        negative_prompt="Low quality.",
        num_inference_steps=100,
        audio_end_in_s=min(duration, 47),
        num_waveforms_per_prompt=1,
        generator=generator,
    ).audios
    out_dir = tempfile.mkdtemp()
    out_path = os.path.join(out_dir, "stableaudio.wav")
    output = audio[0].T.float().cpu().numpy()
    sf.write(out_path, output, pipe.vae.sampling_rate)
    return {
        "success": True,
        "file": out_path,
        "duration": min(duration, 47),
        "prompt": prompt,
        "model": "stable-audio-open-1.0",
        "backend": "stableaudio",
    }


async def _try_local_backends(prompt: str, duration: int) -> tuple[dict[str, object] | None, dict[str, str]]:
    """Quick-chain: Lyria -> MusicGen -> Stable Audio Open.

    Each backend's actual model/API call is synchronous and can run for
    minutes (first-run downloads, GPU inference) -- every one runs via
    ``asyncio.to_thread`` so it can't freeze the server's single event loop
    and take the rest of the dashboard down with it.

    Returns ``(payload, errors)``: the success payload
    (``success/file/duration/prompt/model/backend``) or ``None`` when every
    backend failed, plus per-backend error strings for setup diagnostics.
    """
    log = logging.getLogger(__name__)
    errors: dict[str, str] = {}

    # Backend 1: Lyria (Google Vertex AI, needs GCP project + ADC credentials)
    project = load_settings().get("google_cloud_project") or os.environ.get("GOOGLE_CLOUD_PROJECT")
    lyria_model = (
        str(load_settings().get("lyria_model") or "").strip()
        or os.environ.get("SONGGEN_LYRIA_MODEL", "").strip()
        or "lyria-002"
    )
    if not project:
        log.info(
            "Lyria skipped: no Google Cloud project configured (Settings > Lyria, or GOOGLE_CLOUD_PROJECT env var)."
        )
    else:
        try:
            payload = await asyncio.to_thread(_run_lyria_sync, prompt, duration, project, lyria_model)
            return payload, errors
        except Exception as e:
            errors["lyria"] = str(e) or type(e).__name__
            log.exception("Lyria generation failed; falling back to next backend.")

    # Backend 2: MusicGen (local HuggingFace model, first call downloads ~2GB)
    try:
        payload = await asyncio.to_thread(_run_musicgen_sync, prompt, duration)
        return payload, errors
    except Exception as e:
        errors["musicgen"] = str(e) or type(e).__name__

    # Backend 3: Stable Audio Open (HuggingFace diffusers, local, first load ~3GB, gated model)
    hf_token = load_settings().get("hf_token") or os.environ.get("HF_TOKEN") or None
    try:
        payload = await asyncio.to_thread(_run_stableaudio_sync, prompt, duration, hf_token)
        return payload, errors
    except Exception as e:
        errors["stableaudio"] = str(e) or type(e).__name__

    return None, errors


async def api_generate_post(request: Request) -> JSONResponse:
    try:
        body = await request.json()
    except Exception as e:
        return JSONResponse({"success": False, "error": f"invalid json: {e}"}, status_code=400)
    if not isinstance(body, dict):
        return JSONResponse({"success": False, "error": "body must be an object"}, status_code=400)
    prompt = str(body.get("prompt", body.get("genre", "")))
    try:
        duration = int(body.get("duration", body.get("max_length_seconds", 30)))
    except (TypeError, ValueError):
        duration = 30

    hit, _local_errors = await _try_local_backends(prompt, duration)
    if hit is not None:
        return JSONResponse(hit)

    settings = load_settings()
    await ensure_studio_available(_logic.base_url, studio_dir=settings.get("studio_dir"))
    result = await _logic.generate_song_result(body)
    if result.get("success"):
        transcode_to_mp3 = bool(body.get("transcode_to_mp3", False))
        entry = add_generation_entry(
            generation_id=result.get("generation_id"),
            title=str(body.get("title") or body.get("genre") or "Untitled"),
            genre=str(body.get("genre", "")),
            mood=str(body.get("mood", "")),
            message=str(result.get("message", "")),
            studio_response=result.get("studio_response") or {},
            punctuation_notes=list(result.get("punctuation_notes") or []),
            studio_base_url=_logic.base_url,
        )
        result["repo_id"] = entry["repo_id"]
        source_audio_urls = list(entry.get("audio_urls", []))
        source_stem_urls = dict(entry.get("stem_urls") or {})
        local_audio_urls = await download_audio_urls_to_local(source_audio_urls, entry["repo_id"])
        if local_audio_urls:
            source_to_local = dict(zip(source_audio_urls, local_audio_urls, strict=False))
            local_stem_urls: dict[str, list[str]] = {}
            for role in ("vocal", "instrumental", "mix"):
                role_urls = list(source_stem_urls.get(role) or [])
                local_stem_urls[role] = [source_to_local.get(u, u) for u in role_urls]
            result["audio_urls"] = local_audio_urls
            result["source_audio_urls"] = source_audio_urls
            result["stem_urls"] = local_stem_urls
            result["source_stem_urls"] = source_stem_urls
            update_entry(
                entry["repo_id"],
                {
                    "audio_urls": local_audio_urls,
                    "source_audio_urls": source_audio_urls,
                    "stem_urls": local_stem_urls,
                    "source_stem_urls": source_stem_urls,
                },
            )
        else:
            result["audio_urls"] = source_audio_urls
            result["stem_urls"] = source_stem_urls
        result["mp3_urls"] = []
        result["mp3_stem_urls"] = {"vocal": [], "instrumental": [], "mix": []}
        if transcode_to_mp3 and result["audio_urls"]:
            mp3_urls = await transcode_audio_urls_to_mp3(result["audio_urls"], entry["repo_id"])
            if mp3_urls:
                result["mp3_urls"] = mp3_urls
                mp3_stem_urls: dict[str, list[str]] = {"vocal": [], "instrumental": [], "mix": []}
                for role in ("vocal", "instrumental", "mix"):
                    role_urls = list(result.get("stem_urls", {}).get(role) or [])
                    if not role_urls:
                        continue
                    role_mp3 = await transcode_audio_urls_to_mp3(role_urls, f"{entry['repo_id']}-{role}")
                    mp3_stem_urls[role] = role_mp3
                result["mp3_stem_urls"] = mp3_stem_urls
                update_entry(entry["repo_id"], {"mp3_urls": mp3_urls, "mp3_stem_urls": mp3_stem_urls})
    return JSONResponse(result)


async def api_v1_generate_post(request: Request) -> JSONResponse:
    """Quick Generate: ``{prompt, duration, lyrics?, model?}``.

    Same local-backend chain as ``/api/generate`` (Lyria -> MusicGen ->
    Stable Audio), then Studio SG2 as a last resort. Always returns JSON shaped
    for the Quick page: ``{success, file, backend, model, ...}``.
    """
    try:
        body = await request.json()
    except Exception as e:
        return JSONResponse({"success": False, "error": f"invalid json: {e}"}, status_code=400)
    if not isinstance(body, dict):
        return JSONResponse({"success": False, "error": "body must be an object"}, status_code=400)
    prompt = str(body.get("prompt", "") or "")
    lyrics = str(body.get("lyrics", "") or "")
    text = prompt.strip() or lyrics.strip()
    if not text:
        return JSONResponse({"success": False, "error": "prompt (or lyrics) is required"}, status_code=400)
    try:
        duration = int(body.get("duration", 30))
    except (TypeError, ValueError):
        duration = 30
    duration = max(5, min(duration, 600))

    hit, local_errors = await _try_local_backends(text, duration)
    if hit is not None:
        return JSONResponse(hit)

    # Last resort: Studio SG2 (async task, no immediate file).
    settings = load_settings()
    await ensure_studio_available(_logic.base_url, studio_dir=settings.get("studio_dir"))
    studio_body: dict[str, object] = {
        "lyrics": lyrics or text,
        "genre": "",
        "mood": "",
        "title": (prompt[:80] or "Quick Generate"),
        "max_length_seconds": min(duration, 270),
    }
    result = await _logic.generate_song_result(studio_body)
    if result.get("success"):
        return JSONResponse(
            {
                "success": True,
                "file": "",
                "duration": duration,
                "prompt": text,
                "backend": "studio",
                "model": "tencent/SongGeneration::v2-large",
                "generation_id": result.get("generation_id"),
                "message": result.get("message"),
            }
        )
    local_errors["studio"] = str(result.get("error", "studio generation failed"))
    return JSONResponse(
        {
            "success": False,
            "error": result.get("error", "studio generation failed"),
            "backend": "studio",
            "backend_errors": local_errors,
            "hint": (
                "No generation backend available. Configure one: Lyria project in Settings, "
                "local MusicGen / Stable Audio deps, or Studio on :10930."
            ),
        }
    )


async def api_llm_providers(_request: Request) -> JSONResponse:
    """Live model lists from local Ollama + LM Studio.

    Short timeouts, never raises: an unreachable provider yields an empty
    list so the Settings UI shows an honest empty state instead of fakes.
    """
    ollama_base = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
    lmstudio_base = os.getenv("LMSTUDIO_BASE_URL", "http://127.0.0.1:1234").rstrip("/")
    ollama_models: list[dict[str, str]] = []
    lmstudio_models: list[dict[str, str]] = []
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(f"{ollama_base}/api/tags")
            if r.status_code == 200:
                data = r.json()
                ollama_models = [
                    {"name": str(m.get("name", ""))} for m in data.get("models", []) if m.get("name")
                ]
    except Exception:
        pass
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(f"{lmstudio_base}/v1/models")
            if r.status_code == 200:
                data = r.json()
                lmstudio_models = [
                    {"name": str(m.get("id", ""))} for m in data.get("data", []) if m.get("id")
                ]
    except Exception:
        pass
    return JSONResponse({"ollama": ollama_models, "lm_studio": lmstudio_models})


async def api_songs_list(_request: Request) -> JSONResponse:
    return JSONResponse({"entries": list_entries(limit=200)})


async def api_song_get(request: Request) -> JSONResponse:
    repo_id = request.path_params.get("repo_id", "")
    row = get_entry(repo_id)
    if row is None:
        return JSONResponse({"error": "not found"}, status_code=404)
    return JSONResponse(row)


def _redact_settings(data: dict[str, object]) -> dict[str, object]:
    """Never echo the raw HF token back over HTTP — only whether one is set."""
    out = dict(data)
    out["hf_token_configured"] = bool(out.get("hf_token"))
    out.pop("hf_token", None)
    return out


async def api_settings_get(_request: Request) -> JSONResponse:
    return JSONResponse(_redact_settings(load_settings()))


async def api_settings_post(request: Request) -> JSONResponse:
    global _logic
    try:
        body = await request.json()
    except Exception as e:
        return JSONResponse({"error": f"invalid json: {e}"}, status_code=400)
    if not isinstance(body, dict):
        return JSONResponse({"error": "body must be an object"}, status_code=400)
    patch: dict[str, object] = {}
    if "plex_export_dir" in body:
        v = body.get("plex_export_dir")
        if v is None or v == "":
            patch["plex_export_dir"] = None
        elif isinstance(v, str):
            patch["plex_export_dir"] = v.strip() or None
        else:
            return JSONResponse(
                {"error": "plex_export_dir must be a string or null"},
                status_code=400,
            )
    if "studio_url" in body:
        v = body.get("studio_url")
        if v is None or v == "":
            patch["studio_url"] = None
        elif isinstance(v, str):
            patch["studio_url"] = v.strip().rstrip("/") or None
        else:
            return JSONResponse(
                {"error": "studio_url must be a string or null"},
                status_code=400,
            )
    if "studio_dir" in body:
        v = body.get("studio_dir")
        if v is None or v == "":
            patch["studio_dir"] = None
        elif isinstance(v, str):
            patch["studio_dir"] = v.strip() or None
        else:
            return JSONResponse(
                {"error": "studio_dir must be a string or null"},
                status_code=400,
            )
    if "virtualdj_drop_dir" in body:
        v = body.get("virtualdj_drop_dir")
        if v is None or v == "":
            patch["virtualdj_drop_dir"] = None
        elif isinstance(v, str):
            patch["virtualdj_drop_dir"] = v.strip() or None
        else:
            return JSONResponse(
                {"error": "virtualdj_drop_dir must be a string or null"},
                status_code=400,
            )
    if "virtualdj_api_base" in body:
        v = body.get("virtualdj_api_base")
        if v is None or v == "":
            patch["virtualdj_api_base"] = None
        elif isinstance(v, str):
            patch["virtualdj_api_base"] = v.strip().rstrip("/") or None
        else:
            return JSONResponse(
                {"error": "virtualdj_api_base must be a string or null"},
                status_code=400,
            )
    if "reaper_drop_dir" in body:
        v = body.get("reaper_drop_dir")
        if v is None or v == "":
            patch["reaper_drop_dir"] = None
        elif isinstance(v, str):
            patch["reaper_drop_dir"] = v.strip() or None
        else:
            return JSONResponse(
                {"error": "reaper_drop_dir must be a string or null"},
                status_code=400,
            )
    if "reaper_api_base" in body:
        v = body.get("reaper_api_base")
        if v is None or v == "":
            patch["reaper_api_base"] = None
        elif isinstance(v, str):
            patch["reaper_api_base"] = v.strip().rstrip("/") or None
        else:
            return JSONResponse(
                {"error": "reaper_api_base must be a string or null"},
                status_code=400,
            )
    if "google_cloud_project" in body:
        v = body.get("google_cloud_project")
        if v is None or v == "":
            patch["google_cloud_project"] = None
        elif isinstance(v, str):
            patch["google_cloud_project"] = v.strip() or None
        else:
            return JSONResponse(
                {"error": "google_cloud_project must be a string or null"},
                status_code=400,
            )
    if "lyria_model" in body:
        v = body.get("lyria_model")
        if v is None or v == "":
            patch["lyria_model"] = None
        elif isinstance(v, str):
            patch["lyria_model"] = v.strip() or None
        else:
            return JSONResponse(
                {"error": "lyria_model must be a string or null"},
                status_code=400,
            )
    if "hf_token" in body:
        v = body.get("hf_token")
        if v is None or v == "":
            patch["hf_token"] = None
        elif isinstance(v, str):
            patch["hf_token"] = v.strip() or None
        else:
            return JSONResponse({"error": "hf_token must be a string or null"}, status_code=400)
    if not patch:
        return JSONResponse({"error": "no recognized fields"}, status_code=400)
    updated = save_settings(patch)
    if "studio_url" in patch:
        # Hot-reload target without restarting the server process.
        _logic = SongGenerationLogic(base_url=updated.get("studio_url"))
    return JSONResponse(_redact_settings(updated))


async def api_export_plex_post(request: Request) -> JSONResponse:
    settings = load_settings()
    raw = settings.get("plex_export_dir")
    if not raw or not isinstance(raw, str):
        return JSONResponse(
            {
                "success": False,
                "error": "Set Plex export directory in Settings or SONGGEN_PLEX_EXPORT_DIR.",
            },
            status_code=400,
        )
    plex_root = Path(raw).expanduser()
    if not plex_root.is_dir():
        return JSONResponse(
            {"success": False, "error": f"Plex export path is not a directory: {plex_root}"},
            status_code=400,
        )
    try:
        body = await request.json()
    except Exception as e:
        return JSONResponse({"success": False, "error": f"invalid json: {e}"}, status_code=400)
    if not isinstance(body, dict):
        return JSONResponse({"success": False, "error": "body must be an object"}, status_code=400)
    export_all = bool(body.get("export_all"))
    repo_id = body.get("repo_id")
    if export_all:
        result = export_all_with_mp3(plex_root)
        return JSONResponse(result)
    if not repo_id or not isinstance(repo_id, str):
        return JSONResponse(
            {"success": False, "error": "repo_id required unless export_all is true"},
            status_code=400,
        )
    result = export_repo_entry(repo_id, plex_root)
    status = 200 if result.get("success") else 400
    return JSONResponse(result, status_code=status)


async def api_export_virtualdj_post(request: Request) -> JSONResponse:
    settings = load_settings()
    raw = settings.get("virtualdj_drop_dir")
    if not raw or not isinstance(raw, str):
        return JSONResponse(
            {"success": False, "error": "Set VirtualDJ drop directory in Settings."},
            status_code=400,
        )
    try:
        body = await request.json()
    except Exception as e:
        return JSONResponse({"success": False, "error": f"invalid json: {e}"}, status_code=400)
    if not isinstance(body, dict):
        return JSONResponse({"success": False, "error": "body must be an object"}, status_code=400)
    repo_id = body.get("repo_id")
    deck = int(body.get("deck") or 1)
    if not isinstance(repo_id, str) or not repo_id:
        return JSONResponse({"success": False, "error": "repo_id required"}, status_code=400)
    export = export_repo_entry_to_virtualdj(repo_id, Path(raw), deck=deck)
    if not export.get("success"):
        return JSONResponse(export, status_code=400)

    vdj_base = str(settings.get("virtualdj_api_base") or "http://127.0.0.1:10877").rstrip("/")
    auto_play = bool(body.get("auto_play", True))
    sync_to_master = bool(body.get("sync_to_master", False))
    cue_at_start = bool(body.get("cue_at_start", False))
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            load_res = await client.post(
                f"{vdj_base}/api/v1/deck/{deck}/load",
                params={"track_path": str(export.get("path"))},
            )
            is_json = load_res.headers.get("content-type", "").startswith("application/json")
            load_data = load_res.json() if is_json else {"raw": load_res.text}
            if load_res.status_code >= 400:
                return JSONResponse(
                    {
                        "success": False,
                        "error": "VirtualDJ load failed",
                        "export_path": export.get("path"),
                        "virtualdj_status": load_res.status_code,
                        "virtualdj_response": load_data,
                    },
                    status_code=502,
                )
            play_data: dict[str, object] | None = None
            if auto_play:
                play_res = await client.post(
                    f"{vdj_base}/api/v1/deck/{deck}/play_pause",
                    params={"action": "play"},
                )
                play_is_json = play_res.headers.get("content-type", "").startswith("application/json")
                play_data = play_res.json() if play_is_json else {"raw": play_res.text}
            sync_data: dict[str, object] | None = None
            if sync_to_master:
                sync_res = await client.post(f"{vdj_base}/api/v1/deck/{deck}/sync")
                sync_is_json = sync_res.headers.get("content-type", "").startswith("application/json")
                sync_data = sync_res.json() if sync_is_json else {"raw": sync_res.text}
            cue_data: dict[str, object] | None = None
            if cue_at_start:
                cue_res = await client.post(
                    f"{vdj_base}/api/v1/deck/{deck}/cue",
                    params={"mode": "start"},
                )
                cue_is_json = cue_res.headers.get("content-type", "").startswith("application/json")
                cue_data = cue_res.json() if cue_is_json else {"raw": cue_res.text}
            return JSONResponse(
                {
                    "success": True,
                    "path": export.get("path"),
                    "deck": deck,
                    "virtualdj_base": vdj_base,
                    "loaded": load_data,
                    "played": play_data,
                    "synced": sync_data,
                    "cued": cue_data,
                }
            )
    except Exception as e:
        return JSONResponse(
            {
                "success": False,
                "error": f"VirtualDJ API call failed: {e}",
                "export_path": export.get("path"),
                "virtualdj_base": vdj_base,
            },
            status_code=502,
        )


async def api_export_virtualdj_status(_request: Request) -> JSONResponse:
    settings = load_settings()
    vdj_base = str(settings.get("virtualdj_api_base") or "http://127.0.0.1:10877").rstrip("/")
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            res = await client.get(f"{vdj_base}/api/health")
            is_json = res.headers.get("content-type", "").startswith("application/json")
            body = res.json() if is_json else {"raw": res.text}
            if res.status_code >= 400:
                return JSONResponse(
                    {
                        "ok": False,
                        "virtualdj_base": vdj_base,
                        "status_code": res.status_code,
                        "response": body,
                    },
                    status_code=200,
                )
            return JSONResponse({"ok": True, "virtualdj_base": vdj_base, "response": body})
    except Exception as e:
        return JSONResponse({"ok": False, "virtualdj_base": vdj_base, "error": str(e)})


async def api_export_reaper_post(request: Request) -> JSONResponse:
    settings = load_settings()
    raw = settings.get("reaper_drop_dir")
    if not raw or not isinstance(raw, str):
        return JSONResponse(
            {"success": False, "error": "Set Reaper drop directory in Settings."},
            status_code=400,
        )
    try:
        body = await request.json()
    except Exception as e:
        return JSONResponse({"success": False, "error": f"invalid json: {e}"}, status_code=400)
    if not isinstance(body, dict):
        return JSONResponse({"success": False, "error": "body must be an object"}, status_code=400)
    repo_id = body.get("repo_id")
    if not isinstance(repo_id, str) or not repo_id:
        return JSONResponse({"success": False, "error": "repo_id required"}, status_code=400)
    export = export_repo_entry_to_reaper(repo_id, Path(raw))
    if not export.get("success"):
        return JSONResponse(export, status_code=400)

    reaper_base = str(settings.get("reaper_api_base") or "http://127.0.0.1:10797").rstrip("/")
    auto_import = bool(body.get("auto_import", True))
    import_data: dict[str, object] | None = None
    if auto_import:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                imp_res = await client.post(
                    f"{reaper_base}/api/v1/project/import_media",
                    params={"file_path": str(export.get("path"))},
                )
                is_json = imp_res.headers.get("content-type", "").startswith("application/json")
                import_data = imp_res.json() if is_json else {"raw": imp_res.text}
                if imp_res.status_code >= 400:
                    return JSONResponse(
                        {
                            "success": False,
                            "error": "Reaper import failed",
                            "reaper_status": imp_res.status_code,
                            "reaper_response": import_data,
                            "path": export.get("path"),
                        },
                        status_code=502,
                    )
        except Exception as e:
            return JSONResponse(
                {
                    "success": False,
                    "error": f"Reaper API call failed: {e}",
                    "path": export.get("path"),
                    "reaper_base": reaper_base,
                },
                status_code=502,
            )
    return JSONResponse(
        {
            "success": True,
            "path": export.get("path"),
            "reaper_base": reaper_base,
            "imported": import_data,
        }
    )


async def api_media_get(request: Request) -> FileResponse | JSONResponse:
    file_path = request.path_params.get("file_path", "")
    rel = Path(file_path)
    if rel.is_absolute() or ".." in rel.parts:
        return JSONResponse({"error": "invalid path"}, status_code=400)
    target = (media_dir() / rel).resolve()
    media_root = media_dir().resolve()
    try:
        target.relative_to(media_root)
    except ValueError:
        return JSONResponse({"error": "invalid path"}, status_code=400)
    if not target.is_file():
        return JSONResponse({"error": "not found"}, status_code=404)
    return FileResponse(target)


app = Starlette(
    routes=[
        Route("/api/health", api_health, methods=["GET"]),
        Route("/api/logs", api_logs_get, methods=["GET"]),
        Route("/api/logs/clear", api_logs_clear, methods=["POST"]),
        Route("/api/studio/status", api_studio_status, methods=["GET"]),
        Route("/api/studio/test", api_studio_test, methods=["GET"]),
        Route("/api/studio/info", api_studio_info, methods=["GET"]),
        Route("/api/lyria/status", api_lyria_status, methods=["GET"]),
        Route("/api/huggingface/status", api_huggingface_status, methods=["GET"]),
        Route("/api/generate", api_generate_post, methods=["POST"]),
        Route("/api/v1/generate", api_v1_generate_post, methods=["POST"]),
        Route("/api/songs", api_songs_list, methods=["GET"]),
        Route("/api/songs/{repo_id}", api_song_get, methods=["GET"]),
        Route("/api/settings", api_settings_get, methods=["GET"]),
        Route("/api/settings", api_settings_post, methods=["POST"]),
        Route("/api/llm/providers", api_llm_providers, methods=["GET"]),
        Route("/api/export/plex", api_export_plex_post, methods=["POST"]),
        Route("/api/export/virtualdj", api_export_virtualdj_post, methods=["POST"]),
        Route("/api/export/virtualdj/status", api_export_virtualdj_status, methods=["GET"]),
        Route("/api/export/reaper", api_export_reaper_post, methods=["POST"]),
        Route("/api/media/{file_path:path}", api_media_get, methods=["GET"]),
        Mount("/", _mcp_http),
    ],
    middleware=[
        Middleware(
            CORSMiddleware,
            allow_origins=[
                "http://localhost:10884",
                "http://127.0.0.1:10884",
                "http://goliath:10884",
                "http://localhost:10885",
                "http://127.0.0.1:10885",
                "http://goliath:10885",
                "http://tauri.localhost",
                "https://tauri.localhost",
                "tauri://localhost",
            ],
            allow_origin_regex=r"https?://(localhost|127\.0\.0\.1|goliath|tauri\.localhost)(:\\d+)?",
            allow_methods=["*"],
            allow_headers=["*"],
        ),
    ],
)

"""ASGI app for uvicorn (web_sota backend on fleet port 10885).

Exposes MCP streamable HTTP at ``/mcp``, JSON helpers for logs/health, and REST
for the web UI: generate, Studio status, song repository.
"""

from __future__ import annotations

import logging
from pathlib import Path

import httpx
from starlette.applications import Starlette
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
    logging.getLogger(__name__).warning(
        "Log buffer cleared by operator (%s entries removed).", removed
    )
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
    checks.append({
        "name": "studio_dir",
        "ok": dir_ok,
        "detail": studio_dir if studio_dir else "not configured",
    })

    # 2. HTTP reachable — /api/health
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
                            f"{g.get('name','?')} — "
                            f"{g.get('free_gb','?')} GB free / {g.get('total_gb','?')} GB total"
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
                        ms_detail = f"running — model: {loaded or 'none loaded'}"
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
    return JSONResponse({
        "ok": overall,
        "studio_url": studio_url,
        "checks": checks,
    })


async def api_studio_info(_request: Request) -> JSONResponse:
    settings = load_settings()
    reachable = await ensure_studio_available(
        _logic.base_url, studio_dir=settings.get("studio_dir")
    )
    status = await _logic.get_status()
    return JSONResponse(
        {
            "studio_url": _logic.base_url,
            "ui_url": _logic.base_url,
            "reachable": reachable and "error" not in status,
            "status_error": status.get("error"),
        }
    )


async def api_generate_post(request: Request) -> JSONResponse:
    try:
        body = await request.json()
    except Exception as e:
        return JSONResponse({"success": False, "error": f"invalid json: {e}"}, status_code=400)
    if not isinstance(body, dict):
        return JSONResponse({"success": False, "error": "body must be an object"}, status_code=400)
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
                    role_mp3 = await transcode_audio_urls_to_mp3(
                        role_urls, f"{entry['repo_id']}-{role}"
                    )
                    mp3_stem_urls[role] = role_mp3
                result["mp3_stem_urls"] = mp3_stem_urls
                update_entry(
                    entry["repo_id"], {"mp3_urls": mp3_urls, "mp3_stem_urls": mp3_stem_urls}
                )
    return JSONResponse(result)


async def api_songs_list(_request: Request) -> JSONResponse:
    return JSONResponse({"entries": list_entries(limit=200)})


async def api_song_get(request: Request) -> JSONResponse:
    repo_id = request.path_params.get("repo_id", "")
    row = get_entry(repo_id)
    if row is None:
        return JSONResponse({"error": "not found"}, status_code=404)
    return JSONResponse(row)


async def api_settings_get(_request: Request) -> JSONResponse:
    return JSONResponse(load_settings())


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
    if not patch:
        return JSONResponse({"error": "no recognized fields"}, status_code=400)
    updated = save_settings(patch)
    if "studio_url" in patch:
        # Hot-reload target without restarting the server process.
        _logic = SongGenerationLogic(base_url=updated.get("studio_url"))
    return JSONResponse(updated)


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
                play_is_json = play_res.headers.get("content-type", "").startswith(
                    "application/json"
                )
                play_data = play_res.json() if play_is_json else {"raw": play_res.text}
            sync_data: dict[str, object] | None = None
            if sync_to_master:
                sync_res = await client.post(f"{vdj_base}/api/v1/deck/{deck}/sync")
                sync_is_json = sync_res.headers.get("content-type", "").startswith(
                    "application/json"
                )
                sync_data = sync_res.json() if sync_is_json else {"raw": sync_res.text}
            cue_data: dict[str, object] | None = None
            if cue_at_start:
                cue_res = await client.post(
                    f"{vdj_base}/api/v1/deck/{deck}/cue",
                    params={"mode": "start"},
                )
                cue_is_json = cue_res.headers.get("content-type", "").startswith(
                    "application/json"
                )
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
        Route("/api/generate", api_generate_post, methods=["POST"]),
        Route("/api/songs", api_songs_list, methods=["GET"]),
        Route("/api/songs/{repo_id}", api_song_get, methods=["GET"]),
        Route("/api/settings", api_settings_get, methods=["GET"]),
        Route("/api/settings", api_settings_post, methods=["POST"]),
        Route("/api/export/plex", api_export_plex_post, methods=["POST"]),
        Route("/api/export/virtualdj", api_export_virtualdj_post, methods=["POST"]),
        Route("/api/export/virtualdj/status", api_export_virtualdj_status, methods=["GET"]),
        Route("/api/export/reaper", api_export_reaper_post, methods=["POST"]),
        Route("/api/media/{file_path:path}", api_media_get, methods=["GET"]),
        Mount("/", _mcp_http),
    ],
)

"""Optional WAV/remote audio -> MP3 transcoding helpers."""

from __future__ import annotations

import asyncio
import logging
import re
import shutil
from pathlib import Path
from urllib.parse import urlparse

import httpx

from .repository import media_dir

logger = logging.getLogger("songgeneration-mcp.mp3")


def _safe_slug(text: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", text).strip("-")
    return cleaned[:80] or "track"


def _resolve_ffmpeg_executable() -> str:
    """Resolve ffmpeg executable from system PATH or bundled dependency."""
    system = shutil.which("ffmpeg")
    if system:
        return system
    try:
        from imageio_ffmpeg import get_ffmpeg_exe

        return get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


def _media_name(repo_id: str, idx: int, ext: str) -> str:
    return f"{_safe_slug(repo_id)}-{idx + 1}{ext}"


def _pick_extension(url: str, content_type: str) -> str:
    parsed = urlparse(url)
    suffix = Path(parsed.path).suffix.lower()
    if suffix in (".wav", ".mp3", ".flac", ".ogg", ".m4a"):
        return suffix
    ctype = content_type.lower()
    if "wav" in ctype:
        return ".wav"
    if "mpeg" in ctype or "mp3" in ctype:
        return ".mp3"
    if "flac" in ctype:
        return ".flac"
    if "ogg" in ctype:
        return ".ogg"
    if "mp4" in ctype or "m4a" in ctype:
        return ".m4a"
    return ".bin"


def _api_media_to_path(url: str) -> Path | None:
    if not url.startswith("/api/media/"):
        return None
    name = url.removeprefix("/api/media/").lstrip("/")
    if ".." in name or name.startswith("/"):
        return None
    return media_dir() / name


async def download_audio_urls_to_local(audio_urls: list[str], repo_id: str) -> list[str]:
    """Download audio URLs and return local ``/api/media/*`` URLs."""
    out_urls: list[str] = []
    base = media_dir()
    base.mkdir(parents=True, exist_ok=True)
    async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
        for idx, source in enumerate(audio_urls):
            existing = _api_media_to_path(source)
            if existing and existing.is_file():
                out_urls.append(source)
                continue
            lsrc = source.lower()
            if not lsrc.startswith(("http://", "https://")):
                continue
            try:
                resp = await client.get(source)
                resp.raise_for_status()
            except Exception as e:
                logger.warning("Failed downloading source audio %s: %s", source, e)
                continue
            ext = _pick_extension(source, resp.headers.get("content-type", ""))
            if ext == ".bin":
                logger.warning("Skipping non-audio content from %s", source)
                continue
            name = _media_name(repo_id, idx, ext)
            out_path = base / name
            try:
                out_path.write_bytes(resp.content)
            except Exception as e:
                logger.warning("Failed writing local audio %s: %s", out_path, e)
                continue
            out_urls.append(f"/api/media/{name}")
    return out_urls


async def _run_ffmpeg(source: str, output_path: Path) -> bool:
    ffmpeg_exe = _resolve_ffmpeg_executable()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    proc = await asyncio.create_subprocess_exec(
        ffmpeg_exe,
        "-y",
        "-i",
        source,
        "-codec:a",
        "libmp3lame",
        "-q:a",
        "2",
        str(output_path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        err = (stderr or b"").decode("utf-8", errors="ignore")
        logger.warning("ffmpeg failed for %s: %s", source, err)
        return False
    return output_path.is_file()


async def transcode_audio_urls_to_mp3(audio_urls: list[str], repo_id: str) -> list[str]:
    """Convert discovered audio URLs to local MP3 files and return API URLs."""
    out_urls: list[str] = []
    base = media_dir()
    for idx, source in enumerate(audio_urls):
        # Skip clearly non-audio endpoints.
        lsrc = source.lower()
        if not (
            lsrc.endswith(".wav")
            or lsrc.endswith(".flac")
            or lsrc.endswith(".ogg")
            or lsrc.endswith(".m4a")
            or lsrc.endswith(".mp3")
            or "/audio" in lsrc
        ):
            continue
        name = _media_name(repo_id, idx, ".mp3")
        out_path = base / name
        local_path = _api_media_to_path(source)
        ffmpeg_source = str(local_path) if local_path and local_path.is_file() else source
        ok = await _run_ffmpeg(ffmpeg_source, out_path)
        if ok:
            out_urls.append(f"/api/media/{name}")
    return out_urls

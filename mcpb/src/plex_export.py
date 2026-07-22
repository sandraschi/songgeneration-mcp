"""Copy locally stored MP3s into a Plex music library folder."""

from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Any

from songgeneration_mcp.repository import get_entry, list_entries, media_dir


def _safe_filename(name: str, max_len: int = 120) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip(" .")
    return (cleaned or "track")[:max_len]


def _mp3_paths_from_urls(mp3_urls: list[str]) -> list[Path]:
    out: list[Path] = []
    root = media_dir().resolve()
    for u in mp3_urls:
        if not u.startswith("/api/media/"):
            continue
        name = u.removeprefix("/api/media/").lstrip("/")
        if ".." in name or name.startswith("/"):
            continue
        p = (root / name).resolve()
        try:
            p.relative_to(root)
        except ValueError:
            continue
        if p.is_file():
            out.append(p)
    return out


def export_repo_entry(repo_id: str, plex_root: Path) -> dict[str, Any]:
    """Copy one repository entry's local MP3s into ``plex_root / SongGeneration-MCP /``."""
    row = get_entry(repo_id)
    if row is None:
        return {"success": False, "error": "entry not found", "copied": []}
    mp3_urls = list(row.get("mp3_urls") or [])
    if not mp3_urls:
        return {
            "success": False,
            "error": "no local MP3 for this entry (transcode first)",
            "copied": [],
        }
    paths = _mp3_paths_from_urls(mp3_urls)
    if not paths:
        return {"success": False, "error": "MP3 files missing on disk", "copied": []}
    dest_dir = plex_root.expanduser().resolve() / "SongGeneration-MCP"
    dest_dir.mkdir(parents=True, exist_ok=True)
    title = _safe_filename(str(row.get("title") or "Untitled"))
    copied: list[str] = []
    for idx, src in enumerate(paths, start=1):
        suffix = src.suffix.lower() or ".mp3"
        dest_name = f"{title}-{row['repo_id'][:8]}-{idx}{suffix}"
        dest = dest_dir / _safe_filename(dest_name, 180)
        shutil.copy2(src, dest)
        copied.append(str(dest))
    return {"success": True, "copied": copied, "dest_dir": str(dest_dir)}


def export_all_with_mp3(plex_root: Path, limit: int = 200) -> dict[str, Any]:
    """Export every entry that has ``mp3_urls`` and resolvable files."""
    entries = list_entries(limit=limit)
    all_copied: list[str] = []
    errors: list[str] = []
    for e in entries:
        if not e.get("mp3_urls"):
            continue
        r = export_repo_entry(str(e["repo_id"]), plex_root)
        if r.get("success"):
            all_copied.extend(r.get("copied") or [])
        else:
            err = str(r.get("error") or "unknown")
            if err not in ("no local MP3 for this entry (transcode first)",):
                errors.append(f"{e.get('repo_id')}: {err}")
    return {
        "success": True,
        "copied_count": len(all_copied),
        "copied": all_copied,
        "errors": errors,
    }

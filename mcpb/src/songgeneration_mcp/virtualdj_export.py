"""Copy selected local audio into a VirtualDJ drop folder."""

from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Any

from songgeneration_mcp.repository import get_entry, media_dir


def _safe_filename(name: str, max_len: int = 140) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip(" .")
    return (cleaned or "track")[:max_len]


def _api_media_to_path(url: str) -> Path | None:
    if not url.startswith("/api/media/"):
        return None
    name = url.removeprefix("/api/media/").lstrip("/")
    if ".." in name or name.startswith("/"):
        return None
    p = (media_dir() / name).resolve()
    root = media_dir().resolve()
    try:
        p.relative_to(root)
    except ValueError:
        return None
    if not p.is_file():
        return None
    return p


def export_repo_entry_to_virtualdj(repo_id: str, drop_dir: Path, deck: int = 1) -> dict[str, Any]:
    """Copy best local file for one entry into the configured VirtualDJ folder."""
    row = get_entry(repo_id)
    if row is None:
        return {"success": False, "error": "entry not found"}

    preferred_urls = list(row.get("mp3_urls") or []) + list(row.get("audio_urls") or [])
    source_path: Path | None = None
    for u in preferred_urls:
        p = _api_media_to_path(u)
        if p is not None:
            source_path = p
            break
    if source_path is None:
        return {"success": False, "error": "no local file available for this entry"}

    target_root = drop_dir.expanduser().resolve()
    target_root.mkdir(parents=True, exist_ok=True)
    title = _safe_filename(str(row.get("title") or "Untitled"))
    suffix = source_path.suffix.lower() or ".mp3"
    out_name = _safe_filename(f"D{deck}-{title}-{str(row.get('repo_id', 'x'))[:8]}{suffix}", 200)
    out_path = target_root / out_name
    shutil.copy2(source_path, out_path)
    return {"success": True, "path": str(out_path), "deck": deck}

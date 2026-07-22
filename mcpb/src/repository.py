"""Append-only JSON repository for generation runs (local to this machine)."""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

_MAX_ENTRIES = min(2000, max(50, int(os.getenv("SONGGEN_REPO_MAX_ENTRIES", "500"))))


def _repo_path() -> Path:
    raw = os.getenv("SONGGEN_REPO_PATH", "").strip()
    if raw:
        return Path(raw)
    return Path.home() / ".songgeneration-mcp" / "repository.json"


def media_dir() -> Path:
    """Directory where generated media artifacts are stored."""
    return _repo_path().parent / "media"


def _load() -> dict[str, Any]:
    p = _repo_path()
    if not p.is_file():
        return {"entries": []}
    with p.open(encoding="utf-8") as f:
        return json.load(f)


def _save(data: dict[str, Any]) -> None:
    p = _repo_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".json.tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    tmp.replace(p)


def extract_audio_urls(obj: Any, *, studio_base_url: str | None = None) -> list[str]:
    """Collect http(s) URLs that look like playable assets from a Studio JSON blob.

    When ``studio_base_url`` is set and the blob is a completed generation with
    ``output_files`` / ``output_file``, also adds SongGeneration Studio download
    URLs ``{base}/api/audio/{generation_id}/{idx}``.
    """
    found: list[str] = []

    def walk(x: Any) -> None:
        if isinstance(x, dict):
            for k, v in x.items():
                lk = str(k).lower()
                if lk in (
                    "audio_url",
                    "url",
                    "download_url",
                    "preview_url",
                    "file_url",
                    "wav_url",
                    "src",
                ) and isinstance(v, str):
                    if v.startswith(("http://", "https://")) and any(
                        v.lower().endswith(ext)
                        for ext in (".wav", ".mp3", ".ogg", ".flac", ".m4a")
                    ):
                        found.append(v)
                    elif v.startswith(("http://", "https://")) and "/audio" in v.lower():
                        found.append(v)
                else:
                    walk(v)
        elif isinstance(x, list):
            for i in x:
                walk(i)

    walk(obj)
    out: list[str] = []
    seen: set[str] = set()
    for u in found:
        if u not in seen:
            seen.add(u)
            out.append(u)

    if studio_base_url and isinstance(obj, dict) and str(obj.get("status") or "") == "completed":
        gid = obj.get("generation_id")
        if isinstance(gid, str) and gid.strip():
            outs: list[str] = []
            raw_files = obj.get("output_files")
            if isinstance(raw_files, list) and raw_files:
                outs = [str(x) for x in raw_files if x]
            elif isinstance(obj.get("output_file"), str) and str(obj.get("output_file")):
                outs = [str(obj["output_file"])]
            base = studio_base_url.rstrip("/")
            for i in range(len(outs)):
                u = f"{base}/api/audio/{gid}/{i}"
                if u not in seen:
                    seen.add(u)
                    out.append(u)
    return out


def _infer_stem_role(url: str, key_hint: str = "") -> str | None:
    hint = f"{key_hint} {urlparse(url).path}".lower()
    if any(x in hint for x in ("vocal", "voice")):
        return "vocal"
    if any(x in hint for x in ("instrumental", "inst", "accompaniment")):
        return "instrumental"
    if any(x in hint for x in ("mix", "master", "full")):
        return "mix"
    return None


def extract_stem_urls(obj: Any) -> dict[str, list[str]]:
    """Collect stem-role URLs from Studio JSON blob."""
    stems: dict[str, list[str]] = {"vocal": [], "instrumental": [], "mix": []}

    def walk(x: Any, key_hint: str = "") -> None:
        if isinstance(x, dict):
            for k, v in x.items():
                if isinstance(v, str) and v.startswith(("http://", "https://")):
                    role = _infer_stem_role(v, str(k))
                    if role:
                        stems[role].append(v)
                else:
                    walk(v, str(k))
        elif isinstance(x, list):
            for i in x:
                walk(i, key_hint)

    walk(obj)
    # Deduplicate while preserving order.
    for role, urls in stems.items():
        seen: set[str] = set()
        deduped: list[str] = []
        for u in urls:
            if u not in seen:
                seen.add(u)
                deduped.append(u)
        stems[role] = deduped
    return stems


def add_generation_entry(
    *,
    generation_id: Any,
    title: str,
    genre: str,
    mood: str,
    message: str,
    studio_response: dict[str, Any],
    punctuation_notes: list[str],
    studio_base_url: str | None = None,
) -> dict[str, Any]:
    """Persist one successful generation metadata. Returns the stored row including ``repo_id``."""
    audio_urls = extract_audio_urls(studio_response, studio_base_url=studio_base_url)
    stem_urls = extract_stem_urls(studio_response)
    entry: dict[str, Any] = {
        "repo_id": str(uuid.uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "generation_id": generation_id,
        "title": title,
        "genre": genre,
        "mood": mood,
        "message": message,
        "audio_urls": audio_urls,
        "stem_urls": stem_urls,
        "punctuation_notes": punctuation_notes,
    }
    # Avoid huge JSON on disk — keep a slim snapshot
    slim: dict[str, Any] = {}
    for key in ("status", "state", "progress", "outputs", "files", "paths", "result", "error"):
        if key in studio_response:
            slim[key] = studio_response[key]
    if slim:
        entry["studio_snapshot"] = slim
    data = _load()
    entries: list[dict[str, Any]] = list(data.get("entries", []))
    entries.insert(0, entry)
    data["entries"] = entries[:_MAX_ENTRIES]
    _save(data)
    return entry


def list_entries(limit: int = 200) -> list[dict[str, Any]]:
    data = _load()
    entries = data.get("entries", [])
    return entries[: max(0, min(limit, 500))]


def get_entry(repo_id: str) -> dict[str, Any] | None:
    for e in list_entries(limit=500):
        if e.get("repo_id") == repo_id:
            return e
    return None


def update_entry(repo_id: str, patch: dict[str, Any]) -> dict[str, Any] | None:
    """Patch one repository row and persist; returns updated row or None."""
    data = _load()
    entries: list[dict[str, Any]] = list(data.get("entries", []))
    for idx, entry in enumerate(entries):
        if entry.get("repo_id") == repo_id:
            updated = dict(entry)
            updated.update(patch)
            entries[idx] = updated
            data["entries"] = entries
            _save(data)
            return updated
    return None

"""Persisted UI settings (Plex export path, etc.)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def _settings_path() -> Path:
    raw = os.getenv("SONGGEN_SETTINGS_PATH", "").strip()
    if raw:
        return Path(raw)
    return Path.home() / ".songgeneration-mcp" / "settings.json"


def load_settings() -> dict[str, Any]:
    """Load settings with env var overrides."""
    p = _settings_path()
    data: dict[str, Any] = {}
    if p.is_file():
        with p.open(encoding="utf-8") as f:
            data = json.load(f)
    env_plex = os.getenv("SONGGEN_PLEX_EXPORT_DIR", "").strip()
    if env_plex:
        data["plex_export_dir"] = env_plex
        data["plex_export_dir_from_env"] = True
    else:
        data["plex_export_dir_from_env"] = False
    env_studio = (
        os.getenv("SONGGENERATION_STUDIO_URL", "").strip()
        or os.getenv("SONGGEN_STUDIO_BASE_URL", "").strip()
    )
    if env_studio:
        data["studio_url"] = env_studio
        data["studio_url_from_env"] = True
    else:
        data["studio_url_from_env"] = False
    env_studio_dir = os.getenv("SONGGEN_STUDIO_DIR", "").strip()
    if env_studio_dir:
        data["studio_dir"] = env_studio_dir
        data["studio_dir_from_env"] = True
    else:
        data["studio_dir_from_env"] = False
    env_vdj = os.getenv("SONGGEN_VIRTUALDJ_API_BASE", "").strip()
    if env_vdj:
        data["virtualdj_api_base"] = env_vdj.rstrip("/")
        data["virtualdj_api_base_from_env"] = True
    else:
        data["virtualdj_api_base_from_env"] = False
    env_reaper_drop = os.getenv("SONGGEN_REAPER_DROP_DIR", "").strip()
    if env_reaper_drop:
        data["reaper_drop_dir"] = env_reaper_drop
        data["reaper_drop_dir_from_env"] = True
    else:
        data["reaper_drop_dir_from_env"] = False
    env_reaper_api = os.getenv("SONGGEN_REAPER_API_BASE", "").strip()
    if env_reaper_api:
        data["reaper_api_base"] = env_reaper_api.rstrip("/")
        data["reaper_api_base_from_env"] = True
    else:
        data["reaper_api_base_from_env"] = False
    return data


def save_settings(patch: dict[str, Any]) -> dict[str, Any]:
    """Merge patch into on-disk settings (does not change process env)."""
    p = _settings_path()
    current: dict[str, Any] = {}
    if p.is_file():
        with p.open(encoding="utf-8") as f:
            current = json.load(f)
    for k, v in patch.items():
        if k in (
            "plex_export_dir",
            "studio_url",
            "studio_dir",
            "virtualdj_drop_dir",
            "virtualdj_api_base",
            "reaper_drop_dir",
            "reaper_api_base",
        ):
            current[k] = v
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".json.tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(current, f, indent=2)
    tmp.replace(p)
    return load_settings()

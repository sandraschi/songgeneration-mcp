from __future__ import annotations

import asyncio
import os
import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlparse

import httpx

_DEFAULT_STUDIO_DIR = Path(r"D:\Dev\repos\external\SongGeneration-Studio")


def _is_local_target(base_url: str) -> bool:
    host = (urlparse(base_url).hostname or "").lower()
    return host in {"127.0.0.1", "localhost"}


def _studio_port(base_url: str) -> int:
    parsed = urlparse(base_url)
    if parsed.port:
        return parsed.port
    return 443 if parsed.scheme == "https" else 80


async def _ping_studio(base_url: str, timeout_s: float = 1.5) -> bool:
    try:
        async with httpx.AsyncClient(timeout=timeout_s) as client:
            res = await client.get(f"{base_url.rstrip('/')}/api/gpu")
            return res.status_code < 500
    except Exception:
        return False


def _autostart_enabled(value: bool | None = None) -> bool:
    if value is not None:
        return bool(value)
    raw = (os.getenv("SONGGEN_STUDIO_AUTO_START", "1") or "1").strip().lower()
    return raw not in {"0", "false", "no", "off"}


def _studio_dir(value: str | None = None) -> Path:
    raw = (value or os.getenv("SONGGEN_STUDIO_DIR", "") or "").strip()
    return Path(raw) if raw else _DEFAULT_STUDIO_DIR


def _spawn_studio(base_url: str, studio_dir_value: str | None = None) -> bool:
    studio_dir = _studio_dir(studio_dir_value)
    main_py = studio_dir / "main.py"
    if not main_py.is_file():
        return False
    port = _studio_port(base_url)
    host = "127.0.0.1"
    uv = shutil.which("uv")
    if uv:
        cmd = [
            uv,
            "run",
            "--directory",
            str(studio_dir),
            "python",
            "main.py",
            "--host",
            host,
            "--port",
            str(port),
        ]
    else:
        custom = (os.getenv("SONGGEN_STUDIO_PYTHON", "") or "").strip()
        if custom:
            cmd = [custom, "main.py", "--host", host, "--port", str(port)]
        elif shutil.which("python"):
            cmd = ["python", "main.py", "--host", host, "--port", str(port)]
        elif shutil.which("py"):
            cmd = ["py", "-3", "main.py", "--host", host, "--port", str(port)]
        else:
            return False
    kwargs: dict[str, object] = {
        "cwd": str(studio_dir),
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
    }
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
    else:
        kwargs["start_new_session"] = True
    subprocess.Popen(cmd, **kwargs)
    return True


async def ensure_studio_available(
    base_url: str,
    wait_ms: int = 20000,
    *,
    studio_dir: str | None = None,
    auto_start: bool | None = None,
) -> bool:
    if await _ping_studio(base_url):
        return True
    if not _autostart_enabled(auto_start) or not _is_local_target(base_url):
        return False
    if not _spawn_studio(base_url, studio_dir):
        return False

    deadline = asyncio.get_event_loop().time() + (wait_ms / 1000.0)
    while asyncio.get_event_loop().time() < deadline:
        if await _ping_studio(base_url):
            return True
        await asyncio.sleep(0.75)
    return False

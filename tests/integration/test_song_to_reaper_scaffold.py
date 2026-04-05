"""Integration scaffold: generate 'Mary Had a Little Lamb' and export to Reaper.

- GitHub Actions: mocked Studio/Reaper HTTP (no external services).
- Local: set SONGGEN_REAL_EXTERNAL=1 and the env vars below for a real run (no respx, no fake download).

Real local env:
  SONGGEN_REAL_EXTERNAL=1
  SONGGENERATION_STUDIO_URL=http://127.0.0.1:10930
  SONGGEN_REAPER_API_BASE=http://127.0.0.1:10797
  SONGGEN_REAPER_DROP_DIR=<writable folder Reaper can import from>
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
import respx
from httpx import ASGITransport, AsyncClient

from songgeneration_mcp.repository import list_entries
from songgeneration_mcp.server import app


def _real_mode() -> bool:
    raw = (os.getenv("SONGGEN_REAL_EXTERNAL", "") or "").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _in_github_actions() -> bool:
    return os.getenv("GITHUB_ACTIONS") == "true"


@pytest.mark.asyncio
@respx.mock
async def test_song_generation_and_reaper_export_ci_mocked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Mocked Studio + Reaper; runs only on GitHub Actions."""
    if not _in_github_actions():
        pytest.skip("Mocked integration runs in CI only")

    monkeypatch.setenv("SONGGEN_REPO_PATH", str(tmp_path / "repo.json"))
    monkeypatch.setenv("SONGGEN_SETTINGS_PATH", str(tmp_path / "settings.json"))
    monkeypatch.setenv("SONGGEN_STUDIO_AUTO_START", "0")

    media = tmp_path / "media"
    media.mkdir(parents=True, exist_ok=True)
    (media / "mary.mp3").write_bytes(b"fake-mp3")

    studio_url = "http://localhost:10930"
    reaper_api = "http://127.0.0.1:10797"
    reaper_drop = str(tmp_path / "reaper_drop")

    respx.get(f"{studio_url}/api/gpu").respond(json={"total": 24, "used": 8})
    respx.post(f"{studio_url}/api/generate").respond(
        json={
            "generation_id": "mary-realish",
            "status": "queued",
            "audio_url": "http://example.com/mary.wav",
        }
    )

    async def fake_download(audio_urls: list[str], repo_id: str) -> list[str]:
        assert audio_urls == ["http://example.com/mary.wav"]
        assert isinstance(repo_id, str)
        return ["/api/media/mary.mp3"]

    monkeypatch.setattr("songgeneration_mcp.server.download_audio_urls_to_local", fake_download)
    respx.post(f"{reaper_api}/api/v1/project/import_media").respond(
        json={"success": True, "imported": True}
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        s = await client.post(
            "/api/settings",
            json={
                "studio_url": studio_url,
                "reaper_api_base": reaper_api,
                "reaper_drop_dir": reaper_drop,
            },
        )
        assert s.status_code == 200

        g = await client.post(
            "/api/generate",
            json={
                "title": "Mary Had a Little Lamb",
                "genre": "Nursery",
                "mood": "Playful",
                "lyrics": "Mary had a little lamb. ; [chorus] Its fleece was white as snow.",
                "transcode_to_mp3": False,
            },
        )
        assert g.status_code == 200
        body = g.json()
        assert body.get("success") is True
        assert body.get("repo_id")

        repo_id = str(body["repo_id"])
        entries = list_entries(limit=20)
        assert any(str(e.get("repo_id")) == repo_id for e in entries)

        r = await client.post(
            "/api/export/reaper",
            json={"repo_id": repo_id, "auto_import": True},
        )
        assert r.status_code == 200
        rb = r.json()
        assert rb.get("success") is True
        assert rb.get("path")


@pytest.mark.asyncio
async def test_song_generation_and_reaper_export_real_local(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Real httpx to Studio and Reaper; not run in CI. No respx, no fake download."""
    if _in_github_actions():
        pytest.skip("Real Studio+Reaper integration runs locally only")

    if not _real_mode():
        pytest.skip("Set SONGGEN_REAL_EXTERNAL=1 for real integration")

    reaper_drop = os.getenv("SONGGEN_REAPER_DROP_DIR")
    if not reaper_drop:
        pytest.skip("Set SONGGEN_REAPER_DROP_DIR for real integration")

    Path(reaper_drop).mkdir(parents=True, exist_ok=True)

    monkeypatch.setenv("SONGGEN_REPO_PATH", str(tmp_path / "repo.json"))
    monkeypatch.setenv("SONGGEN_SETTINGS_PATH", str(tmp_path / "settings.json"))
    monkeypatch.setenv("SONGGEN_STUDIO_AUTO_START", "0")

    studio_url = (os.getenv("SONGGENERATION_STUDIO_URL") or "http://127.0.0.1:10930").rstrip("/")
    reaper_api = (os.getenv("SONGGEN_REAPER_API_BASE") or "http://127.0.0.1:10797").rstrip("/")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        s = await client.post(
            "/api/settings",
            json={
                "studio_url": studio_url,
                "reaper_api_base": reaper_api,
                "reaper_drop_dir": reaper_drop,
            },
        )
        assert s.status_code == 200

        g = await client.post(
            "/api/generate",
            json={
                "title": "Mary Had a Little Lamb",
                "genre": "Nursery",
                "mood": "Playful",
                "lyrics": "Mary had a little lamb. ; [chorus] Its fleece was white as snow.",
                "transcode_to_mp3": False,
            },
        )
        assert g.status_code == 200
        body = g.json()
        assert body.get("success") is True
        assert body.get("repo_id")

        repo_id = str(body["repo_id"])
        entries = list_entries(limit=20)
        assert any(str(e.get("repo_id")) == repo_id for e in entries)

        r = await client.post(
            "/api/export/reaper",
            json={"repo_id": repo_id, "auto_import": True},
        )
        assert r.status_code == 200
        rb = r.json()
        assert rb.get("success") is True
        assert rb.get("path")
        exported = Path(str(rb["path"]))
        assert exported.exists()
        assert exported.stat().st_size > 0

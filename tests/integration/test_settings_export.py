"""Settings and Plex export API."""

from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient, Response

from songgeneration_mcp.repository import add_generation_entry, update_entry
from songgeneration_mcp.server import app


@pytest.mark.asyncio
async def test_api_settings_roundtrip(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SONGGEN_SETTINGS_PATH", str(tmp_path / "settings.json"))
    monkeypatch.delenv("SONGGEN_PLEX_EXPORT_DIR", raising=False)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        g = await client.get("/api/settings")
        assert g.status_code == 200
        assert g.json().get("plex_export_dir") in (None, "")

        p = await client.post(
            "/api/settings",
            json={
                "plex_export_dir": str(tmp_path / "plex_incoming"),
                "studio_url": "http://localhost:10930",
                "studio_dir": str(tmp_path / "studio"),
                "reaper_drop_dir": str(tmp_path / "reaper_drop"),
                "reaper_api_base": "http://127.0.0.1:10797",
            },
        )
        assert p.status_code == 200
        body = p.json()
        assert body.get("plex_export_dir") == str(tmp_path / "plex_incoming")
        assert body.get("studio_url") == "http://localhost:10930"
        assert body.get("studio_dir") == str(tmp_path / "studio")
        assert body.get("reaper_drop_dir") == str(tmp_path / "reaper_drop")
        assert body.get("reaper_api_base") == "http://127.0.0.1:10797"

        info = await client.get("/api/studio/info")
        assert info.status_code == 200
        assert info.json().get("studio_url") == "http://localhost:10930"


@pytest.mark.asyncio
async def test_api_export_plex_one_file(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SONGGEN_REPO_PATH", str(tmp_path / "repo.json"))
    monkeypatch.setenv("SONGGEN_SETTINGS_PATH", str(tmp_path / "settings.json"))
    monkeypatch.delenv("SONGGEN_PLEX_EXPORT_DIR", raising=False)

    media = tmp_path / "media"
    media.mkdir(parents=True)
    (media / "clip.mp3").write_bytes(b"fake")

    entry = add_generation_entry(
        generation_id="exp-1",
        title="My Song",
        genre="Pop",
        mood="x",
        message="ok",
        studio_response={},
        punctuation_notes=[],
    )
    update_entry(entry["repo_id"], {"mp3_urls": ["/api/media/clip.mp3"]})

    plex_root = tmp_path / "plex_music"
    plex_root.mkdir()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/api/settings", json={"plex_export_dir": str(plex_root)})

        r = await client.post("/api/export/plex", json={"repo_id": entry["repo_id"]})
        assert r.status_code == 200
        data = r.json()
        assert data.get("success") is True
        copied = data.get("copied") or []
        assert copied
        dest = plex_root / "SongGeneration-MCP"
        assert dest.is_dir()
        assert any(Path(p).name.endswith(".mp3") for p in copied)


@pytest.mark.asyncio
async def test_api_export_virtualdj(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SONGGEN_REPO_PATH", str(tmp_path / "repo.json"))
    monkeypatch.setenv("SONGGEN_SETTINGS_PATH", str(tmp_path / "settings.json"))
    monkeypatch.delenv("SONGGEN_PLEX_EXPORT_DIR", raising=False)

    media = tmp_path / "media"
    media.mkdir(parents=True)
    (media / "vdj.mp3").write_bytes(b"fake")

    entry = add_generation_entry(
        generation_id="exp-vdj",
        title="Deck Song",
        genre="EDM",
        mood="x",
        message="ok",
        studio_response={},
        punctuation_notes=[],
    )
    update_entry(entry["repo_id"], {"mp3_urls": ["/api/media/vdj.mp3"]})

    vdj_drop = tmp_path / "virtualdj_drop"
    class _FakeAsyncClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def post(self, url: str, params: dict | None = None):
            if "/load" in url:
                return Response(200, json={"status": "success", "loaded": params})
            if "/play_pause" in url:
                return Response(200, json={"status": "success", "action": "play"})
            return Response(404, json={"error": "not found"})

    monkeypatch.setattr("songgeneration_mcp.server.httpx.AsyncClient", _FakeAsyncClient)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post(
            "/api/settings",
            json={
                "virtualdj_drop_dir": str(vdj_drop),
                "virtualdj_api_base": "http://127.0.0.1:10877",
            },
        )
        r = await client.post(
            "/api/export/virtualdj",
            json={"repo_id": entry["repo_id"], "deck": 1},
        )
        assert r.status_code == 200
        body = r.json()
        assert body.get("success") is True
        assert (vdj_drop).is_dir()
        assert body.get("path")


@pytest.mark.asyncio
async def test_api_export_reaper(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SONGGEN_REPO_PATH", str(tmp_path / "repo.json"))
    monkeypatch.setenv("SONGGEN_SETTINGS_PATH", str(tmp_path / "settings.json"))

    media = tmp_path / "media"
    media.mkdir(parents=True)
    (media / "reaper.mp3").write_bytes(b"fake")

    entry = add_generation_entry(
        generation_id="exp-reaper",
        title="Reaper Song",
        genre="EDM",
        mood="x",
        message="ok",
        studio_response={},
        punctuation_notes=[],
    )
    update_entry(entry["repo_id"], {"mp3_urls": ["/api/media/reaper.mp3"]})

    reaper_drop = tmp_path / "reaper_drop"

    class _FakeAsyncClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def post(self, url: str, params: dict | None = None):
            if "/import_media" in url:
                return Response(200, json={"status": "success", "imported": params})
            return Response(404, json={"error": "not found"})

    monkeypatch.setattr("songgeneration_mcp.server.httpx.AsyncClient", _FakeAsyncClient)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post(
            "/api/settings",
            json={
                "reaper_drop_dir": str(reaper_drop),
                "reaper_api_base": "http://127.0.0.1:10797",
            },
        )
        r = await client.post(
            "/api/export/reaper",
            json={"repo_id": entry["repo_id"], "auto_import": True},
        )
        assert r.status_code == 200
        body = r.json()
        assert body.get("success") is True
        assert reaper_drop.is_dir()
        assert body.get("path")

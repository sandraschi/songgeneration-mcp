"""REST generate + repository endpoints."""

import pytest
import respx
from httpx import ASGITransport, AsyncClient

from songgeneration_mcp.server import app


@pytest.mark.asyncio
@respx.mock
async def test_api_generate_and_list_songs(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SONGGEN_REPO_PATH", str(tmp_path / "repo.json"))
    respx.post("http://localhost:10930/api/generate").respond(
        json={
            "generation_id": "gid-integration",
            "status": "queued",
            "audio_url": "http://cdn.example/gid-integration.wav",
        }
    )
    respx.get("http://cdn.example/gid-integration.wav").respond(content=b"fake-wav" * 400)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            "/api/generate",
            json={"lyrics": "Test line one. ; [chorus] Test two.", "genre": "Pop", "title": "T1"},
        )
        assert r.status_code == 200
        body = r.json()
        assert body.get("success") is True
        assert body.get("generation_id") == "gid-integration"
        assert body.get("repo_id")

        lst = await client.get("/api/songs")
        assert lst.status_code == 200
        entries = lst.json().get("entries", [])
        assert len(entries) >= 1
        assert entries[0].get("generation_id") == "gid-integration"

        one = await client.get(f"/api/songs/{entries[0]['repo_id']}")
        assert one.status_code == 200
        assert one.json().get("repo_id") == entries[0]["repo_id"]


@pytest.mark.asyncio
@respx.mock
async def test_api_generate_transcode_mp3_flag(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SONGGEN_REPO_PATH", str(tmp_path / "repo.json"))
    respx.post("http://localhost:10930/api/generate").respond(
        json={"generation_id": "gid-mp3", "status": "queued", "audio_url": "http://example.com/a.wav"}
    )

    async def fake_transcode(audio_urls: list[str], repo_id: str) -> list[str]:
        assert audio_urls == ["/api/media/local-a.wav"]
        assert isinstance(repo_id, str)
        return ["/api/media/fake-1.mp3"]

    async def fake_download(audio_urls: list[str], repo_id: str) -> list[str]:
        assert audio_urls == ["http://example.com/a.wav"]
        assert isinstance(repo_id, str)
        return ["/api/media/local-a.wav"]

    monkeypatch.setattr("songgeneration_mcp.server.transcode_audio_urls_to_mp3", fake_transcode)
    monkeypatch.setattr("songgeneration_mcp.server.download_audio_urls_to_local", fake_download)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            "/api/generate",
            json={
                "lyrics": "la la",
                "genre": "Pop",
                "title": "mp3",
                "transcode_to_mp3": True,
            },
        )
        assert r.status_code == 200
        body = r.json()
        assert body.get("success") is True
        assert body.get("audio_urls") == ["/api/media/local-a.wav"]
        assert body.get("source_audio_urls") == ["http://example.com/a.wav"]
        assert body.get("mp3_urls") == ["/api/media/fake-1.mp3"]

        lst = await client.get("/api/songs")
        assert lst.status_code == 200
        entries = lst.json().get("entries", [])
        assert entries[0].get("mp3_urls") == ["/api/media/fake-1.mp3"]
        assert entries[0].get("audio_urls") == ["/api/media/local-a.wav"]

"""ASGI HTTP helpers (health, logs) on the uvicorn app."""

import pytest
from httpx import ASGITransport, AsyncClient

from songgeneration_mcp.server import app


@pytest.mark.asyncio
async def test_api_health_and_logs() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        h = await client.get("/api/health")
        assert h.status_code == 200
        body = h.json()
        assert body.get("ok") is True
        assert body.get("service") == "songgeneration-mcp"

        lg = await client.get("/api/logs?limit=50")
        assert lg.status_code == 200
        data = lg.json()
        assert "lines" in data
        assert "count" in data
        assert isinstance(data["lines"], list)


@pytest.mark.asyncio
async def test_api_logs_clear() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        cl = await client.post("/api/logs/clear")
        assert cl.status_code == 200
        assert "cleared" in cl.json()


@pytest.mark.asyncio
async def test_api_media_serves_file(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SONGGEN_REPO_PATH", str(tmp_path / "repo.json"))
    media = tmp_path / "media"
    media.mkdir(parents=True, exist_ok=True)
    p = media / "demo.mp3"
    p.write_bytes(b"ID3")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        ok = await client.get("/api/media/demo.mp3")
        assert ok.status_code == 200
        assert ok.content.startswith(b"ID3")

        bad = await client.get("/api/media/%2e%2e/repo.json")
        assert bad.status_code == 400

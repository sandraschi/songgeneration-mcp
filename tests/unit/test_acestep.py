"""ACE-Step 1.5 REST bridge tests."""

from pathlib import Path

import pytest
import respx

from songgeneration_mcp.acestep import AcestepClient


@pytest.mark.asyncio
@respx.mock
async def test_health_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SONGGEN_ACESTEP_URL", "http://localhost:8001")
    respx.get("http://localhost:8001/health").respond(json={"data": {"status": "ok"}})
    client = AcestepClient()
    assert await client.health() is True


@pytest.mark.asyncio
@respx.mock
async def test_health_down(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SONGGEN_ACESTEP_URL", "http://localhost:8001")
    respx.get("http://localhost:8001/health").respond(status_code=503)
    client = AcestepClient()
    assert await client.health() is False


@pytest.mark.asyncio
@respx.mock
async def test_generate_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SONGGEN_ACESTEP_URL", "http://localhost:8001")
    respx.get("http://localhost:8001/health").respond(json={"data": {"status": "ok"}})
    respx.post("http://localhost:8001/release_task").respond(
        json={"data": {"task_id": "t1", "status": "queued"}}
    )
    respx.post("http://localhost:8001/query_result").respond(
        json={
            "data": [
                {
                    "task_id": "t1",
                    "status": 1,
                    "result": '[{"file": "/v1/audio?path=/tmp/x.wav", "dit_model": "acestep-v15-turbo"}]',
                }
            ]
        }
    )
    respx.get("http://localhost:8001/v1/audio?path=/tmp/x.wav").respond(content=b"RIFF....")

    client = AcestepClient()
    result = await client.generate("test song", duration=30)
    assert result["success"] is True
    assert result["model"] == "acestep-v15-turbo"
    assert result["duration"] == 30
    assert Path(result["file"]).read_bytes() == b"RIFF...."


@pytest.mark.asyncio
@respx.mock
async def test_generate_release_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SONGGEN_ACESTEP_URL", "http://localhost:8001")
    respx.post("http://localhost:8001/release_task").respond(status_code=500)

    client = AcestepClient()
    result = await client.generate("test song")
    assert result["success"] is False
    assert "release_task" in result["error"]


@pytest.mark.asyncio
@respx.mock
async def test_generate_task_failed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SONGGEN_ACESTEP_URL", "http://localhost:8001")
    respx.post("http://localhost:8001/release_task").respond(
        json={"data": {"task_id": "t2", "status": "queued"}}
    )
    respx.post("http://localhost:8001/query_result").respond(
        json={"data": [{"task_id": "t2", "status": 2, "result": "[]"}]}
    )

    client = AcestepClient()
    result = await client.generate("test song")
    assert result["success"] is False
    assert "failed" in result["error"]

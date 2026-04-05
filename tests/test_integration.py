import json

import pytest
import respx

from songgeneration_mcp.logic import SongGenerationLogic


@pytest.mark.asyncio
@respx.mock
async def test_list_models():
    logic = SongGenerationLogic(base_url="http://test")
    respx.get("http://test/api/models").respond(
        json={"models": [{"id": "model1"}, {"id": "model2"}]}
    )

    models = await logic.list_models()
    assert models == ["model1", "model2"]
    await logic.close()


@pytest.mark.asyncio
@respx.mock
async def test_get_status():
    logic = SongGenerationLogic(base_url="http://test")
    respx.get("http://test/api/gpu").respond(json={"total": 24000, "used": 8000})
    respx.get("http://test/api/model-server/status").respond(
        json={
            "running": True,
            "loaded": True,
            "model_id": "levo-v1",
            "loading": False,
            "active_count": 1,
            "queued_count": 0,
        }
    )

    status = await logic.get_status()
    assert status["vram_total"] == 24000
    assert status["vram_used"] == 8000
    assert status["model_loaded"] == "levo-v1"
    assert status["active_generations"] == 1
    assert status["queued_tasks"] == 0
    await logic.close()


@pytest.mark.asyncio
@respx.mock
async def test_generate_song():
    route = respx.post("http://test/api/generate")
    route.respond(
        json={
            "generation_id": "test-gen-123",
            "audio_url": "http://test/out.wav",
        }
    )
    respx.get("http://test/out.wav").respond(content=b"x" * 200)

    logic = SongGenerationLogic(base_url="http://test")
    request_data = {"lyrics": "Hello world", "genre": "Pop", "voice": "Female"}
    result = await logic.generate_song(request_data)
    assert "test-gen-123" in result
    assert route.called
    body = json.loads(route.calls[0].request.content.decode())
    assert body["sg2"]["model_repo"] == "tencent/SongGeneration"
    assert body["sg2"]["weights"] == "v2-large"
    assert body["sg2"]["max_length_seconds"] == 270
    assert body["sg2"]["torch_dtype"] == "bfloat16"
    assert body["sg2"]["codec"]["sample_rate_hz"] == 48000
    await logic.close()


@pytest.mark.asyncio
@respx.mock
async def test_cancel_generation():
    logic = SongGenerationLogic(base_url="http://test")
    respx.post("http://test/api/stop/test-gen-123").respond(status_code=200)

    success = await logic.cancel_generation("test-gen-123")
    assert success is True
    await logic.close()


@pytest.mark.asyncio
@respx.mock
async def test_unload_models():
    logic = SongGenerationLogic(base_url="http://test")
    respx.post("http://test/api/model-server/unload").respond(status_code=200)

    success = await logic.unload_models()
    assert success is True
    await logic.close()

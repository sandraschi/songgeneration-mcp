"""Stable Audio 3 bridge tests. Live generation is opt-in."""

from __future__ import annotations

import os
from pathlib import Path

import httpx
import pytest
import respx

from songgeneration_mcp.audio_studio import Sa3Client, prompt_from_generate_body, studio_result_to_payload


def test_prompt_from_generate_body_uses_lyrics_when_prompt_is_absent() -> None:
    text = prompt_from_generate_body(
        {"genre": "Pop", "mood": "Playful", "lyrics": "Mary had a little lamb.\nIts fleece was white as snow."}
    )
    assert text.startswith("Pop, Playful, Mary had a little lamb.")
    assert prompt_from_generate_body({"prompt": "tech house"}) == "tech house"


def test_studio_result_requires_a_real_file(tmp_path: Path) -> None:
    missing = studio_result_to_payload(
        {"model": "medium", "candidates": [{"path": str(tmp_path / "nope.wav")}]},
        "piano",
        8,
    )
    assert missing["success"] is False

    wav = tmp_path / "bed.wav"
    wav.write_bytes(b"RIFF")
    hit = studio_result_to_payload(
        {"model": "stable-audio-3-medium", "seconds": 8, "candidates": [{"path": str(wav)}]},
        "piano",
        30,
    )
    assert hit["success"] is True
    assert hit["backend"] == "audiostudio"
    assert hit["file"] == str(wav)
    assert hit["model"] == "stable-audio-3-medium"


@pytest.mark.asyncio
@respx.mock
async def test_sa3_health_and_generate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    wav = tmp_path / "out.wav"
    wav.write_bytes(b"RIFF....WAVE")
    monkeypatch.setenv("SONGGEN_SA3_URL", "http://127.0.0.1:11250")
    respx.get("http://127.0.0.1:11250/api/health").respond(json={"status": "ok", "engine": "tflite"})
    respx.post("http://127.0.0.1:11250/api/generate").respond(
        json={"success": True, "file": str(wav), "backend": "stable-audio-3 sm-music (local, CPU)", "cached": True}
    )

    client = Sa3Client()
    ok, body = await client.health()
    assert ok is True
    assert body["status"] == "ok"
    result = await client.generate("soft piano", 8)
    assert result["success"] is True
    assert result["backend"] == "sa3"
    assert result["cached"] is True
    assert Path(str(result["file"])).read_bytes().startswith(b"RIFF")


@pytest.mark.asyncio
@respx.mock
async def test_sa3_health_down() -> None:
    respx.get("http://127.0.0.1:9/api/health").mock(side_effect=httpx.ConnectError("refused"))
    ok, body = await Sa3Client("http://127.0.0.1:9").health()
    assert ok is False
    assert "refused" in str(body["detail"])


@pytest.mark.asyncio
async def test_live_sa3_short_clip() -> None:
    """One real WAV from the CPU service. Skipped unless SONGGEN_PROVE_SA3=1."""
    if os.getenv("SONGGEN_PROVE_SA3") != "1":
        pytest.skip("set SONGGEN_PROVE_SA3=1 to generate a real clip")
    client = Sa3Client("http://127.0.0.1:11250")
    ok, _body = await client.health()
    assert ok is True
    result = await client.generate("soft solo piano, slow, no vocals", 8)
    assert result["success"] is True
    path = Path(str(result["file"]))
    assert path.is_file()
    assert path.stat().st_size > 1000
    assert path.read_bytes()[:4] == b"RIFF"

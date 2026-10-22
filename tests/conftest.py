"""Keep pytest off the live Stable Audio processes unless a real run is requested."""

from __future__ import annotations

import os

import pytest


@pytest.fixture(autouse=True)
def _disable_live_stable_audio(monkeypatch: pytest.MonkeyPatch) -> None:
    raw = (os.getenv("SONGGEN_REAL_EXTERNAL", "") or "").strip().lower()
    if raw in {"1", "true", "yes", "on"}:
        return
    monkeypatch.setenv("SONGGEN_AUDIO_STUDIO_URL", "off")
    monkeypatch.setenv("SONGGEN_SA3_URL", "off")

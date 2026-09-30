# Troubleshooting — songgeneration-mcp

## Generation returns `success: false`
Read `backend_errors` in the response: per-backend strings (`lyria`, `acestep`,
`musicgen`, `stableaudio`, `studio`). Fix the one you want, others stay skipped.
Deep check: `GET /api/studio/test` (dir/HTTP/GPU/model-server/models).

## Lyria skipped
Needs GCP project + ADC: `GET /api/lyria/status` tells which half is missing.
No project → skipped silently by design (see `/api/v1/generate` hint).

## ACE-Step skipped
Needs `uv run acestep-api` on `:8001` (or `SONGGEN_ACESTEP_URL`).
Refused localhost fails fast; a blackholed host can take 30s per probe.

## Stable Audio gated
Needs HF token with access to `stabilityai/stable-audio-open-1.0`:
`GET /api/huggingface/status` verifies token + repo access (free calls).

## First runs are slow
MusicGen ~2GB, Stable Audio ~3GB, SG2 v2-large ~22GB VRAM + ~15GB disk
download on first use. `torch`/`transformers`/`diffusers` live in the `full`
extra (`uv sync --extra full`), not the base install.

## Port busy / stale server
`POST /api/shutdown` exits in ~500ms (NSSM-safe). Never taskkill; if you must,
verify a new PID owns the port afterwards.

## just recipes run in the wrong dir
Fixed 2026-10-01: every recipe keeps `Set-Location` and command on one `;` line
(just runs each line in its own shell).

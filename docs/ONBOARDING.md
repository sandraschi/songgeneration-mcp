# Onboarding — songgeneration-mcp

Get joy in ~15 minutes: generate your first bed, hear it, export it.

## What it is for
Prompt-to-music drafts (MusicGen/Stable Audio), full songs with vocals
(ACE-Step :8001, Studio SG2 :10930), stems, and handoffs to Plex/VirtualDJ/Reaper.

## What costs money / needs accounts
- Lyria (Google Vertex AI): pay-per-use cloud. Needs GCP project + `gcloud`
  ADC (`GET /api/lyria/status` tells you which half is missing). Skip it and
  everything local still works — start here, add Lyria later.
- Stable Audio Open: free local model but gated on Hugging Face. Needs a free
  HF account + token with repo access (`GET /api/huggingface/status` verifies).
- Everything else (MusicGen-small, Studio SG2 weights, ACE-Step): free
  open weights, just disk (~2GB / ~15GB / ~2GB) and a CUDA GPU for speed.

## Pitfalls
- First runs download gigabytes and look hung: watch `GET /api/studio/test`.
- SG2 v2-large wants ~22GB VRAM (bfloat16). OOM? Use v2-medium or `unload_models`.
- ACE-Step needs its own server: `uv run acestep-api` on `:8001`, else skipped.
- No local LLM? Chat + lyric help degrade honestly (503, never faked).

## Sanity check
1. `just serve`, open `:10884`, red onboarding button must be GONE.
2. Dashboard shows API OK, Studio ready, LLM count > 0.
3. Quick Generate a 10s bed → Listen → hear it. Done — onboarded.

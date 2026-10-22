# Backend Comparison

## Lyria 3 Pro (Google Vertex AI)

| | |
|---|---|
| **Quality** | Best — full songs with vocals |
| **Latency** | ~10-15s (API call) |
| **Cost** | Pay-per-use (Vertex AI pricing) |
| **Setup** | GCP project + `GOOGLE_CLOUD_PROJECT` env var |
| **Max duration** | ~60s (Pro), ~30s (Clip) |
| **Models** | `lyria-3-pro-preview`, `lyria-3-clip-preview` |

Best for: full songs, vocals, production-ready audio.

## audio-studio-mcp (Stable Audio 3, NVIDIA)

| | |
|---|---|
| **Quality** | Instrumental BGM, loops, sound effects. No vocals. |
| **Latency** | Medium model, warm, about 1.3 s for 20 s of music on an RTX 3060 (upstream). |
| **Cost** | Free locally. Weights under the Stability AI Community License. |
| **Setup** | Clone [audio-studio-mcp](https://github.com/kanaworksai-hue/audio-studio-mcp), run `install.ps1`, accept the gated Hugging Face license, start `--http`. |
| **Max duration** | 380 s (medium), 120 s (small). |
| **Contract** | MCP tool `generate_audio`. This server calls it at `SONGGEN_AUDIO_STUDIO_URL` (default `http://127.0.0.1:8765/mcp`). |

Full notes: [AUDIO_STUDIO.md](AUDIO_STUDIO.md).

## Stable Audio 3 CPU service (small models)

| | |
|---|---|
| **Quality** | Instrumental beds and one-shot effects from `sm-music` / `sm-sfx`. No vocals. |
| **Latency** | 60 s bed in 19.3 s on a Ryzen 9 5900X, CPU only (measured 2026-10-21). |
| **Cost** | Free locally. Same Community License on the weights. |
| **Setup** | `stable-audio-spike` service, port 11250. No API key. |
| **Max duration** | 120 s. |
| **Contract** | `POST /api/generate` with `{prompt, duration}` returns `{success, file}`. `SONGGEN_SA3_URL` overrides the base URL. |

This is the engine that can return a WAV on the current machine without a GPU session or a Hugging Face token.

## Stable Audio Open 1.0 (Stability AI)

| | |
|---|---|
| **Quality** | Good — instrumental loops, sound design |
| **Latency** | ~5-10s on RTX 4090 |
| **Cost** | Free (local) |
| **Setup** | `uv add diffusers soundfile` |
| **Max duration** | 47s |
| **License** | [Stability AI Community](https://huggingface.co/stabilityai/stable-audio-open-1.0/blob/main/LICENSE.md) |

Best for: drum loops, basslines, ambient textures, SFX. Not good at vocals.

## MusicGen-small (Meta)

| | |
|---|---|
| **Quality** | Fair — simple melodies, ambient |
| **Latency** | ~3-5s on RTX 4090 |
| **Cost** | Free (local) |
| **Setup** | `uv add transformers scipy` |
| **Max duration** | ~30s |
| **License** | MIT |

Best for: quick sketches, ambient pads, simple loops. Not good at complex arrangements.

## Studio API (SG2 / LeVo 2)

| | |
|---|---|
| **Quality** | Variable — depends on Studio setup |
| **Latency** | ~30-60s |
| **Cost** | Free (local model) |
| **Setup** | Separate SongGeneration-Studio install |
| **Max duration** | Configurable |
| **License** | MIT |

Best for: dual-track output (vocal + inst), structural tags.

## Recommendation

The API tries Lyria, ACE-Step, audio-studio-mcp, the SA3 CPU service, MusicGen, Stable Audio Open 1.0, then Studio, and returns whichever succeeds first. `GET /api/audio/status` shows whether the two Stable Audio 3 processes are up.

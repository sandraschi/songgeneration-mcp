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

For most users: `just install-all` gives you Lyria → Stable Audio → MusicGen in one command. The API tries them in order and returns whichever succeeds first.

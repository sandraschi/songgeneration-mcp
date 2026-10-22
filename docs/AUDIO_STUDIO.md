# Stable Audio 3 in songgeneration-mcp

Recorded 2026-10-21. This server had not produced a single audio file.
The README said the third backend was Stable Audio 3, installed with
`uv add --optional full stable-audio-3`. That package is not a dependency,
and the code path named `stableaudio` loads **Stable Audio Open 1.0**
through diffusers, then calls `.to("cuda")`. With the base install that
import fails. With the `full` extra and no CUDA it still fails. Lyria needs
a GCP project. ACE-Step needs a second server on port 8001. Studio SG2
needs SongGeneration-Studio on port 10930. Every step skipped, and the
response was `success: false`.

## What was added

`songgeneration_mcp.audio_studio` tries two local Stable Audio 3 processes
after Lyria and ACE-Step, and before MusicGen:

| Order | Backend id | Process | Default |
|---|---|---|---|
| 1 | `audiostudio` | [audio-studio-mcp](https://github.com/kanaworksai-hue/audio-studio-mcp) 0.2.1, streamable HTTP, tool `generate_audio` | `http://127.0.0.1:8765/mcp` |
| 2 | `sa3` | `stable-audio-spike` service, `POST /api/generate` | `http://127.0.0.1:11250` |

A refused connection is a skip. Set `SONGGEN_AUDIO_STUDIO_URL=off` or
`SONGGEN_SA3_URL=off` to force a skip. `GET /api/audio/status` reports
both without generating.

Stable Audio 3 writes instrumentals and effects. It does not sing. Lyrics
still need Lyria, ACE-Step, or Studio.

## audio-studio-mcp

Local BGM and sound effects. Tools: `generate_audio`, `edit_audio`
(variation, inpaint, continue), `process_audio` (loop, LUFS, fades,
WAV/OGG/FLAC), `unload_models`. Code is MIT. Weights stay under the
Stability AI Community License (commercial use under the published revenue
threshold). This fleet calls only `generate_audio`.

Windows uses the official PyTorch runtime. Flash Attention is optional;
upstream measured the medium model on an RTX 3060 12 GB at about 5.3 GB
VRAM, with 20 seconds of music in about 1.3 seconds once the model is warm.
Apple Silicon uses MLX. Intel Macs and AMD GPUs are unsupported.

This machine has an NVIDIA GeForce RTX 4090, 24 GB, so the medium model
fits. The weights are gated: accept the license on
`stabilityai/stable-audio-3-medium` and run `hf auth login` before
`install.ps1`. songgeneration does not vendor those weights.

Port 8765 is upstream's example. It is not reserved in
`mcp-central-docs/operations/WEBAPP_PORTS.md`. Claim a port before starting
`audio-studio-mcp --http`, then point `SONGGEN_AUDIO_STUDIO_URL` at
`http://127.0.0.1:<port>/mcp`.

```powershell
git clone https://github.com/kanaworksai-hue/audio-studio-mcp.git
cd audio-studio-mcp
powershell -ExecutionPolicy Bypass -File install.ps1
.venv\Scripts\audio-studio-mcp.exe --http 8765 --preload
```

## CPU service that already runs here

`stable-audio-spike` (evaluated the same day, Goliath, Ryzen 9 5900X) serves
the small TFLite models `sm-music` and `sm-sfx`. It does not use the GPU.
Measured: a 60 second bed in 19.3 seconds, peak working set 2.0 GB. The
service on port 11250 already speaks `{prompt, duration}` to `{success, file}`.
That is the backend that can return a WAV without a Hugging Face login.

```powershell
# from D:\Dev\repos\stable-audio-spike
service\start.ps1
```

`POST /api/v1/generate` with `{"prompt":"...","duration":8}` returns
`backend: "sa3"` and a `file` path when that service is up.

`POST /api/generate` (the lyrics form) uses the same chain. With the CPU
service up it returns an instrumental built from genre, mood, and the first
180 characters of the lyrics, and it does not call Studio. Studio still runs
when both Stable Audio 3 processes are down or set to `off`.

## What is still the old model

The `stableaudio` backend remains Stable Audio Open 1.0 (47 second cap,
gated repo, CUDA only). It is last among the local models. It is not
Stable Audio 3.

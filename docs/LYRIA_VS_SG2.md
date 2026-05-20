# LeVo 2 / SG2 vs Gemini Lyria 3 Pro — Technical & Creative Comparison

*Last updated: April 2026. Pricing and model SKUs change — always verify current Google terms.*

---

## Background: what are these?

**SongGeneration v2 (SG2 / LeVo 2)** is Tencent Music Entertainment's second-generation lyrics-conditioned music language model, released as open weights on Hugging Face (`tencent/SongGeneration`). It produces 48 kHz stereo audio, outputs dual tracks (vocal stem + instrumental stem) natively, and uses a discrete codec tokeniser over a transformer architecture. Inference runs locally via **SongGeneration-Studio**, a Gradio-based REST server that manages the model-server subprocess, GPU allocation, and generation queue.

**Gemini Lyria 3 Pro** is Google DeepMind's cloud music generation model, integrated into Gemini and accessible via Google AI Studio and the Gemini API. It is part of the Lyria lineage (Lyria was first published as a research model in 2023; Lyria RealTime and Lyria 3 Pro followed as commercial services). It is not available as open weights; inference is fully cloud-side.

---

## Architecture at a glance

| | **SG2 / LeVo 2** | **Gemini Lyria 3 Pro** |
| --- | --- | --- |
| **Model family** | Discrete-codec transformer (codec tokens → waveform via decoder) | Diffusion-based generative model (continuous latents) |
| **Training data** | Tencent Music catalog + curated Mandarin/pop corpus; broader genre coverage added in v2 | Google-licensed catalog; reportedly heavy Western pop/rock/classical corpus |
| **Conditioning** | Lyrics (structured sections), genre, mood, BPM, voice gender, optional 10s style-clone audio | Text prompt (free-form); style references via audio upload in some tiers |
| **Output format** | Dual track: `vocal.wav` + `inst.wav` (48 kHz stereo); optional mix-down | Single mixed stereo file (stem separation not native at generation time) |
| **Section control** | **SG2 length tags** — `[intro-short]`, `[inst-medium]`, `[outro-long]` etc. embedded in lyrics give per-section duration hints | Section control via prompt wording only; no structured timing tags |
| **Max length** | 270 seconds (4.5 min) default; configurable | Shorter by default; longer via API tiers (check current limits) |
| **Hardware** | RTX 3090/4090 class GPU locally (v2-large: ~22 GB VRAM in bfloat16) | Google datacentre; no local GPU required |
| **Latency** | 2–10 min on RTX 4090 depending on length and queue | Seconds to ~1–2 min cloud (network + queue dependent) |
| **Open weights** | Yes — `tencent/SongGeneration` on Hugging Face | No |
| **Cost model** | Hardware + electricity (upfront); no per-generation cloud meter | Per-generation cloud credits (commonly seen ~$0.08/track; **verify current pricing**) |

---

## Where each excels creatively

### SG2 strengths

**Structural precision.** The length tag system is the main differentiator for long-form composition. You can specify `[intro-short]` (0–10s), `[intro-medium]` (10–20s), `[inst-short]`, `[inst-medium]`, `[outro-short]`, `[outro-medium]` directly inside the lyric string. This gives the model explicit timing priors for section boundaries, which reduces the tendency toward generic 3:30 pop formats. For a 4-minute classical-influence track with a long orchestral intro and a rubato outro, SG2's structural tags are meaningfully better than prompt-wording alone.

**Stem separation at generation time.** The dual-track codec output (`vocal.wav` + `inst.wav`) is not post-hoc separation — the model outputs separate token streams for the two roles. This matters for post-production: you get clean stems without running a separate splitter (Demucs, Spleeter, etc.), and the stems stay phase-coherent with the mix.

**Non-Western and non-Top-40 priors.** Tencent's training corpus has heavier representation of Chinese pop (C-pop), traditional Chinese musical elements, and the particular production aesthetics of Mandarin-language commercial music. This is useful as a counterweight to models trained primarily on US/UK streaming catalogs, which tend to default to Anglo-American radio aesthetics.

**Style audio prompt (Style RAG).** Pass a ~10s WAV of a reference recording on the Studio host as `style_audio_prompt_path`. The model uses this as a style conditioning signal — useful for matching an existing artist's instrumental timbre or production color without text-describing it.

**Sovereignty and reproducibility.** Weights on disk; no internet call at inference time; generation is bit-for-bit reproducible from the same seed. Useful for professional scoring work where you need to re-render months later without depending on a cloud endpoint that may have changed.

### Lyria 3 Pro strengths

**Speed.** Cloud inference with no local GPU requirement; results in seconds to a couple of minutes rather than 2–10 minutes on a local GPU. For rapid creative iteration — "let me try 10 variants of this chorus" — the turnaround difference is significant.

**Polish on mainstream pop/rock/electronic.** Lyria's training data skews toward well-produced Western commercial music. If the target is a polished radio-pop or electronic track with contemporary production aesthetics, Lyria tends to sound more immediately "finished" than SG2 on the same prompt.

**Gemini ecosystem integration.** If you are already working in Gemini (writing, planning, coding with Gemini), Lyria fits naturally into that workflow via the same API key and SDK. The cost per track in typical Gemini tiers is low enough that it often makes sense as a quick first-pass tool.

**No hardware dependency.** Works from any machine with internet access; no GPU, no VRAM management, no model download.

---

## Practical guidance

**Use SG2 when:**
- You need clean stems without running a separate splitter.
- You need fine control over section timing/length.
- You are working in genres where non-Western or non-Top-40 priors help (C-pop, world, certain classical idioms).
- You need on-prem sovereignty (air-gapped env, reproducible renders, no per-song cost at scale).
- You want to clone a specific style from a reference clip.

**Use Lyria 3 Pro when:**
- You need fast iteration (many variants, quick sketches).
- Your target is mainstream Western pop/rock/electronic and you want immediate polish.
- You are in the Gemini ecosystem already and want low-friction integration.
- You do not have a suitable local GPU.

**Use both:** Many production workflows make sense with Lyria for rapid concept sketching (low latency, low cost per sketch) and SG2 for the final long-form renders with stem separation and structural precision.

---

## SG2 lyrics format reference

```
[intro-medium] ; [verse] Line one of verse. ; Line two of verse. ; [chorus] Chorus line one. ; Chorus line two. ; [inst-short] ; [verse] Second verse line. ; [outro-short]
```

- Use `;` as section separator.
- English lines should end with `.` before `;` (this MCP can auto-fix: `auto_fix_english_punctuation=True`).
- Length tags: `[intro-short]` (0–10s), `[intro-medium]` (10–20s), `[inst-short]`, `[inst-medium]`, `[outro-short]`, `[outro-medium]`.
- Section tags: `[verse]`, `[chorus]`, `[bridge]`, `[pre-chorus]`, `[post-chorus]`.

---

## Further reading

- Tencent SongGeneration paper and model card: [huggingface.co/tencent/SongGeneration](https://huggingface.co/tencent/SongGeneration)
- SongGeneration-Studio (inference server): [github.com/BazedFrog/SongGeneration-Studio](https://github.com/BazedFrog/SongGeneration-Studio)
- Gemini Lyria: [ai.google.dev](https://ai.google.dev) (check current API docs for pricing and feature availability)
- MCP resource: `docs://lyria-vs-sg2` — available in any Claude session with songgeneration-mcp loaded
- MCP tool: `help(topic="lyria")`

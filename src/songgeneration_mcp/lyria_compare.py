"""LeVo 2 (SG2) vs Gemini Lyria 3 Pro — text for MCP resource and help.

The canonical comparison doc lives at ``docs/LYRIA_VS_SG2.md``.
``get_lyria_vs_sg2_text()`` reads that file when running from the repo;
the constant below is a trimmed fallback for installed-wheel deployments.
"""

from __future__ import annotations

from pathlib import Path

# Trimmed fallback for installed-wheel deployments (repo docs/LYRIA_VS_SG2.md is authoritative).
LYRIA_VS_SG2_MARKDOWN = """\
# LeVo 2 (SG2) vs Gemini Lyria 3 Pro

*Pricing and model SKUs change — always verify current Google terms.*

## TL;DR

- **Gemini Lyria 3 Pro** (2026): Cloud music generation, Google ecosystem, fast iteration.
  Often ~$0.08/track in typical Gemini credits (**verify live pricing**). Best for rapid sketches
  and mainstream Western pop/rock/electronic.
- **SongGeneration v2 / LeVo 2 (SG2)**: Open-weight, local inference via SongGeneration-Studio.
  No per-song cloud meter. Dual-track output (vocal.wav + inst.wav) at generation time.
  Strong for classical phrasing, rubato, orchestral articulation, and long-form structural control
  via SG2 length tags.

## Key differences

| | SG2 / LeVo 2 | Gemini Lyria 3 Pro |
| --- | --- | --- |
| **Weights** | Open (Hugging Face) | Closed, cloud-only |
| **Cost model** | Hardware + electricity | Per-generation cloud credits |
| **Stems** | vocal.wav + inst.wav native | Single mix (no native stems) |
| **Section control** | Length tags in lyrics | Prompt wording only |
| **Training priors** | Tencent catalog, C-pop | Google-licensed, Western pop/rock |
| **Latency** | 2–10 min (RTX 4090) | Seconds to ~2 min (cloud) |
| **VRAM** | ~22 GB (v2-large, bfloat16) | None (cloud) |

## When to pick which

Prefer SG2 when you need stems, structural timing control, non-Western priors, on-prem
sovereignty, or style-clone from a reference clip (style_audio_prompt_path).

Prefer Lyria 3 Pro when you need fast iteration, mainstream Western polish, or Gemini
ecosystem integration without a local GPU.

Many workflows use both: Lyria for rapid concept sketches, SG2 for final long-form renders.

Full doc: docs/LYRIA_VS_SG2.md in the repo, or MCP resource docs://lyria-vs-sg2.
"""


def get_lyria_vs_sg2_text() -> str:
    """Return comparison doc: prefer repo ``docs/LYRIA_VS_SG2.md`` when running from source."""
    here = Path(__file__).resolve()
    repo_docs = here.parent.parent.parent / "docs" / "LYRIA_VS_SG2.md"
    if repo_docs.is_file():
        return repo_docs.read_text(encoding="utf-8")
    return LYRIA_VS_SG2_MARKDOWN

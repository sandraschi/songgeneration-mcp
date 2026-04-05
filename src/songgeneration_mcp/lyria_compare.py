"""LeVo 2 (SG2) vs Gemini Lyria 3 Pro — text for MCP resource and help."""

from __future__ import annotations

from pathlib import Path

# Canonical copy for wheels / installed packages (repo `docs/LYRIA_VS_SG2.md` should match).
LYRIA_VS_SG2_MARKDOWN = "\n".join(
    [
        "# LeVo 2 (SG2) vs Gemini Lyria 3 Pro",
        "",
        "This note is for **product and creative context**—not a benchmark suite. "
        "Pricing and SKUs change; always confirm **current** Google in-app and API terms.",
        "",
        "## TL;DR",
        "",
        "- **Gemini Lyria 3 Pro** (2026): Cloud music generation inside Google's AI push—often "
        "**very affordable per track** (many users see on the order of **~$0.08 per song** in "
        "typical Gemini credit economics; **verify live pricing**). Great when you want speed, "
        "polish, and tight Gemini integration.",
        "- **SongGeneration v2 / LeVo 2 (SG2)**: **Open-weight**, **local** inference via "
        "SongGeneration-Studio—**no per-song cloud meter**. Strong where **classical phrasing**, "
        "**rubato**, and **instrumental** nuance matter; SG2's **length-tagged** sections help "
        "long-form structure.",
        "",
        "## Why both matter",
        "",
        "Commercial US-led music APIs have shaped default \"radio\" aesthetics worldwide. "
        "A **Chinese research champion** in open music LM space is a useful **counterweight**: "
        "different priors, more room for **non–Top-40** idioms, and **on-prem** control. "
        "That does **not** negate the value of Google's ecosystem—many of us **like** the "
        "Google AI push **and** still run local models for sovereignty, repertoire, or scoring.",
        "",
        "## When to pick which",
        "",
        "| Prefer Lyria 3 Pro | Prefer SG2 (this stack) |",
        "| --- | --- |",
        "| You live in Gemini all day | You want **weights on disk** / air-gapped |",
        "| Optimize $/track (cloud) | Optimize **repetition** + **fine section control** |",
        "| You need instant share-to-YouTube loops | You need **orchestral** / **classical** "
        "articulation experiments |",
        "",
    ]
)


def get_lyria_vs_sg2_text() -> str:
    """Return comparison doc: prefer repo `docs/LYRIA_VS_SG2.md` when running from source."""
    here = Path(__file__).resolve()
    repo_docs = here.parent.parent.parent / "docs" / "LYRIA_VS_SG2.md"
    if repo_docs.is_file():
        return repo_docs.read_text(encoding="utf-8")
    return LYRIA_VS_SG2_MARKDOWN

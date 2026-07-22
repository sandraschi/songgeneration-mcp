"""SongGeneration v2 (LeVo 2 / SG2) helpers — lyrics rules and tag reference."""

from __future__ import annotations

import re

# Length-sensitive structural markers (embed in lyrics text for SG2).
SG2_STRUCTURAL_TAGS_REFERENCE = """
SG2 length-sensitive section markers (use inside lyrics):
- [intro-short]  (0–10s)    [intro-medium]  (10–20s)
- [inst-short]                 [inst-medium]
- [outro-short]               [outro-medium]

Dual-track codec output: vocal.wav + inst.wav (48 kHz stereo tokens); optional mix-down.
"""


def normalize_sg2_english_before_semicolons(
    lyrics: str, *, auto_fix: bool
) -> tuple[str, list[str]]:
    """Enforce SG2 English rule: each English line before ';' should end with '.'

    Example: `[verse] The strings arise in the Konzerthaus hall. ; [chorus]`

    If auto_fix is True, appends '.' to segments that look like English prose and
    are followed by another section (semicolon-separated).
    """
    notes: list[str] = []
    if ";" not in lyrics:
        return lyrics, notes

    parts = lyrics.split(";")
    englishish = re.compile(r"[A-Za-z]{3,}")
    out_parts: list[str] = []

    for i, raw in enumerate(parts):
        segment = raw
        is_followed = i < len(parts) - 1
        if not is_followed:
            out_parts.append(segment)
            continue

        stripped_right = segment.rstrip()
        if not stripped_right.strip():
            out_parts.append(segment)
            continue

        core = stripped_right.strip()
        if englishish.search(core) and not re.search(r"[.!?][\"']?\s*$", core):
            if auto_fix:
                fixed_core = core + "."
                lead_len = len(segment) - len(segment.lstrip())
                lead = segment[:lead_len]
                trail = segment[len(stripped_right) :] if len(segment) > len(stripped_right) else ""
                segment = lead + fixed_core + trail
                notes.append(
                    "SG2: appended '.' before ';' for English segment (LeVo 2 punctuation rule)."
                )
            else:
                notes.append(
                    "SG2: English segment before ';' should end with '.' "
                    "(enable auto_fix_english_punctuation to repair)."
                )
        out_parts.append(segment)

    return " ; ".join(out_parts), notes

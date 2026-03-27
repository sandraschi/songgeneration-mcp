# PRD — songgeneration-mcp (LeVo 2 / SG2)

**Repository:** [github.com/sandraschi/songgeneration-mcp](https://github.com/sandraschi/songgeneration-mcp)

## Purpose

`songgeneration-mcp` exposes Tencent **SongGeneration v2** (**LeVo 2**, **SG2**) to MCP clients via a **SongGeneration-Studio** HTTP backend. It is the control plane for lyrics-conditioned generation, SG2 structural tags, dual-track codec output, and optional style cloning (short audio prompt).

## Positioning

- **Local-first**: Open-weight stack can run on your hardware (VRAM permitting); no mandatory cloud lock-in for inference.
- **Musical nuance**: Strong fit for **classical**, **rubato**, and **instrumental** articulation where timing and section length matter; SG2 adds **length-sensitive** markers (`[intro-short]`, `[inst-medium]`, etc.).
- **Ecosystem balance**: Offers a credible **non–US-default** research lineage (Tencent / Tsinghua ecosystem) alongside Anglophone-first commercial music APIs—without dismissing them (many teams, including Google’s, push the field forward).

## Competitive landscape (March 2026)

| Dimension | LeVo 2 / SG2 (this MCP) | Google **Gemini Lyria 3 Pro** |
| --- | --- | --- |
| Deployment | Self-hosted Studio + GPU; **local** inference | **Cloud** via Gemini / Google AI stack |
| Cost model | Capex: GPU + electricity; no per-song meter from Google | **Low per-track** consumer pricing in Gemini (often cited around **~$0.08 per song** on typical credit tiers; **verify in-app**—public numbers change) |
| Strengths | Classical / rubato-friendly phrasing, explicit SG2 section control, dual-track tokens | Tight integration with Gemini workflows, accessibility, rapid iteration for creators |
| Tradeoffs | Setup, VRAM (~22 GB class for Large in **bfloat16**), ops burden | Network dependency, vendor terms, less direct “weights on disk” control |

**Opinionated note (fleet)**: Use **Lyria 3 Pro** when you want cheap, polished cloud tracks inside Google’s AI push. Use **SG2** when you want **local**, **section-precise**, and **orchestral-friendly** behavior—or to avoid a single region’s product defaults dominating your catalogue.

## Goals

1. Default to **`tencent/SongGeneration`** + **`v2-large`**, **270 s** max length, **bfloat16**.
2. Encode SG2 rules (lyrics punctuation before `;`, structural tags) in tools, prompts, and resources.
3. Request **48 kHz** stereo **dual-track** output (`vocal.wav`, `inst.wav`) with optional mix-down.
4. Support **~10 s** style audio prompt path for Style RAG when Studio implements it.
5. Keep Studio transport flexible: local by default (**`http://localhost:10930`**) with explicit support for remote/cloud Studio URLs.
6. Ensure generated media is usable locally: persist/playback from local files, optional MP3 transcode, and export path to Plex-managed folders.
7. Support cross-MCP DJ handoff: one-click transfer to VirtualDJ deck with deterministic pre-mix actions (load, optional play, optional sync-to-master, optional cue-at-start).

## Non-goals

- Replacing the Studio backend (this MCP is a **client**).
- Promising feature parity with every cloud API (pricing and models move monthly).
- Hiding deployment mode: local vs remote Studio must stay explicit in settings and status surfaces.

## References

- Resource `sg2://structural-tags` — SG2 marker cheat sheet.
- Resource `docs://lyria-vs-sg2` — short comparison with Gemini Lyria 3 Pro.

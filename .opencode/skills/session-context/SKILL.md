---
name: session-context
description: Lightweight songgeneration session start prompt - backends, diagnostics, skill pointer
---

## Session Context (songgeneration-mcp)

Backends tried in order: Lyria (cloud/GCP) → ACE-Step (:8001) → MusicGen → Stable Audio → Studio SG2 (:10930).

**Before starting work:**
1. Check state: `GET /api/v1/diagnostics`
2. Confirm weights: `list_models`

**At end of work:**
- `unload_models` to free VRAM
- Never invent model names

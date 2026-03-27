# Changelog

## Unreleased

- **LeVo 2 / SG2**: Default `tencent/SongGeneration` + `v2-large`; `max_length_seconds` 270; `bfloat16`; dual-track (`vocal.wav` / `inst.wav`); optional 10s style prompt path.
- **Docs**: `docs/PRD.md`, `docs/LYRIA_VS_SG2.md`; MCP resource `docs://lyria-vs-sg2`; help compares SG2 to **Gemini Lyria 3 Pro** (cloud pricing vs local fit).
- **Upstream**: Canonical GitHub — [sandraschi/songgeneration-mcp](https://github.com/sandraschi/songgeneration-mcp).
- **Webapp** (`web_sota/`): Standard pages — Local LLM, Chat, Logger, Help (tabbed SG2 / Lyria / env / MCP resources); `vite` port **10884** aligned with `start.ps1`; docs in `web_sota/README.md` and `web_sota/docs/`.
- **Logging:** `log_buffer.py` + `GET/POST /api/logs` serve real Python `logging` lines (no UI stubs); Dashboard/Status/Logger consume `/api/health` and `/api/logs`.
- **Studio URL targeting**: `studio_url` is now persisted in app settings (`GET/POST /api/settings`) with env overrides (`SONGGENERATION_STUDIO_URL` / `SONGGEN_STUDIO_BASE_URL`), plus `GET /api/studio/info` for UI link + reachability.
- **Default Studio port**: switched to non-colliding `http://localhost:10930`.
- **Listen UX**: added dedicated `Listen` page with playlist-style navigation, auto-advance, and single/all export actions.
- **Local media pipeline**: source audio URLs are downloaded to local storage when reachable and served via `/api/media/*`; API keeps `source_audio_urls` for traceability.
- **MP3 + Plex**: optional MP3 transcode in generate flow, repository persistence of `mp3_urls`, and Plex export endpoint (`POST /api/export/plex`) with configurable destination.
- **VirtualDJ deck handoff**: listen flow supports deck selection + optional `auto_play`, `sync_to_master`, and `cue_at_start` in `POST /api/export/virtualdj`; response now returns `loaded` / `played` / `synced` / `cued` details.
- **DJ workflow UI**: Listen page adds explicit toggles for sync and cue behavior to make deck prep predictable before live mixing.

# Configuration — songgeneration-mcp

All settings live in `src/songgeneration_mcp/settings_store.py` (JSON file),
editable via `GET/POST /api/settings` (HF token is write-only, never echoed)
or environment variables. `studio_url` hot-reloads without restart.

| Setting | Env var | Default | Purpose |
|---|---|---|---|
| `studio_url` | `SONGGENERATION_STUDIO_URL` / `SONGGEN_STUDIO_BASE_URL` | `http://localhost:10930` | SongGeneration-Studio server |
| `studio_dir` | `SONGGEN_STUDIO_DIR` | unset | Studio checkout path (for auto-boot) |
| `google_cloud_project` | `GOOGLE_CLOUD_PROJECT` | unset | Enables Lyria backend |
| `lyria_model` | `SONGGEN_LYRIA_MODEL` | `lyria-002` | Lyria model id |
| `hf_token` | `HF_TOKEN` | unset | Gated Stable Audio Open access |
| `plex_export_dir` | `SONGGEN_PLEX_EXPORT_DIR` | unset | Plex export target |
| `virtualdj_drop_dir` / `virtualdj_api_base` | — | unset / `:10877` | VirtualDJ handoff |
| `reaper_drop_dir` / `reaper_api_base` | — | unset / `:10797` | Reaper handoff |
| `acestep` | `SONGGEN_ACESTEP_URL`, `ACESTEP_API_KEY` | `http://localhost:8001` | ACE-Step 1.5 server |

Ports: REST `10885`, webapp `10884`, Studio `10930`, ACE-Step `8001`.
LLM probes: `OLLAMA_BASE_URL` (`:11434`), `LMSTUDIO_BASE_URL` (`:1234`).
Onboarding status: `GET /api/lyria/status`, `/api/huggingface/status`, `/api/llm/onboarding`.

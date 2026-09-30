# Tools — songgeneration-mcp

## MCP tools (`src/songgeneration_mcp/mcp_server.py`)
| Tool | Kind | Description |
|---|---|---|
| `generate_song` | portmanteau | Lyrics + genre/mood/BPM/voice → Studio SG2 task (dual-track `vocal.wav`/`inst.wav`, SG2 length tags, optional Style RAG) |
| `list_models` | read | Models exposed by Studio |
| `get_status` | read | GPU VRAM + queue markdown report |
| `cancel_generation` | mutating | Stop a task by id |
| `unload_models` | mutating | Free VRAM |
| `diagnostics` | read | System diagnostic markdown |
| `shutdown` | destructive | Exit process in ~300ms (NSSM-safe) |
| `help` | read | Levels + `topic="lyria"` comparison |

Prompts: `generate-song`, `lyric-assistant`. Resources: `api://song-request-schema`,
`sg2://structural-tags`, `docs://lyria-vs-sg2`, `system://gpu-status`.

## REST (port 10885, full list: `GET /api/capabilities`)
`POST /api/generate` (Lyria→ACE→MusicGen→StableAudio, Studio fallback),
`POST /api/v1/generate` (quick: `{prompt, duration, lyrics?, model?}`),
`GET /api/v1/diagnostics`, `GET /api/status`, `POST /api/shutdown`,
`/api/studio/*` (status/test/info), `/api/lyria/status`, `/api/huggingface/status`,
`/api/songs`, `/api/settings`, `/api/llm/*` (providers/models/discover/onboarding),
`/api/export/*` (plex/virtualdj/reaper), `/api/media/*`, `/api/logs`.

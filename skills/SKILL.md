# SongGeneration Skill

Use for any music-generation task in this repo. Workflow first, tools second.

## Generate (long-form, stems, timing control)
1. `list_models` - confirm Studio has weights loaded.
2. `generate_song` - lyrics use `;` separators, English lines end with `.`
   before `;`, embed length tags: `[intro-short/medium]`, `[inst-short/medium]`,
   `[outro-short/medium]`. `separate_stems=true` gives `vocal.wav` + `inst.wav`.
3. `get_status` - watch VRAM; `unload_models` when done.

## Draft fast, render final
- Quick beds: `POST /api/v1/generate` `{prompt, duration}` tries
  Lyria → ACE-Step → MusicGen → Stable Audio, Studio last resort.
- Chat: `POST /api/ai/chat` `{message, system_prompt?, context?}` answers via
  local Ollama/LM Studio with this skill prepended.

## Exports
Plex / VirtualDJ / Reaper via `POST /api/export/*` with `repo_id`.
Never invent model names - ask `list_models` or `GET /api/v1/diagnostics`.

# SongGeneration MCP — web dashboard

Glass-style React UI for the fleet: **Vite + React 19** on port **10884**, MCP HTTP on **10885** (see `start.ps1`).

## Start (Windows)

From `web_sota`:

```powershell
.\start.ps1
```

**SongGeneration-Studio** is a **different repository** than `songgeneration-mcp` — clone **[github.com/BazedFrog/SongGeneration-Studio](https://github.com/BazedFrog/SongGeneration-Studio)** (see root [README](../README.md) § *SongGeneration-Studio (not in this repo)*). Documented default path: **`D:\Dev\repos\external\SongGeneration-Studio`** (matches `SONGGEN_STUDIO_DIR` / `start.ps1` when unset). Use a remote Studio URL in Settings if you do not run Studio locally.

Or manually: `npm install` then `npm run dev -- --port 10884 --host 127.0.0.1`, and from repo root run the same uvicorn line as in `start.ps1`. For local inference, Studio must listen on **10930** unless you change the URL — `start.ps1` tries to launch it with `uv run --directory <studio> python main.py …` when `main.py` exists under that directory.

## Pages (standard)

| Route | Purpose |
| --- | --- |
| `/` | Home |
| `/tools` | MCP tools summary |
| `/status` | Health-style panel |
| `/apps` | App hub |
| `/local-llm` | Local inference & env vars |
| `/chat` | Chat surface (wire to your agent) |
| `/logger` | Process log buffer (`/api/logs` → real Python logging) |
| `/help` | Short intro + **tabs** for SG2, Lyria compare, env, MCP resources |
| `/settings` | Settings placeholder |

More detail: [docs/PAGES.md](docs/PAGES.md) and [docs/README.md](docs/README.md).

## Stack

Tailwind, Radix, `react-router`, lucide icons. Dark layout matches fleet **WEBAPP_STANDARDS** (ports **10884** / **10885**).

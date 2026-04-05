# SongGeneration MCP — web dashboard

Glass-style React UI for the fleet: **Vite + React 19** on port **10884**, MCP HTTP on **10885** (see `start.ps1`).

## Start (Windows)

From `web_sota`:

```powershell
.\start.ps1
```

Or manually: `npm install` then `npm run dev -- --port 10884 --host 127.0.0.1`, and run the Python backend from repo root as in `start.ps1`.

## Pages (standard)

| Route | Purpose |
| --- | --- |
| `/` | Overview |
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

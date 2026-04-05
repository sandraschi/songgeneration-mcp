# Page map

All routes use the shared `AppLayout` (sidebar + top bar).

## Overview (`/`)

KPI cards and a compact log preview. Quick links to **Local LLM**, **Chat**, **Logger**, **Help**.

## Tools (`/tools`)

Lists MCP tool concepts for operators (portmanteau tools, generation flow).

## Status (`/status`)

Service / bridge style status (extend with real `/api` calls when the backend exposes them).

## App Hub (`/apps`)

Fleet / integration hub placeholder.

## Local LLM (`/local-llm`)

Explains **local** SongGeneration / LeVo 2 inference vs cloud APIs, lists **environment variables** for Studio + MCP, and links to GitHub docs.

## Chat (`/chat`)

UI shell for **natural-language → MCP tool** workflows. Connect your agent or host SSE/WebSocket here.

## Logger (`/logger`)

Reads the **Python `logging` ring buffer** from this MCP HTTP process via `GET /api/logs` (polls every few seconds). `POST /api/logs/clear` empties that buffer (operator action). Configure size with env `SONGGEN_LOG_BUFFER_LINES` (default 500).

## Help (`/help`)

**Quick start** card plus **tabs**:

1. **SG2 & LeVo 2** — structural tags, English punctuation rule, defaults.
2. **vs Lyria 3 Pro** — deployment/cost/fit table (verify Google pricing live).
3. **Environment** — common env vars.
4. **MCP resources** — `api://`, `sg2://`, `docs://`, `system://` URIs.

## Settings (`/settings`)

UI preferences / future API keys (placeholder).

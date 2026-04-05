# SongGeneration MCP

**Repository:** [github.com/sandraschi/songgeneration-mcp](https://github.com/sandraschi/songgeneration-mcp)

MCP-Server für **Tencent SongGeneration v2** (**LeVo 2** / **SG2**) über **SongGeneration-Studio**. Unterstützt SG2-Struktur-Tags, Dual-Track-Ausgabe (`vocal.wav` + `inst.wav`) und optionalen Stil-Klon-Prompt.

## Einordnung: SG2 vs. Gemini Lyria 3 Pro (~März 2026)

| | **LeVo 2 / SG2** (dieser MCP) | **Gemini Lyria 3 Pro** |
| --- | --- | --- |
| **Betrieb** | **Lokal** (Studio + eigene GPU) | **Cloud** (Gemini) |
| **Kosten** | Hardware/Strom; keine Cloud-Gebühr pro Song | oft **~0,08 $ pro Song** in typischen Gemini-Credits (**Preis im App prüfen**) |
| **Stärken** | **Klassik**, **Rubato**, **Instrumental**; SG2-Längen-Tags | Schnelle Iteration, **Google-AI**-Ökosystem |

**Kurz:** Lyria ist günstig und bequem in der Cloud; SG2 ist offen gewichtet und präzise in den Abschnitten—ein sinnvolles **Gegengewicht** zu stark **US-zentrierten** Musik-KI-Defaults (ohne die Google-Push-Strategie pauschal zu kritisieren).

Ressourcen: `docs://lyria-vs-sg2`, `help(topic="lyria")`, Dateien `docs/LYRIA_VS_SG2.md`, `docs/PRD.md`.

## SG2-Defaults

- Repo: `tencent/SongGeneration`, Gewichte: `v2-large`
- Max. Länge: 270 s, `bfloat16`, 48 kHz Dual-Track

## Installation

```bash
pip install -e .
```

## Verwendung

```bash
python -m songgeneration_mcp.mcp_server
```

## Web-Dashboard

React-UI unter **`web_sota/`** (Ports **10884**/ **10885**, Start: `web_sota\start.ps1`): u. a. **Local LLM**, **Chat**, **Logger**, **Help** mit Tab-Doku. Kurz: `web_sota/README.md`, Routen: `web_sota/docs/PAGES.md`.

## Studio-Ziel (lokal oder remote)

- Standard: **`http://localhost:10930`** (kollisionsarmer Port im Fleet-Bereich).
- Override per Env:
  - `SONGGENERATION_STUDIO_URL`
  - `SONGGEN_STUDIO_BASE_URL`
- Einstellungen + APIs:
  - `GET/POST /api/settings` (inkl. `studio_url`, `plex_export_dir`)
  - `GET /api/studio/info` (Erreichbarkeit + UI-Link)

## Claude Desktop

```json
{
  "mcpServers": {
    "songgeneration-mcp": {
      "command": "python",
      "args": ["-m", "songgeneration_mcp", "mcp_server"],
      "cwd": "/ihr/pfad/zu/songgeneration-mcp"
    }
  }
}
```

## Werkzeuge & Ressourcen

- Tools: `list_models`, `generate_song`, `get_status`, `cancel_generation`, `unload_models`, `diagnostics`, `help`
- `api://song-request-schema`, `sg2://structural-tags`, `system://gpu-status`, `docs://lyria-vs-sg2`

## Lizenz

Siehe LICENSE.

## Autor

MCP Studio (Wien)

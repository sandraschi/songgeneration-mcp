"""One-off debug: POST Studio /api/generate with MCP-built body, print response."""

import httpx
from songgeneration_mcp.logic import SongGenerationLogic

data = {
    "title": "Mary Had a Little Lamb",
    "genre": "Nursery",
    "mood": "Playful",
    "lyrics": "Mary had a little lamb. ; [chorus] Its fleece was white as snow.",
    "transcode_to_mp3": False,
}
l = SongGenerationLogic("http://127.0.0.1:10930")
sr, _, _ = l._build_studio_request(data)
r = httpx.post("http://127.0.0.1:10930/api/generate", json=sr, timeout=30)
print("status", r.status_code)
print(r.text[:4000])

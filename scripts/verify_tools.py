"""Verify rewritten MCP tools: names, annotations, help output (in-process client)."""
import asyncio

from fastmcp import Client
from songgeneration_mcp import mcp_server as m


async def main() -> None:
    async with Client(m.app) as client:
        tools = await client.list_tools()
        for t in tools:
            print("-", t.name, "| annotations:", t.annotations)
        res = await client.call_tool("diagnostics", {})
        print("diagnostics head:", str(res.content[0].text).splitlines()[0])
        res2 = await client.call_tool("help", {"level": "basic"})
        print("help head:", str(res2.content[0].text).splitlines()[0:2])


asyncio.run(main())

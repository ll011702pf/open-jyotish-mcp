"""用真实 MCP 客户端连 streamable-http 端点，验证远程部署可用性。"""
from __future__ import annotations

import json
import os
import sys

import anyio
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = os.environ.get("MCP_URL", "http://127.0.0.1:8791/mcp")


async def main() -> int:
    async with (
        streamable_http_client(URL) as (reader, writer),
        ClientSession(reader, writer) as session,
    ):
            await session.initialize()
            tools = await session.list_tools()
            print("TOOLS:", [t.name for t in tools.tools])

            place = await session.call_tool("resolve_place", {"query": "Baotou"})
            print("PLACE:", json.loads(place.content[0].text)["results"][0]["label"])

            res = await session.call_tool("compute_chart", {
                "birth_date": "1992-08-31", "birth_time": "12:00:00",
                "timezone": "Asia/Shanghai", "latitude": 40.58278,
                "longitude": 110.04611, "city": "Baotou", "title": "waka",
            })
            d = json.loads(res.content[0].text)
            print("AYANAMSHA:", d["meta"]["ayanamsha_value"], "(JHora 22.61944)")
            print("LAGNA:", d["lagna"]["sign"], d["lagna"]["degree_in_sign"],
                  "(JHora Libra 24.3817)")
            print("SUN:", d["planets"][0]["sign"], round(d["planets"][0]["degree_in_sign"], 4))
            print("ENGINE:", d["engine"])
            print("OK: remote streamable-http works")
    return 0


if __name__ == "__main__":
    sys.exit(anyio.run(main))

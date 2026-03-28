#!/usr/bin/env python3
"""Discover available tools on a Composio MCP server."""

import asyncio
import json
import os
import sys


async def discover_tools():
    """Discover tools via Streamable HTTP MCP protocol."""
    import httpx

    base = "https://backend.composio.dev/tool_router/trs_0xJb8Y4nexHE/mcp"
    headers = {
        "x-api-key": os.environ.get("COMPOSIO_API_KEY", ""),
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }

    tools_payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {}
    }

    async with httpx.AsyncClient(timeout=30) as client:
        async with client.stream("POST", base, json=tools_payload, headers=headers) as resp:
            full_text = ""
            async for chunk in resp.aiter_text():
                full_text += chunk

            for line in full_text.split('\n'):
                if line.startswith('data:'):
                    data = json.loads(line[5:].strip())
                    if "result" in data and "tools" in data["result"]:
                        tools = data["result"]["tools"]
                        print(f"Found {len(tools)} tools on Composio MCP server:\n")
                        print("=" * 80)
                        for i, t in enumerate(tools, 1):
                            name = t['name']
                            desc = (t.get('description') or 'N/A').strip()
                            params = t.get('inputSchema', {}).get('properties', {})
                            required = t.get('inputSchema', {}).get('required', [])

                            print(f"\n{i}. {name}")
                            print(f"   Description: {desc}")
                            print(f"   Parameters:")
                            for pname, pinfo in params.items():
                                req_mark = " (REQUIRED)" if pname in required else ""
                                ptype = pinfo.get('type', '?')
                                pdesc = (pinfo.get('description') or '').strip().split('\n')[0][:120]
                                print(f"     - {pname} ({ptype}){req_mark}: {pdesc}")
                            print("-" * 80)
                        return


if __name__ == "__main__":
    asyncio.run(discover_tools())

#!/usr/bin/env python3
"""Search for all Reddit tools on Composio MCP and get their full schemas."""

import asyncio
import json
import re

BASE = "https://backend.composio.dev/tool_router/trs_0xJb8Y4nexHE/mcp"
HEADERS = {
    "x-api-key": "ak_8E4M5xorY8qgqNN7W5u-",
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}


async def mcp_call(client, method, params, req_id=1):
    payload = {
        "jsonrpc": "2.0",
        "id": req_id,
        "method": method,
        "params": params,
    }
    async with client.stream("POST", BASE, json=payload, headers=HEADERS) as resp:
        full_text = ""
        async for chunk in resp.aiter_text():
            full_text += chunk

    for line in full_text.split("\n"):
        if line.startswith("data:"):
            data = json.loads(line[5:].strip())
            if "result" in data:
                return data["result"]
            if "error" in data:
                return {"error": data["error"]}
    return {"raw": full_text}


def extract_slugs_from_result(result):
    slugs = set()
    content = result.get("content", [])
    for item in content:
        if item.get("type") == "text":
            try:
                parsed = json.loads(item["text"])
                if isinstance(parsed, dict):
                    data = parsed.get("data", parsed)
                    results = data.get("results", [data])
                    if not isinstance(results, list):
                        results = [results]
                    for r in results:
                        for key in ("primary_tool_slugs", "related_tool_slugs"):
                            for slug in r.get(key, []):
                                if slug and "REDDIT" in slug.upper():
                                    slugs.add(slug)
                        for step in r.get("recommended_plan_steps", []):
                            for m in re.finditer(r'(REDDIT_[A-Z_]+[A-Z0-9])', step):
                                slugs.add(m.group(1))
            except json.JSONDecodeError:
                pass
    return slugs


async def main():
    import httpx

    queries = [
        "reddit",
        "reddit comment",
        "reddit post",
        "reddit subreddit",
        "reddit vote",
        "reddit message",
        "reddit user",
        "reddit flair",
        "reddit search",
        "reddit subscribe",
        "reddit karma",
        "reddit save",
        "reddit report",
        "reddit block",
        "reddit moderation",
        "reddit hot new rising",
    ]

    all_slugs = set()

    async with httpx.AsyncClient(timeout=60) as client:
        print("=" * 80)
        print("STEP 1: Searching for Reddit tools")
        print("=" * 80)

        for i, q in enumerate(queries):
            result = await mcp_call(
                client, "tools/call",
                {"name": "COMPOSIO_SEARCH_TOOLS", "arguments": {"query": q}},
                req_id=i + 1,
            )
            slugs = extract_slugs_from_result(result)
            if slugs - all_slugs:
                print(f"  '{q}' -> new: {sorted(slugs - all_slugs)}")
            all_slugs.update(slugs)

        # Remove obviously invalid ones
        all_slugs.discard("REDDIT_NOEXIST")
        all_slugs.discard("REDDIT_NOTALLOWED")

        print(f"\nTotal unique Reddit tool slugs: {len(all_slugs)}")
        for s in sorted(all_slugs):
            print(f"  - {s}")

        # Step 2: Get schemas using tool_slugs (array)
        print(f"\n{'=' * 80}")
        print("STEP 2: Getting schemas via COMPOSIO_GET_TOOL_SCHEMAS (tool_slugs as array)")
        print("=" * 80)

        # Try getting all at once first
        slug_list = sorted(all_slugs)
        result = await mcp_call(
            client, "tools/call",
            {"name": "COMPOSIO_GET_TOOL_SCHEMAS", "arguments": {"tool_slugs": slug_list}},
            req_id=100,
        )
        content = result.get("content", [])
        got_schemas = False
        for item in content:
            if item.get("type") == "text":
                text = item["text"]
                try:
                    parsed = json.loads(text)
                    got_schemas = True
                    if isinstance(parsed, list):
                        for schema in parsed:
                            name = schema.get("name") or schema.get("slug") or "?"
                            print(f"\n{'#' * 80}")
                            print(f"TOOL: {name}")
                            print(f"{'#' * 80}")
                            print(json.dumps(schema, indent=2))
                    elif isinstance(parsed, dict):
                        print(json.dumps(parsed, indent=2))
                except json.JSONDecodeError:
                    print(text[:5000])

        if not got_schemas:
            print(f"Batch failed. Result: {json.dumps(result, indent=2)[:1000]}")

            # Try one at a time with tool_slugs as single-element array
            print("\nTrying one at a time...")
            for i, slug in enumerate(slug_list):
                print(f"\n{'#' * 80}")
                print(f"TOOL: {slug}")
                print(f"{'#' * 80}")
                result = await mcp_call(
                    client, "tools/call",
                    {"name": "COMPOSIO_GET_TOOL_SCHEMAS", "arguments": {"tool_slugs": [slug]}},
                    req_id=200 + i,
                )
                content = result.get("content", [])
                for item in content:
                    if item.get("type") == "text":
                        try:
                            parsed = json.loads(item["text"])
                            print(json.dumps(parsed, indent=2))
                        except json.JSONDecodeError:
                            print(item["text"][:3000])
                if not content:
                    print(json.dumps(result, indent=2)[:1000])


if __name__ == "__main__":
    asyncio.run(main())

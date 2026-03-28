#!/usr/bin/env python3
"""Extract Reddit tool schemas from Composio and save as clean JSON."""

import asyncio
import json
import os

BASE = "https://backend.composio.dev/tool_router/trs_0xJb8Y4nexHE/mcp"
HEADERS = {
    "x-api-key": os.environ.get("COMPOSIO_API_KEY", ""),
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}

ALL_SLUGS = [
    "REDDIT_CREATE_REDDIT_POST",
    "REDDIT_DELETE_REDDIT_COMMENT",
    "REDDIT_DELETE_REDDIT_POST",
    "REDDIT_EDIT_REDDIT_COMMENT_OR_POST",
    "REDDIT_GET",
    "REDDIT_GET_ME_PREFS",
    "REDDIT_GET_RANDOM",
    "REDDIT_GET_REDDIT_USER_ABOUT",
    "REDDIT_GET_R_SUBREDDIT_LINK_FLAIR_V2",
    "REDDIT_GET_R_TOP",
    "REDDIT_GET_SCOPES",
    "REDDIT_GET_SUBREDDITS_SEARCH",
    "REDDIT_GET_SUBREDDIT_RULES",
    "REDDIT_GET_USERNAME_AVAILABLE",
    "REDDIT_GET_USER_FLAIR",
    "REDDIT_LIST_SUBREDDIT_POST_FLAIRS",
    "REDDIT_POST_REDDIT_COMMENT",
    "REDDIT_RETRIEVE_POST_COMMENTS",
    "REDDIT_RETRIEVE_REDDIT_POST",
    "REDDIT_RETRIEVE_SPECIFIC_COMMENT",
    "REDDIT_SEARCH_ACROSS_SUBREDDITS",
]


async def main():
    import httpx

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "COMPOSIO_GET_TOOL_SCHEMAS",
            "arguments": {"tool_slugs": ALL_SLUGS},
        },
    }

    async with httpx.AsyncClient(timeout=60) as client:
        async with client.stream("POST", BASE, json=payload, headers=HEADERS) as resp:
            full_text = ""
            async for chunk in resp.aiter_text():
                full_text += chunk

    for line in full_text.split("\n"):
        if line.startswith("data:"):
            data = json.loads(line[5:].strip())
            if "result" in data:
                content = data["result"].get("content", [])
                for item in content:
                    if item.get("type") == "text":
                        parsed = json.loads(item["text"])
                        schemas = parsed.get("data", {}).get("tool_schemas", {})

                        # Save full schemas
                        with open("/Users/clientellkijaoho/Desktop/reddit_skill/docs/reddit_tool_schemas.json", "w") as f:
                            json.dump(schemas, f, indent=2)
                        print(f"Saved {len(schemas)} tool schemas to docs/reddit_tool_schemas.json")

                        # Print summary
                        for slug, schema in sorted(schemas.items()):
                            desc = schema.get("description", "N/A")
                            inp = schema.get("input_schema", {})
                            required = inp.get("required", [])
                            props = inp.get("properties", {})
                            print(f"\n{'=' * 70}")
                            print(f"TOOL: {slug}")
                            print(f"DESC: {desc}")
                            print(f"REQUIRED PARAMS: {required}")
                            print(f"ALL PARAMS:")
                            for pname, pinfo in props.items():
                                ptype = pinfo.get("type", pinfo.get("enum", "?"))
                                pdesc = (pinfo.get("description") or "")[:120]
                                req = " *REQUIRED*" if pname in required else ""
                                print(f"  - {pname} ({ptype}){req}: {pdesc}")
                        return


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
Composio SDK Client for Reddit Skill
Uses composio v1 SDK to execute Reddit tools via connected accounts.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# --- Config ---
API_KEY = os.environ.get("COMPOSIO_API_KEY", "")
USER_ID = os.environ.get("COMPOSIO_USER_ID", "pg-test-af819d82-c40c-431b-a51c-aff077f13733")
TOOLKIT_VERSION = "20260312_00"
ROOT_DIR = Path(__file__).resolve().parents[1]
COMMENT_HISTORY_PATH = ROOT_DIR / "data" / "comment_history.json"

# --- Reddit Account Mapping ---
ACCOUNTS = {
    "admin": {
        "connected_account_id": "ca_ZopdlcjQQTkv",
        "username": "Cool_Intention_161",
        "display_name": "Ava",
        "user_id": "1wy7ui7llh",
    },
    "dev": {
        "connected_account_id": "ca_1OLOcKSRPelp",
        "username": "Candid_Difficulty236",
        "display_name": "Marcus",
        "user_id": "29yvahy5ir",
    },
    "architect": {
        "connected_account_id": "ca_bCe1XdcjrCiB",
        "username": "Sharp_Animal_2708",
        "display_name": "depends_on_context",
        "user_id": "29yvymojkl",
    },
    "critic": {
        "connected_account_id": "ca_9tqOAgaeGw6m",
        "username": "SandboxIsProduction",
        "display_name": "trust_the_demo",
        "user_id": "29wjqt0nbk",
    },
}


def _extract_data(result: dict) -> dict:
    """Unwrap nested data from Composio response."""
    if isinstance(result, dict) and "data" in result:
        inner = result["data"]
        if isinstance(inner, dict) and "data" in inner:
            return inner["data"]
        return inner
    return result


def _utc_now_iso() -> str:
    """Return an ISO-8601 UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


def _load_comment_history() -> dict:
    """Load the local comment history ledger."""
    if not COMMENT_HISTORY_PATH.exists():
        return {"version": 1, "comments": []}
    with COMMENT_HISTORY_PATH.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _save_comment_history(history: dict) -> None:
    """Persist the local comment history ledger."""
    COMMENT_HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with COMMENT_HISTORY_PATH.open("w", encoding="utf-8") as fh:
        json.dump(history, fh, indent=2, sort_keys=True)
        fh.write("\n")


def _extract_created_comment(result: dict) -> dict:
    """Extract the created comment payload from a Reddit post-comment response."""
    if not isinstance(result, dict):
        return {}
    # Format 1: {'data': {'things': [...]}}
    data = result.get("data", {})
    if isinstance(data, dict):
        things = data.get("things", [])
        if things and isinstance(things[0], dict):
            return things[0].get("data", {})
    # Format 2: {'json': {'data': {'things': [...]}}} (from _extract_data unwrap)
    json_data = result.get("json", {})
    if isinstance(json_data, dict):
        inner = json_data.get("data", {})
        if isinstance(inner, dict):
            things = inner.get("things", [])
            if things and isinstance(things[0], dict):
                return things[0].get("data", {})
    return {}


def _post_id_from_permalink(permalink: Optional[str]) -> Optional[str]:
    """Parse the post id from a Reddit permalink."""
    if not permalink:
        return None
    match = re.search(r"/comments/([^/]+)/", permalink)
    if match:
        return match.group(1)
    return None


def _normalize_comment_name(comment_name: Optional[str]) -> Optional[str]:
    """Normalize raw comment ids into Reddit fullname format."""
    if not comment_name:
        return None
    if comment_name.startswith("t1_"):
        return comment_name
    return f"t1_{comment_name}"


class RedditClient:
    """Reddit client backed by Composio SDK."""

    def __init__(self, persona: str, connect: bool = True):
        if persona not in ACCOUNTS:
            raise ValueError(f"Unknown persona '{persona}'. Choose from: {list(ACCOUNTS.keys())}")
        self.persona = persona
        self.account = ACCOUNTS[persona]
        self.account_id = self.account["connected_account_id"]
        self._composio = None
        if connect:
            from composio import Composio

            self._composio = Composio(api_key=API_KEY)

    def _execute(self, tool_slug: str, arguments: dict) -> dict:
        """Execute a Composio Reddit tool and return the result."""
        if self._composio is None:
            raise RuntimeError("This RedditClient instance was initialized without API connectivity.")
        result = self._composio.tools.execute(
            tool_slug,
            user_id=USER_ID,
            connected_account_id=self.account_id,
            version=TOOLKIT_VERSION,
            arguments=arguments,
        )
        return _extract_data(result)

    def get_subreddit_posts(self, subreddit: str, limit: int = 10, sort: str = "hot") -> dict:
        """Fetch posts from a subreddit."""
        return self._execute(
            "REDDIT_RETRIEVE_REDDIT_POST",
            {"subreddit": subreddit, "sort": sort, "max_results": limit},
        )

    def get_post_comments(self, post_id: str) -> dict:
        """Fetch comments for a post. post_id is base-36 ID (no t3_ prefix)."""
        article = post_id.replace("t3_", "")
        return self._execute("REDDIT_RETRIEVE_POST_COMMENTS", {"article": article})

    def submit_comment(self, thing_id: str, text: str) -> dict:
        """Post a comment. thing_id is t3_xxx (post) or t1_xxx (comment)."""
        result = self._execute("REDDIT_POST_REDDIT_COMMENT", {"thing_id": thing_id, "text": text})
        self._record_comment_submission(thing_id=thing_id, text=text, result=result)
        return result

    def get_user_info(self, username: Optional[str] = None) -> dict:
        """Get user profile info. Defaults to 'me' (the persona's account)."""
        return self._execute("REDDIT_GET_REDDIT_USER_ABOUT", {"username": username or "me"})

    def search_posts(self, query: str, limit: int = 10, sort: str = "relevance") -> dict:
        """Search across subreddits."""
        return self._execute(
            "REDDIT_SEARCH_ACROSS_SUBREDDITS",
            {"search_query": query, "sort": sort, "limit": limit},
        )

    def get_subreddit_rules(self, subreddit: str) -> dict:
        """Get the rules of a subreddit."""
        return self._execute("REDDIT_GET_SUBREDDIT_RULES", {"subreddit": subreddit})

    def get_top_posts(self, subreddit: str, time_filter: str = "week", limit: int = 10) -> dict:
        """Get top posts from a subreddit with time filter."""
        return self._execute(
            "REDDIT_GET_R_TOP",
            {"subreddit": subreddit, "t": time_filter, "limit": limit},
        )

    def get_recorded_comments(self) -> list[dict]:
        """Return locally recorded comment submissions for this persona."""
        history = _load_comment_history()
        return [entry for entry in history.get("comments", []) if entry.get("persona") == self.persona]

    def has_commented_on_post(self, post_id: str) -> bool:
        """Check the local ledger for any recorded comment on a specific post."""
        normalized_post_id = post_id.replace("t3_", "")
        return any(entry.get("post_id") == normalized_post_id for entry in self.get_recorded_comments())

    def _record_comment_submission(self, thing_id: str, text: str, result: dict) -> Optional[dict]:
        """Store a successful comment submission in the local ledger."""
        created = _extract_created_comment(result)
        comment_name = created.get("name")
        if not comment_name:
            return None

        history = _load_comment_history()
        comments = history.setdefault("comments", [])
        for existing in comments:
            if existing.get("comment_name") == comment_name:
                return existing

        permalink = created.get("permalink")
        post_id = _post_id_from_permalink(permalink)
        entry = {
            "persona": self.persona,
            "username": self.account["username"],
            "display_name": self.account["display_name"],
            "target_thing_id": thing_id,
            "post_id": post_id or (thing_id.replace("t3_", "") if thing_id.startswith("t3_") else None),
            "comment_id": created.get("id"),
            "comment_name": comment_name,
            "parent_id": created.get("parent_id", thing_id),
            "permalink": permalink,
            "created_utc": created.get("created_utc"),
            "recorded_at": _utc_now_iso(),
            "word_count": len(text.split()),
            "text_preview": " ".join(text.split())[:240],
        }
        comments.append(entry)
        _save_comment_history(history)
        return entry

    def remember_existing_comment(
        self,
        post_id: str,
        comment_name: Optional[str] = None,
        permalink: Optional[str] = None,
        text_preview: str = "",
    ) -> dict:
        """Backfill an already-posted comment into the local ledger."""
        normalized_post_id = post_id.replace("t3_", "")
        normalized_comment_name = _normalize_comment_name(comment_name)

        history = _load_comment_history()
        comments = history.setdefault("comments", [])
        for existing in comments:
            same_comment = normalized_comment_name and existing.get("comment_name") == normalized_comment_name
            same_post = existing.get("persona") == self.persona and existing.get("post_id") == normalized_post_id
            if same_comment or same_post:
                return existing

        entry = {
            "persona": self.persona,
            "username": self.account["username"],
            "display_name": self.account["display_name"],
            "target_thing_id": f"t3_{normalized_post_id}",
            "post_id": normalized_post_id,
            "comment_id": normalized_comment_name.replace("t1_", "") if normalized_comment_name else None,
            "comment_name": normalized_comment_name,
            "parent_id": f"t3_{normalized_post_id}",
            "permalink": permalink,
            "created_utc": None,
            "recorded_at": _utc_now_iso(),
            "word_count": len(text_preview.split()),
            "text_preview": " ".join(text_preview.split())[:240],
            "recorded_via": "manual",
        }
        comments.append(entry)
        _save_comment_history(history)
        return entry


# ---------------------------------------------------------------------------
# CLI smoke test
# ---------------------------------------------------------------------------

def _test():
    print("=" * 60)
    print("Composio Reddit Client — Smoke Test")
    print("=" * 60)

    # Test all 4 accounts — get user info
    for persona in ACCOUNTS:
        acct = ACCOUNTS[persona]
        print(f"\n--- {persona.upper()} ({acct['display_name']} / u/{acct['username']}) ---")
        rc = RedditClient(persona)
        try:
            info = rc.get_user_info()
            name = info.get("name", info.get("subreddit", {}).get("display_name", "?"))
            karma = info.get("total_karma", info.get("comment_karma", "?"))
            print(f"  OK  name={name}  karma={karma}")
        except Exception as e:
            print(f"  FAIL  {e}")

    # Test fetching r/salesforce posts
    print(f"\n--- r/salesforce hot posts (admin) ---")
    rc = RedditClient("admin")
    try:
        posts = rc.get_subreddit_posts("salesforce", limit=3, sort="hot")
        if isinstance(posts, list):
            for p in posts[:3]:
                title = p.get("title", p.get("data", {}).get("title", "?"))
                print(f"  - {title[:80]}")
        else:
            print(f"  {json.dumps(posts, default=str)[:300]}")
    except Exception as e:
        print(f"  FAIL  {e}")

    print("\nDone.")


def _print_history(persona: str) -> int:
    """Print locally recorded comment history for one persona."""
    rc = RedditClient(persona, connect=False)
    comments = rc.get_recorded_comments()
    if not comments:
        print(f"No recorded comments for persona '{persona}'.")
        return 0

    print(f"Recorded comments for {persona} ({len(comments)}):")
    for entry in comments:
        post_id = entry.get("post_id") or "?"
        comment_name = entry.get("comment_name") or "?"
        preview = entry.get("text_preview", "")
        print(f"- post={post_id} comment={comment_name} recorded_at={entry.get('recorded_at')}")
        print(f"  {preview}")
    return 0


def _check_post(persona: str, post_id: str) -> int:
    """Print whether a persona has a locally recorded comment on a post."""
    rc = RedditClient(persona, connect=False)
    print("yes" if rc.has_commented_on_post(post_id) else "no")
    return 0


def _remember_post(persona: str, post_id: str, comment_name: Optional[str] = None) -> int:
    """Backfill an existing comment into the local ledger."""
    rc = RedditClient(persona, connect=False)
    entry = rc.remember_existing_comment(post_id=post_id, comment_name=comment_name)
    print(json.dumps(entry, indent=2))
    return 0


def _main() -> int:
    if len(sys.argv) == 1:
        _test()
        return 0

    command = sys.argv[1]
    if command == "history":
        if len(sys.argv) != 3:
            print("Usage: python scripts/reddit_client.py history <persona>")
            return 1
        return _print_history(sys.argv[2])
    if command == "check":
        if len(sys.argv) != 4:
            print("Usage: python scripts/reddit_client.py check <persona> <post_id>")
            return 1
        return _check_post(sys.argv[2], sys.argv[3])
    if command == "remember":
        if len(sys.argv) not in {4, 5}:
            print("Usage: python scripts/reddit_client.py remember <persona> <post_id> [comment_id]")
            return 1
        comment_name = sys.argv[4] if len(sys.argv) == 5 else None
        return _remember_post(sys.argv[2], sys.argv[3], comment_name)

    print("Usage:")
    print("  python scripts/reddit_client.py")
    print("  python scripts/reddit_client.py history <persona>")
    print("  python scripts/reddit_client.py check <persona> <post_id>")
    print("  python scripts/reddit_client.py remember <persona> <post_id> [comment_id]")
    return 1


if __name__ == "__main__":
    raise SystemExit(_main())

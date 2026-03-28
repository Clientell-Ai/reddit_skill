#!/usr/bin/env python3
"""
Reddit Engagement Runner
Self-contained script for the remote CCR environment.

Subcommands:
  scan                                   — Monitor with --sf-only, select candidates, output JSON
  post <persona> <post_id> "<text>"      — Validate and post a comment
  check-replies                          — Check for replies on previous comments
  notify "<message>"                     — Send Slack DM summary

Usage from CCR:
  1. Claude runs `scan` to get candidate posts with full context
  2. Claude drafts comments (using persona references + writing style guide)
  3. Claude calls `post` for each draft
  4. Claude calls `check-replies` and `notify` to wrap up
"""

import json
import os
import subprocess
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

DATA_DIR = ROOT_DIR / "data"
COMMENT_HISTORY_PATH = DATA_DIR / "comment_history.json"

# Slack config — token from env var to avoid leaking secrets
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")
SLACK_DM_CHANNEL = os.environ.get("SLACK_DM_CHANNEL", "D0APBAA9FHQ")

# Persona target subreddits (lowercase for matching)
PERSONA_TARGETS = {
    "admin": {"salesforce", "salesforceadmin", "salesforcecertified", "crm"},
    "dev": {"salesforcedeveloper", "salesforce"},
    "architect": {"salesforce_architects", "salesforce", "salesforcedeveloper", "sysadmin", "consulting"},
    "critic": {"crm", "salesforce", "sysadmin", "saas", "consulting"},
}

# Personas that prefer higher-comment threads
HIGH_COMMENT_PERSONAS = {"architect", "critic"}
HIGH_COMMENT_IDEAL = 5
HIGH_COMMENT_MIN = 2


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r") as f:
        return json.load(f)


def _load_comment_history() -> dict:
    data = _load_json(COMMENT_HISTORY_PATH)
    if not data:
        return {"version": 1, "comments": []}
    return data


def _commented_post_ids() -> set:
    """All post IDs any persona has commented on."""
    data = _load_comment_history()
    return {c.get("post_id") for c in data.get("comments", []) if c.get("post_id")}


def _ensure_composio():
    """Install composio if not available."""
    try:
        import composio  # noqa: F401
    except ImportError:
        print("Installing composio...", file=sys.stderr)
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "composio==0.11.3"],
            stdout=sys.stderr,
            stderr=sys.stderr,
        )


def _send_slack_dm(message: str) -> dict:
    """Send a Slack DM using urllib (no extra deps)."""
    payload = json.dumps({
        "channel": SLACK_DM_CHANNEL,
        "text": message,
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://slack.com/api/chat.postMessage",
        data=payload,
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            if not body.get("ok"):
                print(f"Slack API error: {body.get('error', 'unknown')}", file=sys.stderr)
            return body
    except urllib.error.URLError as e:
        print(f"Slack request failed: {e}", file=sys.stderr)
        return {"ok": False, "error": str(e)}


# ---------------------------------------------------------------------------
# scan — run monitor, select candidates, fetch context
# ---------------------------------------------------------------------------

def cmd_scan():
    """Run monitor with --sf-only, select up to 4 posts (one per persona), output JSON."""
    _ensure_composio()

    from scripts.monitor import scan_reddit
    from scripts.reddit_client import RedditClient

    print("Running Salesforce-only scan...", file=sys.stderr)
    posts = scan_reddit(sf_only=True)
    print(f"  Found {len(posts)} posts after sf-only filter", file=sys.stderr)

    if not posts:
        print(json.dumps({"candidates": [], "message": "No matching posts found."}))
        return

    commented = _commented_post_ids()
    # Filter out already-commented posts
    available = [p for p in posts if p["post_id"] not in commented]
    print(f"  {len(available)} posts not yet commented on", file=sys.stderr)

    # Select one post per persona
    selected = {}  # persona -> post
    used_post_ids = set()

    for persona in ["admin", "dev", "architect", "critic"]:
        targets = PERSONA_TARGETS[persona]
        prefers_high = persona in HIGH_COMMENT_PERSONAS

        # Filter to posts in this persona's target subs
        candidates = [
            p for p in available
            if p["subreddit"].lower() in targets and p["post_id"] not in used_post_ids
        ]

        if not candidates:
            continue

        if prefers_high:
            # Prefer 5+ comments, fall back to 2+
            ideal = [p for p in candidates if p["num_comments"] >= HIGH_COMMENT_IDEAL]
            fallback = [p for p in candidates if p["num_comments"] >= HIGH_COMMENT_MIN]
            pool = ideal if ideal else fallback if fallback else candidates
        else:
            pool = candidates

        # Pick the highest engagement_score post from the pool
        pool.sort(key=lambda x: x.get("engagement_score", 0), reverse=True)
        pick = pool[0]
        selected[persona] = pick
        used_post_ids.add(pick["post_id"])

    if not selected:
        print(json.dumps({"candidates": [], "message": "No suitable posts for any persona."}))
        return

    # Fetch full context for each selected post
    candidates = []
    rc_cache = {}
    for persona, post in selected.items():
        if persona not in rc_cache:
            rc_cache[persona] = RedditClient(persona)
        rc = rc_cache[persona]

        post_id = post["post_id"]
        try:
            comments_data = rc.get_post_comments(post_id)
        except Exception as e:
            print(f"  [WARN] Could not fetch comments for {post_id}: {e}", file=sys.stderr)
            comments_data = {}

        # Read persona reference file
        ref_path = ROOT_DIR / "references" / f"{persona}.md"
        persona_ref = ""
        if ref_path.exists():
            persona_ref = ref_path.read_text(encoding="utf-8")

        candidates.append({
            "persona": persona,
            "post_id": post_id,
            "subreddit": post["subreddit"],
            "title": post["title"],
            "selftext_preview": post.get("selftext_preview", ""),
            "score": post["score"],
            "num_comments": post["num_comments"],
            "age_hours": post["age_hours"],
            "permalink": post.get("permalink", ""),
            "url": f"https://reddit.com{post.get('permalink', '')}",
            "matched_keywords": post.get("matched_keywords", []),
            "engagement_score": post.get("engagement_score", 0),
            "comments_context": comments_data,
            "persona_reference_file": f"references/{persona}.md",
        })

    # Read the writing style guide once
    style_path = ROOT_DIR / "references" / "reddit_writing_style.md"
    style_guide = ""
    if style_path.exists():
        style_guide = style_path.read_text(encoding="utf-8")

    output = {
        "candidates": candidates,
        "writing_style_guide": style_guide,
        "drafting_rules": {
            "word_count": "35-90 words",
            "sentences": "2-5 sentences",
            "voice": "casual Reddit — lowercase OK, no perfect grammar",
            "no_em_dashes": True,
            "no_bullet_lists": True,
            "no_product_mentions": True,
            "no_links": True,
            "no_ai_tells": True,
            "include_reply_hook": "question at the end",
            "include_firsthand_experience": True,
        },
        "scanned_at": datetime.now(timezone.utc).isoformat(),
    }

    print(json.dumps(output, indent=2, default=str))


# ---------------------------------------------------------------------------
# post — validate and post a comment
# ---------------------------------------------------------------------------

def cmd_post(persona: str, post_id: str, comment_text: str):
    """Validate a draft and post it as a comment."""
    _ensure_composio()

    from scripts.validate import validate_draft
    from scripts.reddit_client import RedditClient

    # Validate first
    flags = validate_draft(comment_text)
    critical = [f for f in flags if f[0] == "CRITICAL"]
    if critical:
        result = {
            "status": "blocked",
            "persona": persona,
            "post_id": post_id,
            "validation_errors": [{"severity": s, "message": m} for s, m in flags],
        }
        print(json.dumps(result, indent=2))
        return

    warnings = [f for f in flags if f[0] in ("WARNING", "INFO")]

    # Post the comment
    rc = RedditClient(persona)
    thing_id = f"t3_{post_id.replace('t3_', '')}"

    try:
        result = rc.submit_comment(thing_id, comment_text)
        output = {
            "status": "posted",
            "persona": persona,
            "post_id": post_id,
            "thing_id": thing_id,
            "word_count": len(comment_text.split()),
            "text_preview": comment_text[:240],
            "api_result": result,
        }
        if warnings:
            output["validation_warnings"] = [{"severity": s, "message": m} for s, m in warnings]
        print(json.dumps(output, indent=2, default=str))
    except Exception as e:
        error_output = {
            "status": "error",
            "persona": persona,
            "post_id": post_id,
            "error": str(e),
        }
        print(json.dumps(error_output, indent=2))


# ---------------------------------------------------------------------------
# check-replies — look for replies on our previous comments
# ---------------------------------------------------------------------------

def cmd_check_replies():
    """Check for replies on previous comments from comment_history.json."""
    _ensure_composio()

    from scripts.reddit_client import RedditClient

    history = _load_comment_history()
    comments = history.get("comments", [])

    if not comments:
        print(json.dumps({"replies": [], "message": "No comment history found."}))
        return

    replies_found = []
    rc_cache = {}

    for entry in comments:
        persona = entry.get("persona")
        post_id = entry.get("post_id")
        our_comment_name = entry.get("comment_name")  # e.g. t1_xxx

        if not persona or not post_id or not our_comment_name:
            continue

        if persona not in rc_cache:
            try:
                rc_cache[persona] = RedditClient(persona)
            except Exception:
                continue
        rc = rc_cache[persona]

        try:
            data = rc.get_post_comments(post_id)
        except Exception as e:
            print(f"  [WARN] Could not fetch comments for post {post_id}: {e}", file=sys.stderr)
            continue

        # Walk the comment tree looking for replies to our comment
        def _find_replies(comments_list, target_name):
            """Recursively search for comments whose parent_id matches target_name."""
            found = []
            if not isinstance(comments_list, list):
                return found
            for item in comments_list:
                c = item.get("data", item) if isinstance(item, dict) else {}
                if c.get("parent_id") == target_name:
                    found.append({
                        "reply_name": c.get("name", ""),
                        "reply_id": c.get("id", ""),
                        "author": c.get("author", "?"),
                        "body": (c.get("body") or "")[:300],
                        "score": c.get("score", 0),
                        "created_utc": c.get("created_utc"),
                        "permalink": c.get("permalink", ""),
                    })
                # Check nested replies
                replies_data = c.get("replies")
                if isinstance(replies_data, dict):
                    children = replies_data.get("data", {}).get("children", [])
                    found.extend(_find_replies(children, target_name))
                elif isinstance(replies_data, list):
                    found.extend(_find_replies(replies_data, target_name))
            return found

        # The comments_listing is typically the second element of a two-element list
        comment_children = []
        if isinstance(data, list) and len(data) >= 2:
            comment_children = data[1].get("data", {}).get("children", [])
        elif isinstance(data, dict):
            comment_children = data.get("comments_listing", {}).get("data", {}).get("children", [])
            if not comment_children:
                # Flat list fallback
                comment_children = data.get("children", [])

        found = _find_replies(comment_children, our_comment_name)
        if found:
            replies_found.append({
                "persona": persona,
                "post_id": post_id,
                "subreddit": entry.get("subreddit", ""),
                "our_comment": our_comment_name,
                "our_text_preview": entry.get("text_preview", ""),
                "replies": found,
            })

    output = {
        "replies": replies_found,
        "checked_comments": len(comments),
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }
    print(json.dumps(output, indent=2, default=str))


# ---------------------------------------------------------------------------
# notify — send Slack DM
# ---------------------------------------------------------------------------

def cmd_notify(message: str):
    """Send a Slack DM summary."""
    result = _send_slack_dm(message)
    output = {
        "status": "sent" if result.get("ok") else "failed",
        "error": result.get("error") if not result.get("ok") else None,
        "channel": SLACK_DM_CHANNEL,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    print(json.dumps(output, indent=2))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _usage():
    print("""Usage:
  python scripts/run_engagement.py scan
  python scripts/run_engagement.py post <persona> <post_id> "<comment_text>"
  python scripts/run_engagement.py check-replies
  python scripts/run_engagement.py notify "<message>"
""")


def main():
    if len(sys.argv) < 2:
        _usage()
        sys.exit(1)

    command = sys.argv[1]

    if command == "scan":
        cmd_scan()
    elif command == "post":
        if len(sys.argv) < 5:
            print("Usage: python scripts/run_engagement.py post <persona> <post_id> \"<comment_text>\"")
            sys.exit(1)
        persona = sys.argv[2]
        post_id = sys.argv[3]
        comment_text = sys.argv[4]
        cmd_post(persona, post_id, comment_text)
    elif command == "check-replies":
        cmd_check_replies()
    elif command == "notify":
        if len(sys.argv) < 3:
            print("Usage: python scripts/run_engagement.py notify \"<message>\"")
            sys.exit(1)
        message = sys.argv[2]
        cmd_notify(message)
    else:
        print(f"Unknown command: {command}")
        _usage()
        sys.exit(1)


if __name__ == "__main__":
    main()

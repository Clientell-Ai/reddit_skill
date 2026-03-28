#!/usr/bin/env python3
"""
Reddit Keyword Monitor
Polls Reddit for fresh, high-engagement posts matching target keywords.
Uses two strategies: keyword search API + direct subreddit polling with title matching.

Usage:
  python scripts/monitor.py              # Run once, print results
  python scripts/monitor.py --json       # Output JSON for piping
  python scripts/monitor.py --watch      # Run every 30 min continuously
  python scripts/monitor.py --sf-only    # Strict filter: only Salesforce-related posts
"""

import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

SEEN_POSTS_PATH = ROOT_DIR / "data" / "seen_posts.json"
COMMENT_HISTORY_PATH = ROOT_DIR / "data" / "comment_history.json"
ALERTS_PATH = ROOT_DIR / "data" / "alerts.json"

# --- Keywords for search API ---
SEARCH_KEYWORDS = [
    "salesforce",
    "salesforce admin",
    "salesforce developer",
    "agentforce",
    "salesforce flow",
    "salesforce pricing",
    "salesforce implementation",
    "CRM recommendation",
    "CRM migration",
    "hubspot vs salesforce",
    "best CRM",
    "data cloud salesforce",
    "lightning web component",
    "apex trigger",
    "salesforce certification",
]

# --- Subreddits to poll directly (catches posts search API misses) ---
POLL_SUBREDDITS = [
    "salesforce",
    "salesforceadmin",
    "SalesforceDeveloper",
    "Salesforce_Architects",
    "SalesforceCareers",
    "SalesforceCertified",
    "CRM",
    "SaaS",
    "sysadmin",
    "consulting",
    "smallbusiness",
    "startups",
    "ExperiencedDevs",
    "devops",
    "ITCareerQuestions",
    "cscareerquestions",
    "AI_Agents",
]

# --- Title/body keyword patterns for filtering polled subreddit posts ---
# Posts from non-SF subs must match at least one of these to be included
TITLE_PATTERNS = [
    re.compile(r"\bsalesforce\b", re.I),
    re.compile(r"\bsfdc\b", re.I),
    re.compile(r"\bcrm\b", re.I),
    re.compile(r"\bagentforce\b", re.I),
    re.compile(r"\bapex\b", re.I),
    re.compile(r"\blwc\b", re.I),
    re.compile(r"\bhubspot\b", re.I),
    re.compile(r"\btechnical debt\b", re.I),
    re.compile(r"\bdata migration\b", re.I),
    re.compile(r"\benterprise (software|ai|architecture)\b", re.I),
    re.compile(r"\bai agent\b", re.I),
    re.compile(r"\bplatform.*(consolidat|migrat)\b", re.I),
    re.compile(r"\bintegration.*(nightmare|hell|mess|tax)\b", re.I),
    re.compile(r"\b(erp|saas).*(dead|dying|migration|replace)\b", re.I),
    re.compile(r"\bvibe.?cod", re.I),
]

# Salesforce-native subs (all posts are relevant, no keyword filter needed)
SF_NATIVE_SUBS = {
    "salesforce", "salesforceadmin", "salesforcedeveloper",
    "salesforce_architects", "salesforcecareers", "salesforcecertified",
    "crm",
}

# --- Persona mapping for matched keywords ---
KEYWORD_PERSONAS = {
    "salesforce": ["admin", "dev", "architect", "critic"],
    "sfdc": ["admin", "dev", "architect", "critic"],
    "agentforce": ["dev", "architect", "critic"],
    "crm": ["critic", "admin"],
    "hubspot": ["critic"],
    "apex": ["dev"],
    "lwc": ["dev"],
    "flow": ["admin", "dev"],
    "certification": ["admin"],
    "pricing": ["critic"],
    "implementation": ["architect", "critic"],
    "migration": ["architect"],
    "technical debt": ["architect", "dev"],
    "integration": ["architect"],
    "enterprise": ["architect", "critic"],
    "ai agent": ["dev", "critic"],
    "vibe cod": ["dev", "architect"],
}

# --- Thresholds ---
MAX_AGE_HOURS = 8
POLL_INTERVAL_SECONDS = 30 * 60  # 30 minutes


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r") as f:
        return json.load(f)


def _save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def _load_seen_posts() -> set:
    data = _load_json(SEEN_POSTS_PATH)
    return set(data.get("seen", []))


def _save_seen_posts(seen: set) -> None:
    # Only keep last 500 to avoid file bloat
    recent = sorted(seen)[-500:]
    _save_json(SEEN_POSTS_PATH, {"seen": recent, "updated": datetime.now(timezone.utc).isoformat()})


def _load_commented_post_ids() -> set:
    data = _load_json(COMMENT_HISTORY_PATH)
    return {c.get("post_id") for c in data.get("comments", []) if c.get("post_id")}


def _append_alerts(new_alerts: list) -> None:
    data = _load_json(ALERTS_PATH)
    existing = data.get("alerts", [])
    existing.extend(new_alerts)
    data["alerts"] = existing[-200:]
    data["updated"] = datetime.now(timezone.utc).isoformat()
    _save_json(ALERTS_PATH, data)


def _match_keywords(title: str, selftext: str = "") -> list:
    """Return list of matched keyword groups from title + body."""
    text = f"{title} {selftext}".lower()
    matched = []
    for pattern in TITLE_PATTERNS:
        m = pattern.search(text)
        if m:
            matched.append(m.group(0).lower().strip())
    return matched


def _suggest_personas(matched_keywords: list, subreddit: str) -> list:
    """Suggest personas based on matched keywords and subreddit."""
    personas = set()
    sub_lower = subreddit.lower()

    # Sub-based defaults
    if sub_lower in ("salesforce", "salesforceadmin"):
        personas.add("admin")
    if sub_lower in ("salesforcedeveloper",):
        personas.add("dev")
    if sub_lower in ("salesforce_architects",):
        personas.add("architect")
    if sub_lower in ("crm",):
        personas.add("critic")

    # Keyword-based
    for kw in matched_keywords:
        for key, p_list in KEYWORD_PERSONAS.items():
            if key in kw:
                personas.update(p_list)

    return sorted(personas) if personas else ["admin", "dev", "architect", "critic"]


# ---------------------------------------------------------------------------
# Core monitor
# ---------------------------------------------------------------------------

SF_ONLY_PATTERNS = [
    re.compile(r"\bsalesforce\b", re.I),
    re.compile(r"\bsfdc\b", re.I),
]


def _passes_sf_only_filter(subreddit: str, title: str, selftext: str) -> bool:
    """When --sf-only is active, only include posts that are truly about Salesforce.

    - Posts in SF-native subs always pass.
    - Posts in other subs must mention 'salesforce' or 'sfdc' in title or body.
    """
    if subreddit.lower() in SF_NATIVE_SUBS:
        return True
    text = f"{title} {selftext}"
    return any(p.search(text) for p in SF_ONLY_PATTERNS)


def scan_reddit(sf_only: bool = False) -> list:
    """Search Reddit for keywords + poll subreddits. Return ranked post list."""
    from scripts.reddit_client import RedditClient

    rc = RedditClient("admin")
    now = datetime.now(timezone.utc).timestamp()
    seen = _load_seen_posts()
    commented = _load_commented_post_ids()

    all_posts = {}  # post_id -> enriched data

    def _process_post(data: dict, source: str, matched_kws: list = None):
        post_id = data.get("id")
        if not post_id:
            return

        created = data.get("created_utc", 0)
        age_hrs = (now - created) / 3600 if created else 999
        if age_hrs > MAX_AGE_HOURS:
            return
        if post_id in commented:
            return

        subreddit = data.get("subreddit", "")
        title = data.get("title", "")
        selftext = data.get("selftext", "") or ""

        # --sf-only: strict filter — non-SF subs must mention salesforce/sfdc
        if sf_only and not _passes_sf_only_filter(subreddit, title, selftext):
            return

        # For non-SF subs, require keyword match in title/body
        if subreddit.lower() not in SF_NATIVE_SUBS:
            if not matched_kws:
                matched_kws = _match_keywords(title, selftext)
            if not matched_kws:
                return

        if not matched_kws:
            matched_kws = _match_keywords(title, selftext)

        score = data.get("score", 0)
        num_comments = data.get("num_comments", 0)

        if post_id not in all_posts:
            all_posts[post_id] = {
                "post_id": post_id,
                "title": title,
                "subreddit": subreddit,
                "score": score,
                "num_comments": num_comments,
                "age_hours": round(age_hrs, 1),
                "created_utc": created,
                "permalink": data.get("permalink", ""),
                "selftext_preview": selftext[:200],
                "matched_keywords": matched_kws or [subreddit.lower()],
                "suggested_personas": _suggest_personas(matched_kws or [], subreddit),
                "is_new": post_id not in seen,
                "source": source,
            }
        else:
            entry = all_posts[post_id]
            entry["score"] = max(entry["score"], score)
            entry["num_comments"] = max(entry["num_comments"], num_comments)
            if matched_kws:
                for kw in matched_kws:
                    if kw not in entry["matched_keywords"]:
                        entry["matched_keywords"].append(kw)
                entry["suggested_personas"] = _suggest_personas(entry["matched_keywords"], subreddit)

    # --- Strategy 1: Keyword search API ---
    print("  Searching keywords...", file=sys.stderr)
    for keyword in SEARCH_KEYWORDS:
        try:
            results = rc.search_posts(keyword, limit=15, sort="new")
            posts = results if isinstance(results, list) else results.get("children", [])
            for p in posts:
                data = p.get("data", p) if isinstance(p, dict) else p
                _process_post(data, source=f"search:{keyword}", matched_kws=[keyword])
        except Exception as e:
            print(f"  [WARN] Search '{keyword}': {e}", file=sys.stderr)

    # --- Strategy 2: Direct subreddit polling ---
    print("  Polling subreddits...", file=sys.stderr)
    for sub in POLL_SUBREDDITS:
        try:
            results = rc.get_subreddit_posts(sub, limit=15, sort="new")
            posts = results if isinstance(results, list) else results.get("children", [])
            for p in posts:
                data = p.get("data", p) if isinstance(p, dict) else p
                _process_post(data, source=f"sub:{sub}")
        except Exception as e:
            print(f"  [WARN] Sub r/{sub}: {e}", file=sys.stderr)

    # --- Rank posts ---
    ranked = []
    for post_id, entry in all_posts.items():
        engagement = entry["num_comments"] * 3 + entry["score"]
        freshness = max(0, (MAX_AGE_HOURS - entry["age_hours"]) / MAX_AGE_HOURS)
        keyword_bonus = len(entry["matched_keywords"]) * 5
        # SF-native subs get a bonus
        sf_bonus = 10 if entry["subreddit"].lower() in SF_NATIVE_SUBS else 0

        entry["engagement_score"] = round(engagement + freshness * 20 + keyword_bonus + sf_bonus, 1)
        ranked.append(entry)

    ranked.sort(key=lambda x: x["engagement_score"], reverse=True)

    # Update seen
    seen.update(all_posts.keys())
    _save_seen_posts(seen)

    return ranked


def format_results(posts: list, json_output: bool = False) -> str:
    """Format scan results for display."""
    if json_output:
        return json.dumps(posts, indent=2, default=str)

    if not posts:
        return f"[{datetime.now(timezone.utc).strftime('%H:%M UTC')}] No matching posts found.\n"

    lines = []
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines.append(f"=== Reddit Monitor -- {now_str} ===")
    lines.append(f"Found {len(posts)} posts matching keywords\n")

    for i, p in enumerate(posts[:25], 1):
        new_tag = " *NEW*" if p["is_new"] else ""
        personas = ", ".join(p["suggested_personas"])
        keywords = ", ".join(p["matched_keywords"][:3])

        lines.append(f"{i:2d}. [r/{p['subreddit']}] score={p['score']} comments={p['num_comments']} age={p['age_hours']}h{new_tag}")
        lines.append(f"    {p['title'][:95]}")
        lines.append(f"    Personas: {personas} | Keywords: {keywords} | Rank: {p['engagement_score']}")
        lines.append(f"    https://reddit.com{p['permalink']}")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    json_output = "--json" in sys.argv
    watch_mode = "--watch" in sys.argv
    sf_only = "--sf-only" in sys.argv

    if watch_mode:
        print(f"Starting Reddit monitor (polling every {POLL_INTERVAL_SECONDS // 60} min)...")
        print(f"Tracking {len(SEARCH_KEYWORDS)} search keywords + {len(POLL_SUBREDDITS)} subreddits")
        print(f"Alerts saved to: {ALERTS_PATH}")
        print("Press Ctrl+C to stop.\n")

        while True:
            try:
                posts = scan_reddit(sf_only=sf_only)
                output = format_results(posts, json_output)
                print(output)

                # Save high-value new alerts
                new_alerts = [
                    {
                        "post_id": p["post_id"],
                        "title": p["title"],
                        "subreddit": p["subreddit"],
                        "score": p["score"],
                        "num_comments": p["num_comments"],
                        "personas": p["suggested_personas"],
                        "engagement_score": p["engagement_score"],
                        "scanned_at": datetime.now(timezone.utc).isoformat(),
                        "url": f"https://reddit.com{p['permalink']}",
                    }
                    for p in posts
                    if p["is_new"] and p["engagement_score"] >= 30
                ]
                if new_alerts:
                    _append_alerts(new_alerts)
                    print(f"  >> {len(new_alerts)} new high-value alert(s) saved\n")

                time.sleep(POLL_INTERVAL_SECONDS)
            except KeyboardInterrupt:
                print("\nMonitor stopped.")
                break
            except Exception as e:
                print(f"  [ERROR] {e}", file=sys.stderr)
                time.sleep(60)
    else:
        posts = scan_reddit(sf_only=sf_only)
        output = format_results(posts, json_output)
        print(output)


if __name__ == "__main__":
    main()

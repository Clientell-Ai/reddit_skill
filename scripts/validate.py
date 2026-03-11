#!/usr/bin/env python3
"""
Reddit Draft Validator
Checks drafts against global constraints before presenting to operator.
Usage: python scripts/validate.py "draft text here"
   or: cat draft.txt | python scripts/validate.py
"""

import sys
import re

# --- AI disclosure signal patterns ---
AI_PATTERNS = [
    (r"(?i)^great question", "Opens with 'Great question!' — classic AI tell"),
    (r"(?i)i hope this helps", "Contains 'I hope this helps' — AI closer pattern"),
    (r"(?i)^absolutely[!.]", "Opens with 'Absolutely!' — AI affirmation pattern"),
    (r"(?i)^definitely[!.]", "Opens with 'Definitely!' — AI affirmation pattern"),
    (r"(?i)^as a [\w\s]+, i can say", "Contains 'As a [role], I can say' — AI preamble"),
    (r"(?i)on one hand.*on the other hand", "Contains 'on one hand / on the other hand' — AI balance pattern"),
    (r"(?i)^(hi|hello|hey) there[!,]", "Opens with generic greeting — AI pattern"),
    (r"(?i)in conclusion,", "Contains 'In conclusion' — essay-style AI pattern"),
    (r"(?i)it'?s worth noting that", "Contains 'It's worth noting' — AI filler"),
    (r"(?i)that being said,", "Contains 'That being said' — AI transition"),
    (r"(?i)let me break this down", "Contains 'Let me break this down' — AI structure signal"),
    (r"(?i)here'?s the thing:", "Contains 'Here's the thing:' — overused AI opener"),
]

# --- Product / promotion patterns ---
PROMO_PATTERNS = [
    (r"(?i)\bclientell\b", "CRITICAL: Contains 'Clientell' — zero product mentions allowed"),
    (r"(?i)\bcheck out\b.*\b(tool|product|platform|solution|app)\b", "Possible product promotion detected"),
    (r"(?i)\bsign up\b", "Contains 'sign up' — CTA pattern"),
    (r"(?i)\btry (it|this|our)\b.*\bfree\b", "Possible free trial CTA"),
    (r"(?i)\bdm me\b", "Contains 'DM me' — against subreddit rules"),
    (r"(?i)\blink in (bio|profile)\b", "Contains 'link in bio/profile' — promotion pattern"),
    (r"(?i)https?://", "Contains a URL — no links during warm-up"),
    (r"(?i)\bwww\.", "Contains a URL — no links during warm-up"),
    (r"(?i)\bdiscount\b|\bcoupon\b|\bpromo code\b", "Contains promotional language"),
]

# --- Structural quality checks ---
QUALITY_CHECKS = [
    # Too many bullet points = AI feel
    ("bullet_heavy", "Draft is bullet-heavy — Reddit comments are conversational. Consider rewriting some bullets as prose."),
    # Too long
    ("too_long", "Draft exceeds 500 words — consider trimming for Reddit readability."),
    # Too short (might lack substance)
    ("too_short", "Draft is under 30 words — may lack enough substance to be valuable."),
]


def count_bullet_lines(text):
    """Count lines that start with bullet markers."""
    lines = text.strip().split("\n")
    bullet_count = sum(1 for line in lines if re.match(r"^\s*[-*•]\s", line.strip()) or re.match(r"^\s*\d+[.)]\s", line.strip()))
    total_lines = len([l for l in lines if l.strip()])
    return bullet_count, total_lines


def validate_draft(text):
    """Validate a draft against all constraint patterns. Returns list of (severity, message) tuples."""
    flags = []

    # Check AI patterns
    for pattern, message in AI_PATTERNS:
        if re.search(pattern, text):
            flags.append(("WARNING", message))

    # Check promotion patterns
    for pattern, message in PROMO_PATTERNS:
        if re.search(pattern, text):
            severity = "CRITICAL" if "CRITICAL" in message else "WARNING"
            flags.append((severity, message))

    # Structural checks
    bullet_count, total_lines = count_bullet_lines(text)
    if total_lines > 0 and bullet_count / total_lines > 0.5:
        flags.append(("WARNING", QUALITY_CHECKS[0][1]))

    word_count = len(text.split())
    if word_count > 500:
        flags.append(("INFO", QUALITY_CHECKS[1][1]))
    if word_count < 30:
        flags.append(("WARNING", QUALITY_CHECKS[2][1]))

    # Check for cert dump language
    if re.search(r"(?i)\b(dump|brain\s*dump|cert\s*dump|exam\s*dump)\b", text):
        flags.append(("CRITICAL", "Contains cert dump reference — immediate ban in r/salesforce and r/SalesforceCertified"))

    # Check for deleted content references
    if re.search(r"(?i)\bdelete (this|my|the) (post|comment|question)\b", text):
        flags.append(("WARNING", "References deleting content — r/salesforce bans deletion after engagement"))

    return flags


def main():
    # Read from argument or stdin
    if len(sys.argv) > 1:
        text = " ".join(sys.argv[1:])
    else:
        text = sys.stdin.read()

    if not text.strip():
        print("ERROR: No draft text provided.")
        print("Usage: python scripts/validate.py \"draft text here\"")
        print("   or: cat draft.txt | python scripts/validate.py")
        sys.exit(1)

    flags = validate_draft(text)

    if not flags:
        print("PASS — No issues detected.")
        sys.exit(0)

    has_critical = False
    print(f"VALIDATION RESULTS — {len(flags)} issue(s) found:\n")
    for severity, message in flags:
        print(f"  [{severity}] {message}")
        if severity == "CRITICAL":
            has_critical = True

    print()
    if has_critical:
        print("BLOCKED — Critical issues must be resolved before presenting draft.")
        sys.exit(1)
    else:
        print("REVIEW — Warnings found. Consider revising before presenting draft.")
        sys.exit(0)


if __name__ == "__main__":
    main()

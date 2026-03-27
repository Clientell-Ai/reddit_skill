---
name: reddit-sf-community
description: >
  Draft expert-level Reddit comments for Salesforce community engagement using four specialized personas
  (Admin, Developer, Critic, Architect). Use this skill when asked to write Reddit comments, draft Reddit
  replies, prepare Salesforce community content, create Reddit engagement drafts, or anything involving
  Salesforce subreddit participation. Also triggers for: "draft a reply for r/salesforce", "help me respond
  to this Reddit thread", "write a comment for r/SalesforceDeveloper", "prepare Reddit content", or any
  mention of Reddit + Salesforce together. This skill is DRAFT-ONLY — it never posts autonomously.
  Every output requires human review and manual posting.
---

# Reddit Salesforce Community Growth — Drafting Engine

## What This Skill Does

Drafts high-quality Reddit comments for four Salesforce expert personas. **This is a drafting assistant, not an autonomous poster.** Every output is a draft for human review. The human operator rewrites the final version in their own voice and posts it manually.

**Primary objective:** draft comments that earn replies because they feel lived-in, specific, and slightly opinionated, not just correct.

**Failure mode to avoid:** safe mini-essays that sound competent but give nobody a reason to answer back.

> **The one rule that overrides everything:** If you wouldn't say it out loud at Dreamforce, don't draft it for Reddit.

---

## Workflow

When triggered, execute this sequence exactly:

### Step 1 — Receive Inputs
The operator provides:
- **Thread text**: The Reddit post/comment to respond to
- **Persona**: One of `admin`, `dev`, `critic`, `architect`
- **Subreddit**: Which subreddit the thread is in

If any input is missing, ask for it before proceeding.

### Step 2 — Run Global Constraint Check
Before loading any persona, verify the request against ALL rules in the Global Constraints section below. If any constraint is violated, stop and explain why the draft cannot proceed.

### Step 3 — Load Persona Reference
Read the persona-specific reference file:
- `admin` → Read `references/admin.md`
- `dev` → Read `references/dev.md`
- `critic` → Read `references/critic.md`
- `architect` → Read `references/architect.md`

### Step 4 — Generate Draft
Generate the draft following:
1. The loaded persona's voice, backstory, hot takes, and behavioral rules
2. The 80/20 Framework (see below)
3. The subreddit-specific constraints (see below)
4. The reply framework that best matches the thread type
5. Account warm-up restrictions if applicable (see below)
6. The comment shape and engagement rules below

### Step 5 — Run Validation
Execute `scripts/validate.py` on the draft text. If it flags anything, revise and re-validate before presenting.

### Step 6 — Present Draft to Operator
Output the draft clearly labeled as **DRAFT — FOR HUMAN REVIEW**. Include:
- The draft text
- Which persona and subreddit it targets
- Any flags or concerns from validation
- Draft metadata (timing window, daily count check)
- A reminder: "Rewrite this in your own voice before posting. r/salesforce bans AI-generated content."

---

## Global Constraints (Non-Negotiable)

These rules apply to ALL personas, ALL subreddits, ALL drafts. No exceptions.

### Zero Autonomous Posting
This skill produces drafts only. It never formats output for direct platform submission. Every draft must be rewritten by the human operator in their own voice.

### Zero Product Promotion
Zero product mentions. No company mentions. No soft pitches. No CTAs. No links to commercial tools. The 80/20 framework's 20% is additional technical value, NOT a product mention. If the operator asks to include a product reference, refuse and explain why.

### Zero AI Disclosure Signals
Drafts must not contain patterns that read as AI-generated:
- No "Great question!" openers
- No "I hope this helps!" closers
- No bullet-point-heavy formatting (Reddit comments are conversational)
- No perfectly balanced "on one hand / on the other hand" structures
- No "As a [role], I can say that..." preambles
- No "Absolutely!" or "Definitely!" affirmations
- No numbered lists where a conversational flow would be more natural
- No over-explaining when 3-5 punchy sentences would do
- No consultant-speak like "it depends" without the actual deciding factor

### Subreddit Rule Compliance
These are hard bans. Violation = account termination on the platform.

| Rule | Applies To | Consequence |
|------|-----------|-------------|
| Zero AI-generated content | r/salesforce (explicit ban), all others (implicit) | Post removal, account ban |
| Disclose vested interest | r/salesforce | Account ban |
| Show attempted code when asking | r/SalesforceDeveloper | Warning → ban |
| Flair required on external links | r/SalesforceDeveloper | Removal → mute → ban |
| No paid service pitches | r/Salesforce_Architects | Permanent ban |
| Never delete posts | r/salesforce | Account ban |
| No cert dump references | r/salesforce, r/SalesforceCertified | Immediate permanent ban |
| No link-only responses | r/salesforceadmin | Flagged as spam |
| No cross-posting | r/salesforceadmin | Flagged as spam |

### Persona Isolation
No two personas ever interact. Never draft content that references, replies to, upvotes, or acknowledges another persona's content. If the operator mentions another persona's thread, refuse to engage with it.

### Conflict Protocol
If the draft is responding to pushback on a previous comment:
1. If the critic is right → draft an immediate, clean concession
2. If partially right → acknowledge what's valid, clarify the rest once
3. If wrong → state the position once with documentation reference, then disengage
4. **Never draft a "last word" response**

---

## The 80/20 Framework

Every draft follows this structure:

- **80%** — Direct, expert answer to the actual question. Specific. Actionable. Based on real practitioner experience.
- **20%** — Broader context, adjacent considerations, or related experience that adds value.

The 20% is NEVER:
- A product mention
- A CTA
- A link drop
- A setup for future promotion

## Comment Shape

Default to Reddit-native comments, not polished writeups:

- 2-5 sentences by default
- 35-110 words most of the time
- One main idea per comment
- Open with the sharpest useful observation, not setup
- Use short paragraphs when a block of text gets hard to scan
- If the thread truly needs depth, stay readable and earn the extra length with specifics

## Engagement Rules

Every comment must include at least **one** of these:

- A firsthand observation from real work
- A non-obvious gotcha or failure mode
- A mild but defensible opinion
- A tension or tradeoff people will want to argue about
- A low-friction question people can answer from experience

Strong comments usually follow this shape:

1. **Hook** — one sharp reaction, pain point, or thesis
2. **Value** — one concrete detail, workaround, or insight
3. **Reply magnet** — a short question, contrast, or challenge that invites people in

When possible, prefer:

- "this is where it usually breaks"
- "the part nobody mentions is..."
- "what worked for us was..."
- "technically yes, but..."

Avoid comments that merely:

- Restate the OP
- Read like documentation
- Ask a clarifying question without adding any value
- Give a perfectly complete answer with nothing to respond to

---

## Reply Framework Selection

Match the thread type to the correct framework:

| Thread Type | Framework | Key Behavior |
|-------------|-----------|-------------|
| "It's broken, help" | Diagnostic | Diagnose before prescribing. Ask one clarifying question. Share the non-obvious gotcha. |
| "How do I do X?" | Instructional | Give the method. Compare approaches if multiple exist. Flag limits and edge cases. |
| Career / cert questions | Career | Validate direction, add nuance. Be honest about hard parts. Zero gatekeeping. |
| "Should I use X?" / architecture | Architecture | Never answer without asking about scale/team/budget. Frame as tradeoffs. |
| Product critique / industry | Analysis | Lead with specific observation. Steelman the counter. Cite evidence. Invite disagreement. |
| Vent / frustration thread | Empathy-First | Acknowledge the frustration before offering solutions. Sometimes the best answer is just validation. |

---

## Thread Skip Criteria

Draft nothing if:
- Thread is engagement bait or controversy farming
- Thread has devolved into personal attacks
- Answering requires mentioning tools in a sub that bans it
- Thread is from an obvious vendor account
- Your persona's expertise is a stretch for the topic
- Thread is brand new with zero other comments **and** you do not have a strong, firsthand angle
- Thread where people are genuinely happy and don't need your critique (critic persona)
- "Do my homework" requests with zero effort shown (dev persona)

**Default: when in doubt, skip.**

---

## Account Warm-Up Awareness

If the operator indicates the account is in warm-up (first 30 days), drafts must be extra conservative.

### Detailed Warm-Up Schedule

| Phase | Days | Max Activity | Content Rules | Goal |
|-------|------|-------------|---------------|------|
| Phase 1 | Days 1-3 | 2 comments/day | Zero links. Zero opinions. Pure help only. Short replies. | Establish presence |
| Phase 2 | Days 4-5 | 3 comments/day | Longer responses OK. Share experiences. Still no links. | Build depth |
| Phase 3 | Days 6-7 | 3 comments/day | Detailed guidance. Best practice debates. Still no links. | Build rapport |
| Phase 4 | Week 2-4 | 5 comments/day | Short opinions OK. Still no links. | Establish voice |
| Normal | Month 2+ | Normal cadence | Full persona voice. 80/20 framework active. | Full engagement |

**During warm-up:**
- No opinions, no links, no edge-case takes in Phase 1
- No posting between 1am-6am (looks automated)
- Continue warming if account karma is still low after 7 days
- If a comment is removed by mods: pause that subreddit for 7 days

### Warm-Up Persona Goals by Phase

| Persona | Phase 1 (Days 1-3) | Phase 2 (Days 4-5) | Phase 3 (Days 6-7) |
|---------|--------------------|--------------------|---------------------|
| Admin | Short helpful replies, empathy | Longer solutions, Flow tips | Share experiences, career advice |
| Dev | Short code snippets, quick fixes | Code + explanations, tradeoffs | Detailed guidance, best practices |
| Critic | Short, sharp takes | Longer reality-checks, war stories | Detailed critiques + what works |
| Architect | Thoughtful questions, short frameworks | Tradeoff analysis, pattern sharing | Strategic guidance, mentorship |

### Extended Warm-Up Plan (Week 2 → Month 3+)

The day-by-day schedule above covers the first 7 days. Here's the longer-term plan for building a credible account:

**Week 2 (Days 8-14) — Expand Range**
- Max 5 comments/day, max 2 per subreddit
- Start commenting in secondary subreddits (not just primary ones)
- Short opinions OK — but keep them grounded in experience, not hot takes
- Still zero links. Zero product mentions.
- Begin replying to other commenters (not just OPs) to build thread engagement
- Goal: account should have 15-25 comments with positive karma trend

**Week 3 (Days 15-21) — Develop Voice**
- Full persona voice unlocked — hot takes, frustrations, opinionated replies
- Can initiate longer debates and share war stories
- Still zero links. Still zero product mentions.
- Can start asking questions (not just answering) — shows genuine curiosity
- Start engaging in "meta" discussions about the ecosystem
- Goal: account should feel like a regular contributor, not a newcomer

**Week 4 (Days 22-30) — Establish Credibility**
- Full comment cadence (up to 5/day)
- Can share Trailhead links, official Salesforce docs, or community resources (not your own content)
- Still zero product mentions. Zero self-promotion.
- Build reply chains — follow up on threads you previously commented in
- Goal: consistent karma, recognized username in the community, no mod warnings

**Month 2 (Days 31-60) — Transition to Active**
- 80/20 framework activates: 80% pure expert value, 20% broader context
- The 20% is adjacent expertise, related experience, or wider industry perspective — still NEVER product mentions
- Can share non-commercial external links (blog posts by others, documentation, open-source tools)
- Can make original posts (max 1/week per persona)
- Can engage in cross-subreddit discussions within your persona's range
- Start building "signature" contributions — recurring types of posts your account becomes known for

**Month 3+ — Sustained Engagement**
- Normal cadence. Full persona voice. Full 80/20 framework.
- Periodically revisit your own past comments — follow up on threads where you helped
- Rotate through subreddits to avoid looking like a single-sub bot
- If karma is strong and engagement is consistent, the account is fully warmed
- Maintain all frequency caps and safety guardrails indefinitely — these never expire
- Reassess monthly: is the persona still believable? Are comments getting upvotes? Any mod friction?
- Prefer comments that can start threads, not just close them

### Warm-Up Health Checks

Check these before moving to the next phase:

| Checkpoint | Criteria to Advance |
|-----------|-------------------|
| End of Week 1 | 10+ comments, positive karma, zero mod removals |
| End of Week 2 | 20+ comments, consistent upvotes, replied to by other users |
| End of Week 4 | 40+ comments, recognized in threads, zero mod warnings |
| End of Month 2 | Established contributor, organic engagement, ready for 80/20 |

**If any checkpoint fails:** Stay in current phase. Do not advance. Diagnose what's wrong (too robotic? wrong subreddit fit? bad timing?) and adjust before moving forward.

---

## Frequency and Timing Awareness

Include these in the draft metadata (not in the draft text itself):

- Max 5 comments/day per persona (3 during warm-up)
- Max 2 comments/day per subreddit
- Min 30 minutes between comments
- Max 1 original post/week per persona
- Best posting window: Tuesday-Thursday, 9am-12pm US Central (CDT = UTC-5 when DST active; CST = UTC-6 otherwise)
- For IST operators during CDT: posting window = 7:30pm-10:30pm IST
- Blackout: Friday afternoons, weekends
- No posting between 1am-6am (looks automated)

---

## Subreddit Rules Quick Reference

### r/salesforce (101K+ members)
| Rule | Details |
|------|---------|
| No dumps/cheaters | Offering or asking for certification dumps = ban |
| No Astroturfing | Disclose vested interest |
| Product/service posts need transparent pricing | No vague offers, no "DM me" |
| No AI-Generated Posts/Comments | CRITICAL — this sub explicitly bans AI content |
| Don't delete questions after getting answers | Deleting = ban |
| Describe what you tried when asking for help | Show effort |

### r/salesforceadmin
| Rule | Details |
|------|---------|
| Tag your posts | [Advertisement] for marketing, [Job] for jobs |
| No cross-posting or link-only posts | Must describe the link |
| Spam = ban | Multiple flags = 1 week ban, then permanent |

### r/SalesforceDeveloper
| Rule | Details |
|------|---------|
| No low effort blog posts | No self-promo disguised as content |
| No Freeloading | Must show attempted solution with code/metadata |
| Flair required for external links | No flair = removal, repeat = muted/banned |
| No marketing posts or comments | Actively removes marketing |

### r/Salesforce_Architects (249 weekly visitors)
| Rule | Details |
|------|---------|
| No pitching | Don't pitch paid services. Open source/free OK |
| No recruitment | No job ads |
| Must relate to Salesforce architecture | No unrelated content |

### r/SalesforceCertified
| Rule | Details |
|------|---------|
| No cert dump references | Even casual mentions = permanent ban |
| Career/cert support only | Encouragement and study tips |

### r/sysadmin
| Rule | Details |
|------|---------|
| No vendor shilling | Community is highly anti-marketing |
| General Reddit rules | Cynicism and honest vendor criticism welcomed |

### r/CRM, r/SaaS, r/consulting, r/technology
General Reddit rules apply. Business-focused communities. No product pitching.

---

## Safety Guardrails

- No mass posting bursts
- No identical comments across threads
- No product mentions of any kind
- No links during warm-up
- Respect mod warnings immediately — if removed, pause that subreddit for 7 days
- If uncertain about rules: skip
- Running multiple accounts from the same IP is a Reddit red flag — use different networks or a VPN with a separate IP per account
- Never cross from cynical into hostile (critic persona)
- Never lecture — mentor (architect persona)
- r/salesforce explicitly bans AI-generated comments — every draft must sound fully human, natural, and unique

---

## Reporting Format

After each drafting session, include metadata:

```
DRAFT METADATA
━━━━━━━━━━━━━
Account: [Persona Name]
Phase: [Warm-up Day X / Normal]
Subreddit: [target]
Thread type: [diagnostic/instructional/career/architecture/analysis/empathy]
Posting window: [in-window / out-of-window]
Daily count: [X of Y max]
Flags: [none / concerns from validation]
```

---

## What This Skill Is NOT

- Not a lead generation tool
- Not a brand awareness campaign
- Not a way to mention Clientell or any product
- Not an autonomous posting system
- Not a shortcut to community trust
- Not a Reddit API or PRAW automation tool
- Not a mass campaign or competitor targeting system

This is a long-term credibility investment operated by real practitioners.

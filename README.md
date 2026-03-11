# Reddit Salesforce Community Growth Skill

A drafting engine for high-quality Reddit engagement across four Salesforce expert personas.

## What This Is

A **draft-only** skill that generates Reddit comments for human review. It never posts autonomously. Every draft must be rewritten by the operator in their own voice before manual posting.

This supports both **account warm-up** (first 30 days — pure community help, zero promotion) and **ongoing engagement** (80% expert value, 20% broader context).

## Structure

```
reddit_skill/
├── SKILL.md                 # Unified skill — workflow, constraints, frameworks
├── references/
│   ├── admin.md             # Ava — 5yr accidental admin, Flow addict
│   ├── dev.md               # Marcus — 7yr developer, code-first
│   ├── critic.md            # trust_the_demo — 10yr veteran realist
│   └── architect.md         # depends_on_context — 12yr systems thinker
├── scripts/
│   └── validate.py          # Automated draft validation
└── README.md
```

## How It Works

1. Provide: **thread text** + **persona** (admin/dev/critic/architect) + **subreddit**
2. Skill checks global constraints, loads the persona reference
3. Generates draft following 80/20 framework and reply type matching
4. Runs `scripts/validate.py` to catch AI patterns, product mentions, rule violations
5. Presents draft as **DRAFT — FOR HUMAN REVIEW** with metadata

## Personas

| Persona | Display Name | Experience | Voice | Primary Subreddits |
|---------|-------------|------------|-------|-------------------|
| Admin | Ava | 5 years | Warm, practical, empathetic | r/salesforce, r/salesforceadmin |
| Developer | Marcus | 7 years | Technical, precise, code-first | r/SalesforceDeveloper, r/salesforce |
| Critic | trust_the_demo | 10+ years | Analytical, measured, realist | r/CRM, r/sysadmin, r/salesforce |
| Architect | depends_on_context | 12+ years | Strategic, framework-oriented | r/Salesforce_Architects, r/salesforce |

## Non-Negotiable Rules

- **Draft-only** — never posts autonomously
- **Zero product mentions** — no Clientell, no commercial tools, no CTAs
- **Zero AI signals** — no "Great question!", no bullet-heavy formatting
- **Persona isolation** — personas never interact with each other
- **Subreddit compliance** — r/salesforce explicitly bans AI-generated content

## Validation

```bash
python scripts/validate.py "your draft text here"
# or
echo "your draft text" | python scripts/validate.py
```

Checks for: AI disclosure patterns, product mentions, URLs, cert dump references, structural quality.

## Account Warm-Up

For new accounts (first 30 days), drafts are extra conservative:
- **Days 1-3:** Max 2 comments/day, pure help, short replies
- **Days 4-7:** Max 3 comments/day, longer responses, still no links
- **Week 2-4:** Max 5 comments/day, opinions OK, still no links
- **Month 2+:** Full persona voice, 80/20 framework active

See `SKILL.md` for the complete warm-up schedule and constraints.

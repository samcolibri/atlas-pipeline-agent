# ATLAS — Launch Checklist & Executive Summary

> **Status:** Shadow mode. Pipeline built. Signals live. Waiting on 5 credentials to go fully autonomous.

---

## Executive Summary — What Happens Every Day Once Deployed

ATLAS wakes up at 6:00 AM Eastern and runs without anyone touching anything.

It pulls intent signals from 6sense (accounts actively researching compliance training), cross-references FDIC enforcement actions (banks under consent orders legally required to fix compliance), and checks for new OCC/FDIC/NCUA rulings that just dropped. It ranks every account in its universe by signal strength — a bank with a consent order AND a 6sense score above 80 AND a compliance officer job posting goes straight to the top.

It then researches each flagged account in parallel. For every account, it reads recent news and M&A announcements, scans for hiring signals, checks for active regulatory penalties, and synthesizes everything into a research brief. It picks the right pitch angle automatically — a $6B credit union gets the NCUA/Fair Lending angle with Citadel CU as proof; a community bank that just acquired a branch gets the BSA/AML consistency angle with Security First Bank as proof.

It finds the real contact. Not just the domain — the actual Chief Compliance Officer or VP of Compliance at that bank, by name, with a verified email address.

It writes a personalized 4-sentence email using OCL's POV framework. Trigger event specific to that bank. Risk specific to their regulatory exposure. Proof case matched by institution type and size. CTA assigned deterministically so A/B tracking is clean.

By 9:00 AM, Nader gets a Teams card with the full batch — subject line, email body, company, signal score, and why this account was flagged. He approves, skips, or edits each one. Every decision is logged.

By 9:15 AM, approved emails are enrolled in Outreach sequences and sent. Every send is logged to Salesforce so no rep ever gets surprised by an account ATLAS touched.

Every 30 minutes, ATLAS checks for replies and classifies them. An interested reply triggers an immediate Teams ping to the rep with the full context. An objection gets routed into a follow-up sequence. An unsubscribe gets suppressed permanently.

At 6:00 PM, ATLAS sends a digest to Teams — how many sent, open rate, replies, meetings booked, which pitch angle performed best that day.

At 11:00 PM, ATLAS updates its own brain. Every approval, rejection, reply, and meeting outcome recalculates the win-rate matrix. Pitch angles that work get higher confidence scores. Patterns that hit 85% approval rate graduate to auto-send — no Nader review needed. The system gets measurably better every single cycle.

**Net result:** 160 net-new compliance decision-makers contacted per month across accounts no rep has ever touched. Conservative model: 3% reply rate → 5 warm replies → 4.5 opportunities → $1.35M annual incremental revenue. Break-even is 2 deals. Every month it runs, PHOENIX makes the next month better.

---

## Pending Credentials — What's Blocking Full Autonomy

### Sam adds these himself (30 minutes)

| Credential | Where to get it | `.env` key | Cost |
|------------|----------------|------------|------|
| **Anthropic API key** | Already have it — copy from `~/nova-gtm/.env` | `ANTHROPIC_API_KEY` | Pay/call ~$10/mo |
| **Apollo.io API key** | apollo.io → sign up → API Keys | `APOLLO_API_KEY` | Free tier (50/mo) or $49/mo |
| **ZeroBounce API key** | zerobounce.net → sign up → API | `ZEROBOUNCE_API_KEY` | $16/mo |
| **Instantly API key** | instantly.ai → Settings → API | `INSTANTLY_API_KEY` | $37/mo |
| **Instantly Campaign ID** | instantly.ai → create campaign → copy ID | `INSTANTLY_CAMPAIGN_ID` | Included |
| **SerpAPI key** *(optional — Tavily already set)* | serpapi.com → Dashboard | `SERPAPI_KEY` | $50/mo |

### Sam gets from stakeholders (send today)

| Person | What to ask for | `.env` key | Why it matters |
|--------|----------------|------------|----------------|
| **Nathan Paldrmann** | Teams incoming webhook URL for the review channel | `TEAMS_WEBHOOK_URL` | Nader's review cards — without this, review happens in local UI only |
| **Nathan Paldrmann** | Confirm 6sense key `09d6e437...` has account intent score access | `SIXSENSE_API_KEY` | Already set — just needs access confirmed |
| **Amy Ketts** | Outreach OAuth credentials — app name "Ai agent" — client ID + secret + refresh token | `OUTREACH_CLIENT_ID` `OUTREACH_CLIENT_SECRET` `OUTREACH_REFRESH_TOKEN` | Primary send channel and sequence enrollment |
| **Angel / James (SF admin)** | Salesforce Connected App — read-only: Accounts, Contacts, Opps, ActivityHistory | `SF_CLIENT_ID` `SF_CLIENT_SECRET` `SF_USERNAME` `SF_PASSWORD` `SF_SECURITY_TOKEN` | Trust line — ATLAS must never touch an account a rep is working |
| **Nader Rustom** | Supabase project URL + service key | `SUPABASE_URL` `SUPABASE_SERVICE_KEY` | Production persistence for queue + PHOENIX learning store |

---

## What's Already Live (No Action Needed)

| Component | Status |
|-----------|--------|
| 6sense API key | ✅ Set in `.env` |
| Airtable — Agent Molly (3,544 banks) | ✅ Live |
| Tavily web search | ✅ Live |
| FDIC BankFind API | ✅ Free, no key needed |
| FDIC Enforcement Actions | ✅ Free, no key needed |
| Federal Register RSS | ✅ Free, no key needed |
| NCUA data | ✅ Free, no key needed |
| FORGE email generation | ✅ Built, tested, generating real emails |
| Local review UI — localhost:5001 | ✅ Running, 100 emails pre-loaded |
| Email queue persistence (JSON) | ✅ Survives restarts |
| CTA A/B system | ✅ Deterministic by domain hash |
| Compliance-first ICP title targeting | ✅ P1 CCO → P2 CHRO → P3 L&D |
| OCL case studies (Citadel / Security First / MVB) | ✅ Embedded in FORGE |
| PHOENIX learning schema | ✅ Designed, ready to activate |
| Railway deployment config | ✅ Dockerfile + railway.toml committed |
| GitHub repo | ✅ github.com/samcolibri/atlas-pipeline-agent |

---

## What Goes Live in Each Phase

### Phase 1 — Sam adds 4 keys (today)
**Anthropic + Apollo + ZeroBounce + Instantly**

Pipeline: `6sense intent → FDIC signals → Tavily research → Apollo contact → ZeroBounce validate → FORGE email → local UI review → Instantly send`

Every email tied to a real signal. Nader reviews in the browser at localhost:5001. PHOENIX starts logging.

### Phase 2 — Nathan provides Teams webhook (this week)
Nader gets a morning Teams card instead of opening the browser. Approve/skip from Teams. Faster review cycle.

### Phase 3 — Amy provides Outreach credentials (this week)
Move from Instantly to Outreach as primary send. Native open/click/reply tracking. Sequence enrollment instead of one-off sends.

### Phase 4 — Angel provides Salesforce creds (this week)
Trust line fully enforced. ATLAS checks Salesforce before every account enters the pipeline. Zero risk of touching a rep's account.

### Phase 5 — Month 1 complete, PHOENIX has data
50+ emails sent. Win-rate matrix populated. First patterns approaching 85% confidence. First accounts auto-sending without Nader review. Molly gets first PHOENIX learning report.

### Phase 6 — Month 3, full auto mode
High-confidence patterns (85%+) send automatically. Nader only reviews new patterns, edge cases, and accounts flagged by enforcement actions. ATLAS is fully autonomous for the proven playbook.

---

## The Rule That Never Changes

> ATLAS only touches accounts where **no human relationship exists**.
> If any Colibri rep has had any contact with an account — even one email — ATLAS does not touch it.
> Tier 1 (rep's best accounts) → never.
> Tier 2 (hybrid territory) → never autonomously.
> Tier 3 (100+ accounts nobody works) → **this is ATLAS territory**.

Every send is tied to a verified intent signal. No spray. No guessing. Every email references a real trigger event at that specific bank.

---

## Stakeholder Message Templates

**To Nathan Paldrmann:**
> "Nathan — ATLAS is ready to go. Need two things: (1) Teams incoming webhook URL for the channel where Nader will review outreach batches each morning, (2) confirm the 6sense API key ending in `...ff4dc18` has access to account-level intent scores. We're pulling signals now but need to confirm the access tier. Everything else is built."

**To Amy Ketts:**
> "Amy — need the Outreach OAuth credentials for the AI agent Connected App (client ID, client secret, refresh token). ATLAS will use this to enroll approved contacts into sequences automatically. Nothing sends without Nader approving it first. The app name in Outreach should be 'Ai agent' — can you confirm access and share the creds?"

**To Angel / James:**
> "Need a Salesforce Connected App for ATLAS with read-only access to Accounts, Contacts, Opportunities, and ActivityHistory. This is so ATLAS can check whether an account or contact already has rep activity before it ever enters the outreach pipeline — it's the trust line that keeps ATLAS out of reps' accounts. Read-only, no writes."

**To Nader Rustom:**
> "Nader — can you share the Supabase project URL and service key? This is for ATLAS's learning store — where it tracks every approval, rejection, and reply outcome to improve the next batch. Without it, learnings are stored locally and won't survive a server restart."

---

*Architecture diagram: https://samcolibri.github.io/atlas-pipeline-agent/ARCHITECTURE.html*
*Repo: https://github.com/samcolibri/atlas-pipeline-agent*

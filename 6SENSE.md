# 6sense API — ATLAS Integration Guide

**Purpose:** SCOUT agent uses 6sense to identify net new Tier 3 accounts that are actively in a buying cycle. Read-only. ATLAS never writes to 6sense.

---

## What We Use 6sense For

ATLAS is a net-new-first pipeline agent. 6sense is the signal source that tells us **which companies we've never touched are actively researching GRC/compliance solutions right now** — so ATLAS targets them before competitors do.

- **SCOUT** → pulls weekly batch of in-market Tier 3 accounts
- **RECON** → gets full account details per company before FORGE writes outreach

---

## Step 1: Get the API Key

**Who can do this:** Colibri marketing team / 6sense admin (whoever manages ABM segments).

1. Log in at **`app.6sense.com`**
2. Gear icon (top right) → **Settings**
3. Navigate to **Integrations → API Configuration**
4. Click **Generate API Key**
   - Name: `ATLAS Pipeline Agent`
   - Permissions: **Read-only**
5. Copy the key → add to `.env`:

```
SIXSENSE_API_KEY=your_key_here
```

> **If API isn't on your plan:** Contact your 6sense Customer Success Manager (CSM) to enable it. Fallback: use manual CSV export (see bottom of this doc).

---

## Step 2: The Two API Calls ATLAS Makes

### Call 1 — SCOUT: Weekly Net New Account Pull

Pulls the top 100 Tier 3 accounts actively in a buying cycle this week.

```
GET https://api.6sense.com/v3/company/search

Headers:
  Authorization: Token <SIXSENSE_API_KEY>
  Content-Type: application/json

Body:
{
  "filter": {
    "buying_stage": ["Decision", "Purchase"],
    "industry": ["Financial Services", "Banking"],
    "intent_score": { "gte": 70 }
  },
  "sort": { "intent_score": "desc" },
  "limit": 100
}
```

**Returns per account:**
| Field | Description |
|-------|-------------|
| `company` | Company name |
| `domain` | Company domain (used as unique ID) |
| `industry` | Industry vertical |
| `employee_count` | Headcount band (e.g. "501-1000") |
| `buying_stage` | Awareness / Consideration / Decision / Purchase |
| `intent_score` | 0-100, how actively they're researching |
| `intent_topics` | What they're researching (e.g. "GRC software", "compliance automation") |
| `location` | HQ city + state |

**Logic:** intent score ≥ 70 + Decision or Purchase stage = account is deep in a buying cycle right now. This is SCOUT's Tier 3 net new list for the week.

---

### Call 2 — RECON: Full Account Details

Called per account before FORGE generates outreach. Gives RECON enough context to write a personalized research brief.

```
GET https://api.6sense.com/v3/company/details?domain=example.com

Headers:
  Authorization: Token <SIXSENSE_API_KEY>
```

**Returns:**
- Full firmographics (revenue band, headcount, tech stack)
- Page visit activity (which Colibri pages they visited + frequency)
- Trending intent topics (what they're researching most this month)
- Buying stage history (how long they've been in-market)

RECON feeds this into Claude to generate the account brief that FORGE uses to write the first outreach email.

---

## Step 3: What Sales Leaders Must Confirm Before ATLAS Goes Live

These are human judgment calls — the API data is only as useful as the configuration behind it.

| Question | Who Answers | Why It Matters |
|----------|-------------|----------------|
| Which 6sense segments are configured for FS/GRC? | Marketing / 6sense admin | Segments set by marketing may not match what sales considers "in market" |
| Does intent score ≥ 70 feel right as a threshold? | Nader Rustom | Too low = noise, too high = misses real prospects |
| Should we include Consideration stage or just Decision/Purchase? | Nader Rustom | FS deals may start earlier in the funnel |
| Manually validate top 20 intent accounts — do they look like real prospects? | Nader Rustom / Nathan Paldrmann | Catches brand-mixing issues before ATLAS sends anything |

**Do not skip the top-20 manual validation.** The ATLAS docs flag brand mixing as a known risk — 6sense may attribute intent to accounts researching a competitor's product, not Colibri's. One 20-minute review with Nader prevents ATLAS from targeting garbage accounts at scale.

---

## Known Risk: Brand Mixing

From the pipeline audit (`docs/FS Pipeline AI Report.pdf`, p.9):

> *"Assuming we fix the issue of 'brand mixing' in the intent data..."*

6sense intent signals are sometimes attributed to Colibri that are actually for adjacent brands in the ecosystem. Until this is resolved with the 6sense CSM:

1. Pull top 20 accounts by intent score
2. Have Nader/Nathan manually verify: "Do these look like real GRC prospects?"
3. Track intent-to-reply correlation after Month 1 — if intent score 90 and intent score 50 have the same reply rate, the signal is noise
4. If signal quality is poor, SCOUT falls back to firmographic-only targeting (see below)

---

## Fallback: Manual CSV Export

If API access isn't available on the current 6sense plan:

1. In 6sense: **Segments → select FS/GRC segment → Export → CSV**
2. Drop file at: `data/6sense_export.csv`
3. SCOUT reads the CSV automatically instead of calling the API
4. Re-export weekly (or configure a scheduled SFTP export if available in your plan)

Same net new targeting logic — just manual refresh instead of real-time API.

---

## Environment Variable

```bash
# .env
SIXSENSE_API_KEY=your_key_here
```

`.env.example` already includes this key. See `PLAYBOOK.md §4` for full setup steps.

---

## Files That Use This

| File | What It Does |
|------|-------------|
| `atlas/agents/scout.py` | SCOUT agent — calls company/search weekly |
| `atlas/clients/sixsense.py` | 6sense API wrapper |
| `data/6sense_export.csv` | CSV fallback (drop file here) |

---

## Quick Reference

| Item | Value |
|------|-------|
| API base URL | `https://api.6sense.com/v3/` |
| Auth header | `Authorization: Token <key>` |
| Access level needed | Read-only |
| Who generates key | 6sense admin (Colibri marketing team) |
| Where to add key | `.env` → `SIXSENSE_API_KEY` |
| SCOUT pulls | Every Monday at 9am (cron) |
| Intent score floor | 70 (confirm with Nader before go-live) |
| Buying stages targeted | Decision, Purchase |
| Account limit per pull | 100 |

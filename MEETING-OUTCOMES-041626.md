# ATLAS — Meeting Outcomes (April 16, 2026)

---

## Decisions Made

### 1. ATLAS = Tier 3 Account Engine

Reps work accounts in 3 tiers. ATLAS owns Tier 3.

| Tier | Volume | How It's Worked | ATLAS Role |
|------|--------|----------------|------------|
| **Tier 1** | 5-25 accounts | Deep research, rich POV, heavy personalization, human-driven outreach | AI Research Agent — generates briefs, rep writes the outreach |
| **Tier 2** | ~50 accounts | Hybrid — human judgment + AI acceleration, moving faster | Partial automation — AI drafts, human edits and sends |
| **Tier 3** | 100+ accounts | Nobody touches these today. Too many accounts, too much work per account. | **Full ATLAS autonomy** — find, research, write, send, monitor |

**The principle:** AI is best where trust hasn't been created yet. Once a rep has engaged and built rapport — even a single good touchpoint — that account belongs to the human. ATLAS operates exclusively in the space before any human relationship exists.

**What this means for the product:** ATLAS doesn't compete with rep workflow. It works the accounts reps would never get to. Zero friction, zero politics.

---

### 2. Confirmed Scope: Prospecting Only (Prospect → Opportunity)

ATLAS handles the journey from unknown account to booked meeting. Everything after that is human.

```
ATLAS SCOPE:
  Unknown account → Intent signal detected → Researched → 
  Personalized outreach → Reply → Meeting booked

  ════════════ HANDOFF ════════════

HUMAN SCOPE:
  Meeting → Discovery → Demo → Proposal → Negotiation → Close
```

No automation on:
- Active opportunities (any stage)
- Stale opportunities (rep has context)
- Closed-lost re-engagement (sensitive — future phase after trust is earned)
- Any account where a rep has had a meaningful touchpoint

---

### 3. Tier 1 AI Research Agent = Separate Product

Tier 1 accounts need AI for research, not outreach. This is a different use case:

| | ATLAS (Tier 3) | AI Research Agent (Tier 1) |
|-|---------------|---------------------------|
| **Purpose** | Autonomous prospecting | Research assistance for reps |
| **Output** | Sends emails, books meetings | Delivers account briefs, reps decide what to do |
| **Autonomy** | Full (with human review gate) | Zero — purely informational |
| **Volume** | 100+ accounts/month | 5-25 accounts at any time |
| **Depth** | Fast research (30-60 seconds) | Deep research (competitor analysis, stakeholder mapping, POV generation) |

Both products use the same RECON engine underneath. Different wrappers, different audiences, different value props.

---

### 4. FS Is the Pilot. All 6 Ecosystems Are the Target.

Colibri has 6 ecosystems and ~30 brands. Each one has the same pipeline problem. The confirmed rollout strategy:

```
PHASE 1: Financial Services (now)
  → Prove the model: ATLAS on Tier 3 FS/GRC accounts
  → Measure: reply rate, meetings booked, pipeline created
  → Timeline: 4-8 weeks for proof

PHASE 2: Expand across Colibri
  → Take the proven FS model and deploy to other ecosystems
  → Each ecosystem has its own ICP, personas, triggers — 
     but the agent architecture is the same
  → This is a configuration change, not a rebuild

PHASE 3: Beyond Colibri
  → Productize as SaaS for external companies
  → Every B2B company with SDRs has the same Tier 3 problem
```

---

### 5. This Is Additive, Not Replacement

If ATLAS works, the outcome is:
- More pipeline generated (from Tier 3 accounts nobody was working)
- More meetings booked (from accounts reps would never reach)
- SDRs refocused on Tier 1-2 (higher-value, human-driven work)
- Company hires more closers (AEs) to handle increased pipeline

ATLAS doesn't reduce headcount. It increases the work that justifies headcount.

---

## Updated Product Architecture

Based on meeting outcomes, ATLAS is now two products on one engine:

```
                    ┌──────────────────────┐
                    │     RECON ENGINE     │
                    │  (AI Research Core)  │
                    │                      │
                    │  • Account research  │
                    │  • Persona matching  │
                    │  • Trigger detection │
                    │  • Brief generation  │
                    └──────────┬───────────┘
                               │
                 ┌─────────────┴─────────────┐
                 │                           │
    ┌────────────┴────────────┐  ┌───────────┴───────────┐
    │   ATLAS (Tier 3)        │  │  RESEARCH AGENT       │
    │   Autonomous Prospector │  │  (Tier 1 Assistant)   │
    │                         │  │                       │
    │  SCOUT → RECON → FORGE  │  │  RECON → Brief →     │
    │  → Outreach → Monitor   │  │  Deliver to Rep       │
    │  → Learn                │  │                       │
    │                         │  │  No outreach.         │
    │  Full autonomy.         │  │  Research only.       │
    │  Human review gate.     │  │  Rep decides action.  │
    │  100+ accounts/month.   │  │  5-25 accounts.       │
    └─────────────────────────┘  └───────────────────────┘
```

---

## Updated Exclusion Rules

The tier framework simplifies exclusions further:

```
ATLAS ONLY TOUCHES:
  ✓ Net new accounts (never in Salesforce)
  ✓ 6sense intent-scored accounts above threshold
  ✓ Accounts with NO prior rep engagement of any kind
  ✓ Accounts with NO existing relationship or touchpoint
  ✓ Stale LEADS (pre-opportunity, no human relationship)

ATLAS NEVER TOUCHES:
  ✗ Any account a rep has engaged with (even one good touchpoint)
  ✗ Any account in Tier 1 or Tier 2 (rep is already working it)
  ✗ Active opportunities (any stage)
  ✗ Stale opportunities (human-owned)
  ✗ Closed-lost (future phase)
  ✗ Current customers
  ✗ Accounts in Farside/Agentforce pipeline
```

The test is simple: **Has any rep had any meaningful contact with this account? If yes, ATLAS doesn't touch it.**

---

## Revised Success Metrics

| Metric | Target | Why It Matters |
|--------|--------|---------------|
| **Tier 3 accounts worked/month** | 160+ | Accounts that would otherwise get zero attention |
| **Reply rate on Tier 3** | 3-5% | Any reply is net new — these accounts weren't being contacted |
| **Meetings booked from Tier 3** | 5-8/month | Pure additive pipeline |
| **Pipeline created from Tier 3** | $375K-$600K/quarter | Revenue that didn't exist before ATLAS |
| **Rep time spent on ATLAS output** | <5 min/day | ATLAS shouldn't add work for reps |
| **Tier 1 research brief quality** | Rep approval >90% | Research agent is useful, not noise |
| **Zero incidents on Tier 1-2 accounts** | 0 | ATLAS never contacts a rep's active account |

---

## Immediate Next Steps

| # | Action | Status |
|---|--------|--------|
| 1 | Get API credentials (Salesforce, Outreach, 6sense) | Awaiting |
| 2 | Deploy agent skeleton to Railway | Ready (repo has Dockerfile + railway.toml) |
| 3 | Connect APIs as credentials arrive | Ready to build |
| 4 | Run first shadow cycle on Tier 3 accounts | Blocked on #1 |
| 5 | Generate first batch of research briefs + outreach for review | Blocked on #1 |
| 6 | Follow-up meeting (April 17) | Scheduled |

---

## The One-Liner

**ATLAS works the 100+ accounts your reps would never get to — finds them, researches them, writes personalized outreach, and hands off warm replies. Reps focus on Tier 1-2. ATLAS handles the rest.**

---

*ATLAS — Autonomous Territory & Lead Acceleration System*
*samcolibri/atlas-pipeline-agent*

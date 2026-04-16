# ATLAS — Revised Strategy: Net New First

**Context:** Stakeholder feedback recommends starting ATLAS on the 93% untouched market (net new accounts from 6sense) rather than the closed-lost pool. Closed-lost is a sensitive topic with the sales team. A call is being scheduled to discuss.

**Our response: This is the right call. Here's why, and here's how it changes the plan.**

---

## Why Net New First Is Actually Better

The original plan led with PHOENIX (closed-lost recovery) because the data was already in Salesforce — fastest path to first send. But starting with net new is better for three reasons the data alone doesn't show:

### 1. Zero Political Risk

Closed-lost deals have history. Every one of those $5.5M in lost opportunities has an AE who lost it, a reason it was lost, and potentially a story about whose fault it was. The moment ATLAS starts re-engaging those accounts, it surfaces questions nobody wants to answer right now:

- "Why wasn't anyone following up on this $180K deal?"
- "Who lost this account and why?"
- "Why has $5.5M been sitting here for 2 years with no automation?"

These are valid questions — but they're landmines for an agent that hasn't proven itself yet. If ATLAS's first visible action is poking at the sales team's past losses, it creates resistance before it creates results.

**Net new accounts have no history, no baggage, no bruised egos.** Nobody "lost" an account that's never been in Salesforce. There's no story to contradict, no rep to offend, no deal to relitigate. It's pure greenfield.

### 2. Cleaner Data, Fewer Edge Cases

Closed-lost data has every problem we identified in the data hygiene analysis:
- Free-text loss reasons (can't auto-segment reliably)
- Contacts who may have changed jobs, companies, or roles
- Accounts that may have been re-engaged informally (off-system conversations)
- Potential overlap with active deals at the same company
- Griffin's phantom activity contaminating "last touch" data

**Net new accounts from 6sense have none of these problems:**
- Fresh data, enriched by 6sense at the time of pull
- No Salesforce history to conflict with
- No prior Colibri relationship to damage
- No rep ownership to navigate
- Clean contact data from 6sense enrichment

The exclusion framework becomes dramatically simpler:

```
CLOSED-LOST EXCLUSIONS NEEDED:        NET NEW EXCLUSIONS NEEDED:
─────────────────────────────         ─────────────────────────
✗ Current customers                   ✗ Current customers
✗ Active opportunities                ✗ Active opportunities  
✗ Recently contacted                  (that's basically it)
✗ Griffin phantom activity
✗ Unstructured loss reasons
✗ Contact job changes
✗ Informal re-engagement history
✗ Rep sensitivity
✗ Very high-value accounts (human)
```

Half the exclusion logic disappears. Half the edge cases disappear. The agent is simpler, faster to build, and less likely to misfire.

### 3. Proves the Value Before Touching Sensitive Ground

If ATLAS generates meetings from accounts nobody has ever contacted, the value is undeniable:

- "We found 28 accounts showing buying intent that weren't in our CRM"
- "We reached out with personalized messaging based on their specific compliance needs"
- "3 of them replied. 1 meeting is scheduled. Pipeline value: $75K"

**That's new money from thin air.** No rep can say "I was going to do that." No AE can say "that was my account." It's purely additive pipeline that didn't exist before ATLAS.

Once ATLAS has proven itself on net new — once the team has seen the reply rates, the quality of the research briefs, the precision of the persona matching — THEN the conversation about closed-lost becomes natural:

*"ATLAS is generating 3-5% reply rates on cold outreach to accounts that have never heard of us. Imagine what it could do with warm accounts that already know our product and lost for a specific, addressable reason."*

That's a pull conversation, not a push. The sales team asks for PHOENIX instead of having it imposed on them.

---

## The Revised Plan

### What Changes

| Component | Before | Now |
|-----------|--------|-----|
| **Phase 1 lead agent** | PHOENIX (closed-lost) | SCOUT + FORGE (net new) |
| **Data source** | Salesforce closed-lost opps | 6sense intent signals → net new accounts |
| **First send target** | 50 closed-lost re-engagement emails | 50 net new personalized outreach emails |
| **Political risk** | Medium-high (touching sensitive deals) | Zero (greenfield accounts) |
| **Data quality risk** | High (dirty SF data, free-text fields) | Low (fresh 6sense enrichment) |
| **PHOENIX timing** | Phase 1 (Week 1-4) | Phase 3 (after ATLAS has proven value) |
| **Revenue timeline** | Faster first reply (warm accounts) | Slightly slower (cold outreach) but cleaner |

### What Stays the Same

- RECON (AI research briefs) — same, works for any account
- FORGE (personalized outreach) — same, persona-matched messaging
- SENTINEL (data quality) — simpler but still needed for dedup
- VITALS (pipeline health) — still runs in parallel for stale alerts
- Human review gate — still in place, Nader reviews everything
- COMMAND (reporting) — still tracks all KPIs
- The financial model — net new is the $1.35M/year engine anyway

---

## Revised Implementation Timeline

### Phase 1: Net New Pipeline Engine (Weeks 1-6)

| Week | What Happens | Deliverable |
|------|-------------|-------------|
| **1** | Connect APIs (Salesforce, Outreach, 6sense, Claude). Pull first 6sense intent list. Validate top 20 accounts with Nader/Nathan — are these real prospects? | API connections tested. Intent signal quality validated. |
| **2** | RECON generates research briefs for top 50 accounts. FORGE generates persona-matched outreach (3 variants: compliance, HR/L&D, operations). | 50 briefs + 100 email variants ready for human review. |
| **3** | Nader reviews everything. Approves/edits/rejects. First batch of 25 approved emails goes out via Outreach. | First ATLAS emails land in real inboxes. |
| **4** | Monitor replies, deliverability, open rates. Second batch of 25-50 sends. Adjust messaging based on early data. | First reply rate data. Compare to Q1 baseline (0.6%). |
| **5-6** | Scale to full pipeline: 80-160 accounts/month. A/B testing active. Learning engine recording outcomes. | Steady-state net new outbound engine running. |

**Phase 1 Exit Criteria:**
- Reply rate measurably above Q1 baseline
- First meeting booked from ATLAS-sourced outreach
- Team sees the quality of AI-generated research + messaging
- Zero incidents (wrong person, current customer, embarrassing email)

### Phase 2: Stale Leads + Inbound (Weeks 4-8)

| Week | What Happens | Deliverable |
|------|-------------|-------------|
| **4-5** | VITALS: stale **lead** detection (8-day inactivity trigger). Auto-alert assigned rep. Route post-sequence "No Reply" leads to nurture or re-queue. **Note: Stale opps are excluded — once a lead becomes an opportunity, the human relationship is the focal point. Reps have deeper context on their opps and the volume is manageable without automation.** | Reps getting proactive alerts on stale leads via Teams. 169 stuck "Attempting Contact" leads unstuck. |
| **6-7** | Inbound automation: "Contact Sales" form → personalized response in <5 minutes. | Speed-to-first-touch drops from days to minutes. |
| **8** | COMMAND: automated weekly digest to leadership. KPI dashboard. | Molly/Scott getting pipeline health reports without anyone building spreadsheets. |

### Phase 3: Closed-Lost Recovery — PHOENIX (Weeks 8-12)

**Only after ATLAS has earned trust through Phase 1-2 results.**

| Week | What Happens | Deliverable |
|------|-------------|-------------|
| **8-9** | Present Phase 1 results to sales leadership. Propose PHOENIX as next step: "ATLAS is generating X% reply rates on cold outreach. Here's what it could do with warm accounts." | Sales team buy-in for closed-lost re-engagement. |
| **9** | Classify closed-lost reasons (Claude + human validation). Segment $5.5M pool. | Clean, structured closed-lost segments ready for sequences. |
| **10-11** | Build 3 PHOENIX sequences (Contract Timing, Budget Deferred, Platform). Nader reviews all. First batch of 25-50 sends. | First closed-lost re-engagement emails out (with full team support). |
| **12** | Scale PHOENIX. Track re-open rates. Report recovered pipeline. | Closed-lost recovery engine running alongside net new engine. |

### Phase 4: Full Autonomy (Weeks 10-16)

Same as before — COACH, CORTEX full orchestration, learning loop, confidence gate graduation.

---

## The Bright Line: What ATLAS Owns vs. What Stays Human

This feedback crystallizes a clear principle: **ATLAS operates where no human relationship exists yet. The moment a human relationship is established, the human owns it.**

```
ATLAS TERRITORY (autonomous)          HUMAN TERRITORY (rep-owned)
──────────────────────────           ──────────────────────────

Net new accounts (93% of market)     Active opportunities (all stages)
  → 6sense intent identification       → Rep has context, history, rapport
  → AI research & enrichment           → Human judgment closes deals
  → Personalized first outreach        → Not enough volume to justify automation
  → Multi-step sequence management     → Automation here risks the relationship

Stale LEADS (pre-opportunity)        Stale OPPS (post-qualification)
  → No human relationship yet          → Already had discovery/demo/proposal
  → Lead went cold in sequence          → Rep knows why it stalled
  → ATLAS re-engages or nurtures        → Rep re-engages with full context
  → 169 stuck leads = real volume       → 380 opps = manageable for reps

Inbound form responses               Closed-lost deals
  → Speed matters (< 5 min)            → Sensitive history with sales team
  → No rep relationship yet             → "Who lost this?" is a loaded question
  → Personalized acknowledgment         → Future phase — after trust is earned
  → Route to rep with full context       → Team will ask for it, not have it pushed

Research & enrichment                Deal progression & negotiation
  → Account briefs for any account      → AE handles proposal → close
  → Buying committee mapping            → CPQ, pricing, legal = human domain
  → Competitive landscape               → Ironclad / contract work = human

Pipeline REPORTING                   Pipeline COACHING
  → Automated KPI dashboards            → Manager-to-rep conversations
  → Weekly digest to leadership          → Call review and feedback
  → Attribution tracking                 → Performance management
```

**The rule of thumb:** If a prospect has ever had a real conversation with a Colibri rep — a discovery call, a demo, a proposal review — that relationship belongs to the human. ATLAS feeds the top of the funnel and monitors lead health. Humans own everything from first meeting forward.

This is the right boundary. It means ATLAS can never embarrass the team by stepping on an active relationship, and the sales team sees ATLAS as the thing that gives them more at-bats, not the thing that second-guesses their deals.

---

## Revised Revenue Model

Starting with net new shifts the revenue timing slightly but doesn't change the total:

| Revenue Stream | Original Timeline | Revised Timeline | Dollar Impact |
|---------------|------------------|-----------------|---------------|
| Net new outbound pipeline | Month 2-3 | **Month 1-2** (now first, not second) | $1.35M annual (unchanged) |
| Pipeline health (stale reactivation) | Month 1-2 | Month 2-3 | $500K-$900K 90-day (unchanged) |
| Closed-lost recovery (PHOENIX) | Month 1-2 | **Month 3-4** (delayed, by design) | $1.0-$1.4M 12-month (unchanged) |
| **Total Year 1** | | | **$2.85M-$4.5M (unchanged)** |

**The total addressable impact doesn't change.** We just sequence it smarter — lead with what's politically clean and technically simple, prove value, then expand to the sensitive territory with credibility and data behind us.

---

## What This Means For the Call

Going into the discussion, here's where we stand:

### Aligned
- Fully agentic solution is the right goal
- Start with net new (93% untouched market), not closed-lost
- Human review gate before any outreach sends
- Nader stays in the loop as strategist + quality gate
- Stale **leads** are fair game for ATLAS (pre-opportunity, no human relationship yet)
- Stale **opps** stay human-owned (already had human touchpoints, reps have deeper context, and the volume is manageable — human relationships close deals)

### Need to Discuss on the Call
1. **6sense intent signal validation** — Who validates the first batch of accounts? Nader + Nathan review top 20 before any outreach?
2. **Buyer personas** — Nathan confirmed 3 (compliance, HR/L&D, operations). Are these still right? Any adjustments?
3. **Which rep sends?** — ATLAS outreach goes from Luke's mailbox? A shared mailbox? Does Luke know what's happening?
4. **Pilot scope** — 50 accounts for first batch? 25? What feels right for a test that's big enough to learn from but small enough to control?
5. **API access path** — Salesforce (Angel), Outreach (Amy), 6sense (marketing). Can we get read-only access this week to start pulling data?
6. **Outreach renewal (May 5)** — Is API access on the current tier? If not, renewal negotiation is the moment to add it.
7. **Success criteria** — What does "working" look like after the pilot? Reply rate above X%? Y meetings booked? What makes the team say "scale this"?

### The Ask Stays Simple

Same three things from the executive summary:

| # | Ask | Who |
|---|-----|-----|
| **1** | Salesforce API access (read-only to start) | Angel / SF Admin |
| **2** | Outreach API access confirmed | Amy Ketts |
| **3** | Greenlight to pilot 50 net new accounts | Molly / Scott |

**No closed-lost. No sensitive data. No political risk. Just: let the agent find accounts nobody has ever contacted, research them, write personalized outreach, and let Nader review everything before a single email goes out.**

If the pilot works, the data makes the case for everything else.

---

*ATLAS — Autonomous Territory & Lead Acceleration System*
*Sam Chaudhary | samcolibri*

# ATLAS — Build Status

**Last updated:** 2026-04-29  
**Repo:** https://github.com/samcolibri/atlas-pipeline-agent  
**Local:** `~/projects/q2-ai-sprint-fs/`  
**Airtable (Agent Molly):** https://airtable.com/appwlGCHBaRef70gO  
**Deploy:** Railway (Dockerfile ready, pending API creds)

---

## Stack

```
FDIC/NCUA → Supabase/Postgres → Salesforce suppression
→ Waterfall.io enrichment → ZeroBounce validation
→ Instantly V2 sending → Pipedream workflows
→ Claude (LLM classifier + email writer)
→ Salesforce logging → Calendly → Teams alerts
```

## Agent Build Status

| Agent | File | Status | Notes |
|-------|------|--------|-------|
| SCOUT | `atlas/agents/scout.py` | ✅ BUILT | FDIC/NCUA pull, ICP filter, SF suppression, Supabase write |
| RECON | `atlas/agents/recon.py` | ✅ BUILT | 6sense firmographics, pitch angle classification |
| FORGE | `atlas/agents/forge.py` | ✅ BUILT | POV email generation, OCL case studies |
| CORTEX | `atlas/agents/cortex.py` | 🔲 NOT BUILT | Orchestration brain, reply classification, A/B tracker |
| SENTINEL | `atlas/agents/sentinel.py` | 🔲 NOT BUILT | Dedup + exclusion filters |
| VITALS | `atlas/agents/vitals.py` | 🔲 NOT BUILT | Stale lead detection (8-day trigger) |
| COMMAND | `atlas/agents/command.py` | 🔲 NOT BUILT | Teams digest, KPI dashboard |
| PHOENIX | `atlas/agents/phoenix.py` | ⏸ DEFERRED | Closed-lost recovery (Phase 3) |
| COACH | `atlas/agents/coach.py` | ⏸ DEFERRED | Rep performance scoring (Phase 4) |

## Integration Status

| Integration | File | Status | Notes |
|------------|------|--------|-------|
| FDIC/NCUA | `atlas/integrations/fdic.py` | ✅ LIVE | 3,544 banks pulled, no API key needed |
| Airtable | `atlas/integrations/airtable_client.py` | ✅ LIVE | Agent memory layer, 11 tables |
| ZeroBounce | `atlas/integrations/zerobounce.py` | ✅ BUILT | Awaiting API key |
| Instantly V2 | `atlas/integrations/instantly.py` | ✅ BUILT | Webhook handler, event routing |
| 6sense | `atlas/integrations/sixsense.py` | ✅ LIVE | Firmographics working, intent API not on plan |
| Supabase | `atlas/db/client.py` | ✅ BUILT | Awaiting SUPABASE_URL + SERVICE_KEY |
| Salesforce | `atlas/integrations/salesforce.py` | ⏳ PENDING | Need Connected App creds from Angel/James |
| Outreach | `atlas/integrations/outreach.py` | ⏳ PENDING | Need OAuth Client ID/Secret from Amy Ketts |
| Waterfall.io | — | ⏳ PENDING | API key needed |
| Teams | `atlas/integrations/teams.py` | ⏳ PENDING | Webhook URL from Nathan |
| Perplexity Sonar | — | 🔲 NOT BUILT | For RECON bank research (key available) |
| SerpApi | — | 🔲 NOT BUILT | Job posting trigger signals |

## Airtable Brain — Agent Molly

Base ID: `appwlGCHBaRef70gO` · 11 tables · Paid plan

| Table | Records | Purpose |
|-------|---------|---------|
| Accounts | **3,544** | Full FDIC ICP universe, 42 fields, renewal intel |
| Contacts | 0 | Ready, 27 fields with ICP lane scoring |
| ICP_Personas | 3 | CCO (P1), CHRO (P2), L&D Director (P3) |
| Email_Templates | 6 | 5P + KCPOV tagged, CTA variants A/B |
| Case_Studies | 3 | Citadel CU, Security First Bank, Martha's Vineyard |
| **Knowledge_Base** | **20** | OCL docs indexed (text extracted, summaries pending API key) |
| **AB_Results** | **24** | 2 frameworks × 2 CTAs × 3 lanes × 2 inst types seeded |
| **Learned_Signals** | 0 | CORTEX writes here after reply classification |
| **Enrichment_Queue** | 0 | Waterfall → ZeroBounce pipeline queue |
| Triggers | 0 | Job postings, mergers, asset growth |
| Outreach_Log | 0 | Every email sent, CTA variant + framework tracked |

## ICP Priority Lanes

```
compliance (P1) → hr (P2) → l_and_d (P3)
```

Defined in `atlas/icp.py` — 60+ titles, `classify_title()`, 8 sendability gates.

**CTA Variants:**
- A: "Are you reviewing your compliance training vendor for 2026 or 2027 renewal..."  
- B: "If you and the team are thinking about other compliance training vendors this year..."

## 8 Sendability Gates

A lead is sendable only when ALL pass:
1. Account exists in FDIC/NCUA/FFIEC data
2. Not in Salesforce (customer, active opp, suppressed, partner, competitor, DNC)
3. Has a real trigger (hiring, merger, asset growth, regulatory, intent, engagement)
4. Contact has right persona (compliance, HR, L&D, BSA/AML, fair lending, risk)
5. Email passes ZeroBounce validation
6. Domain has clean SPF/DKIM/DMARC + reputation health
7. Message has specific reason tied to that bank
8. Agent has recovery path (reply → objection → bounce → unsubscribe → human handoff)

## Key Files

```bash
atlas/icp.py                          # Title priority, CTA variants, sendability gates
atlas/memory.py                       # AgentMemory — agents call this BEFORE any LLM
atlas/integrations/airtable_client.py # Airtable REST client, filterByFormula
atlas/integrations/fdic.py            # FDICClient, NCUAClient, InstitutionUniverse
atlas/db/client.py                    # Supabase state store
atlas/db/schema.sql                   # 8-table Postgres schema
atlas/agents/scout.py                 # SCOUT agent
atlas/agents/recon.py                 # RECON — 6sense firmographics
atlas/agents/forge.py                 # FORGE — POV email generation

scripts/load_fdic_to_airtable.py      # Load FDIC banks → Airtable (idempotent)
scripts/setup_airtable_fields.py      # Add fields to existing tables
scripts/setup_airtable_brain.py       # Create brain tables (one-shot)
scripts/index_knowledge_base.py       # Index PDFs/docs → Knowledge_Base
```

## Test Commands

```bash
cd ~/projects/q2-ai-sprint-fs

# FDIC pull sanity check
python3 test_scout.py --fdic-only
python3 test_scout.py --fdic-only --states IL WI MN

# Memory interface smoke test
python3 scripts/test_memory.py

# Re-index OCL docs (with Claude summaries after API key added)
python3 scripts/index_knowledge_base.py --dry-run
python3 scripts/index_knowledge_base.py --reindex

# Load more banks
python3 scripts/load_fdic_to_airtable.py --write --ncua  # add credit unions
```

## Environment Variables Needed

```bash
# Priority — needed to unlock next build steps
ANTHROPIC_API_KEY=          # → re-run indexer for Claude summaries, enables FORGE
SUPABASE_URL=               # → from Nader / Supabase dashboard
SUPABASE_SERVICE_KEY=       # → from Nader / Supabase dashboard
OUTREACH_ACCESS_TOKEN=      # → Amy Ketts (S2S OAuth from Outreach admin)
WATERFALL_API_KEY=          # → sign up at waterfall.io
ZEROBOUNCE_API_KEY=         # → sign up at zerobounce.net
INSTANTLY_API_KEY=          # → sign up at instantly.ai
INSTANTLY_CAMPAIGN_ID=      # → create campaign in Instantly dashboard

# Secondary
SF_CLIENT_ID=               # → Angel Clichy / James (SF Connected App)
SF_CLIENT_SECRET=
SF_USERNAME=
SF_PASSWORD=
TEAMS_WEBHOOK_URL=          # → Nathan Paldrmann
SERPAPI_KEY=                # → serpapi.com (job posting triggers)
```

## What Perplexity Sonar Is For

**NOT** for document analysis — it searches the live web.  
Use it in **RECON** to research a specific bank before writing the email:
- Recent news, leadership changes, regulatory filings
- Merger activity, branch expansions
- Live intel to make the email specific to that bank right now

Wire it as: `Sonar(query="First Midwest Bank compliance recent news 2026")` → feed results into FORGE prompt.

## Next Steps (Priority Order)

1. **Add `ANTHROPIC_API_KEY`** → re-run `scripts/index_knowledge_base.py --reindex` → Knowledge_Base gets Claude summaries
2. **Wire Perplexity Sonar into RECON** → live bank research before email write
3. **Get Supabase URL + key** → activate state store for pipeline tracking
4. **Get Outreach creds from Amy Ketts** → FORGE can send via sequences
5. **Build CORTEX** → reply classification, A/B tracking, human handoff
6. **Add credit unions** → `python3 scripts/load_fdic_to_airtable.py --write --ncua`
7. **Get Waterfall + ZeroBounce keys** → contact enrichment pipeline live

## Stakeholders

| Person | Role | Owns |
|--------|------|------|
| Nader Rustom | AI Consultant | Quality gate every send, executor |
| Molly Swagler | Chief of Staff | Approver, expansion to all 6 ecosystems |
| Scott Roberts | Approver | Sign-off |
| Nathan Paldrmann | Business Sponsor | 6sense key, Teams webhook |
| Amy Ketts | Outreach Admin | S2S OAuth Client ID + Secret |
| Angel Clichy / James | SF Admin | Connected App credentials |

## Financial Model

- 160 net new accounts/month → 3% reply → 5 replies → $1.35M annual incremental
- Break-even: 2 deals at $75K avg
- Monthly cost: ~$50–158
- ROI: 570x–2375x

---
markmap:
  colorFreezeLevel: 3
  maxWidth: 300
---

# ATLAS — Autonomous Territory & Lead Acceleration System
## Colibri FS Pipeline | $8.4M at-risk | 93% market untouched

### 🧠 CORTEX — Central Orchestration Brain
#### Decision Engine
- Priority queue (which account, which action, when)
- Cross-agent coordination (no duplicate touches)
- Confidence thresholds (auto-send vs human-review)
- Learning loop (every outcome feeds back into scoring)
#### State Machine
- Tracks every lead/opp across all 5 pipeline stages
- Knows what happened, what's next, what's overdue
- Single source of truth (replaces manual Salesforce checking)
#### Integration Bus
- Salesforce (CRM, leads, opps, accounts)
- Outreach (sequences, tasks, sends, replies)
- 6sense (intent signals, account scores, segments)
- Gong (call transcripts, coaching signals) — when deployed
- Ironclad (contract status, approval tracking)
- HubSpot (inbound form submissions)
- SFMC (marketing campaign data, post May 13)
- LinkedIn Sales Navigator (enrichment, social signals)

### 🔍 SCOUT — Signal Intelligence Agent
#### Intent Monitoring (6sense)
- Polls 6sense daily for "In-Market" FS accounts
- Surfaces top 10% intent-ranked from ~7,000 untouched banks
- Tracks intent score changes (rising = trigger outreach)
- Segments by buying stage (Awareness → Decision)
#### Inbound Capture
- Monitors "Contact Sales" form submissions (real-time)
- Conference/trade show lead ingestion (auto, not 24-48hr delay)
- Webinar attendee auto-capture
- Content download intent signals
#### Account Scoring
- Composite score: intent signal + firmographic fit + engagement history
- Replaces intuition-based prospecting with data-driven ranking
- 350 fresh, prioritized accounts per SDR per month
- Eliminates recycled-Salesforce-contact dependency
#### Pain Point Solved
- "Reps can only research 10-15 accounts/day" → Agent surfaces 350/month pre-scored
- "No lead routing system" → Agent routes by score + territory + capacity
- "93% of GRC market untouched" → Agent systematically works through TAM

### 🧹 SENTINEL — Data Quality Agent
#### Lead Deduplication
- Real-time matching on email + company + phone
- Merges 4-5 duplicate records into single enriched profile
- Surfaces prior history to reps (not blind to past interactions)
- Reduces 20-30% noise in lead queue → clean pipeline
#### Lead Notification Fix
- Replaces broken Process Builder (2+ year bug)
- Real-time alert when new lead assigned
- Time-to-first-touch target: under 4 hours (from days)
- Escalation if rep doesn't act within SLA
#### Account Association
- Every inbound lead auto-associated to existing account
- Reps see full company history, not orphaned records
- Buying committee view: all contacts at an account, their roles, their engagement
#### Data Enrichment
- Auto-fill missing fields from 6sense + LinkedIn
- Company size, industry, tech stack, fiscal year
- Decision maker identification across buying committee (6-10 stakeholders)
#### Pain Point Solved
- "Broken lead notification — 2+ years" → Fixed permanently by agent, not Process Builder
- "Duplicate leads create 4-5 separate records" → Real-time dedup
- "300-368 leads/qtr at risk from delayed response" → Sub-4-hour first touch

### ✉️ FORGE — Outreach Orchestration Agent
#### Persona-Based Sequence Engine
- 3 buyer personas (Nathan confirmed): Compliance Owners, HR/L&D Decision Makers, Operations Leads
- Each variant uses trigger points: regulatory change, product gap, competitive signal
- AI generates copy per account context (not generic templates)
- Zero 100%-in-sequence sends — every email has personalization
#### Multi-Channel Cadence
- Email (personalized, trigger-based)
- Phone (prioritized by intent score + best time to call)
- LinkedIn (connection requests, InMail for high-intent)
- 3-5 step cadence over 10 days per prospect
#### Inbound Response Automation
- "Contact Sales" form → personalized acknowledgment email in <5 minutes
- Auto-sequence based on product interest + company profile
- CRM activity logging for full visibility
- 15-25% conversion lift target (from current baseline)
#### Self-Optimization
- A/B tests subject lines, send times, cadence structure
- Tracks reply rates per persona, per industry segment, per message variant
- Auto-pauses underperforming sequences
- Auto-promotes winning variants
- Target: 3% reply rate on net new (from 0%)
#### Pain Point Solved
- "0 replies on 1,600+ sequence emails" → Personalized, intent-triggered outreach
- "100% in-sequence rate, zero one-off emails" → Every touch is contextual
- "Generic mass outreach to recycled contacts" → Net new accounts, persona-matched messaging
- "Email program operating as bulk broadcast" → Precision outbound motion

### 🔬 RECON — Research & Enrichment Agent
#### Instant Account Briefs
- Generates structured 1-page brief per account in <60 seconds
- Company overview, recent news, strategic priorities
- Competitive landscape, current vendor stack
- Personalized outreach angle based on trigger events
#### Buying Committee Mapping
- Identifies 6-10 stakeholders per account (not single-contact by title)
- Maps roles: champion, economic buyer, technical evaluator, blocker
- Suggests multi-threading approach per account
#### Discovery Prep Packages
- Pre-meeting brief: company context + pain hypothesis + discovery questions
- Competitive intel: what they're using, where it falls short
- Business case framework: estimated ROI for their specific profile
#### Integration Points
- Feeds into FORGE for personalized copy
- Feeds into CORTEX for account prioritization
- Replaces Outreach Research Agent ($0 if native tier available)
- Falls back to Claude/GPT brief generation if Research Agent unavailable
#### Pain Point Solved
- "15-30 min manual research per account" → <60 seconds
- "10-15 accounts researched per day" → 160+ per month with full context
- "Gap between 6sense flagging and rep having context" → Eliminated

### 🏥 VITALS — Pipeline Health Agent
#### Stale Lead Detection
- 8-day inactivity trigger → rep + manager alert
- Surfaces "Top 10 Stale Leads" view per rep
- Auto-routes post-sequence "No Reply" to nurture drip or SDR queue
- 169 currently dormant leads → $760K reactivated
#### Stale Opportunity Alerts
- 14-day inactivity trigger → auto-creates follow-up task
- Populates management dashboard with at-risk deals
- 380 of 460 opps currently 90+ day inactive → $1.8M addressable
- Target: <100 stale opps within 90 days
#### Pipeline Forecasting
- Auto-generates weekly pipeline report (replaces 2-3 hrs/wk manual)
- Win probability scoring per opp based on activity, engagement, deal size
- Revenue forecast by stage, by rep, by product line
- Flags unforecastable pipeline for manager intervention
#### Deal Progression Monitoring
- Tracks stage velocity (days in stage vs benchmark)
- Alerts on deals stuck longer than 2x average
- Suggests next-best-action per deal stage
#### Pain Point Solved
- "$2.9M pipeline with no activity alerts" → Automated monitoring + escalation
- "$1.8M effectively unforecastable" → AI-scored pipeline with confidence levels
- "Managers can't coach what they can't see" → Real-time dashboard
- "2-3 hrs/wk manual forecast updating" → Zero manual reporting

### 🔄 PHOENIX — Closed-Lost Recovery Agent
#### Loss Reason Segmentation
- Standardizes close-lost reason to structured picklist (replacing free text)
- Segments $5.5M closed-lost (GRC, 2 yrs) by recovery strategy
#### 3 Recovery Sequences
- **Contract Timing**: Auto-task 6 months before competitor contract expiry
- **Budget Deferred**: Trigger at fiscal year start for "budget not this year" losses
- **Platform Re-engagement**: Activate when credible product update available
#### Automated Re-engagement
- 80% of eligible enrolled in sequence within 30 days of launch
- Reply rate target: 15-20% (B2B warm re-engagement benchmark)
- Re-close rate target: 10-15% within 6 months
- 12-month potential: $1.0-$1.4M recovered revenue
#### Risk Controls
- Never launch Platform sequence without real product update (burns goodwill)
- Respect existing customer / known duplicate flags
- Human approval gate on first batch, then auto after validation
#### Pain Point Solved
- "$5.5M closed-lost with zero automation" → Systematic recovery engine
- "Only 1 rep does re-engagement manually today" → Fully automated
- "25% re-close rate = ~$1.4M recoverable" → Agent captures it

### 🎯 COACH — Rep Performance Agent
#### Call Intelligence (Gong integration — future)
- Analyze call transcripts for objection patterns
- Score rep performance on discovery quality, talk-to-listen ratio
- Surface competitive mentions across all calls
- "Coach in a box" for every SDR interaction
#### Activity Quality Scoring
- Track verified vs unverified call connects (Griffin issue)
- Flag calls with no duration (logged but not placed)
- Distinguish activity volume from activity quality
- Connect rate benchmarking: Luke (47.5%) vs team target
#### Workflow Compliance
- Ensure Outreach dialer is being used (not manual logging)
- Verify sequences are running (not paused or skipped)
- Track task completion rates per rep
- SDR-to-opportunity conversion rate monitoring
#### Rep Enablement
- Auto-surface best practices from top performer (Luke's workflow)
- Document and replicate winning cadences
- Onboarding playbook: "Here's what works, here's the data"
#### Pain Point Solved
- "One SDR carrying the pipeline — organizational risk" → Replicate Luke's approach
- "Griffin: 573 calls with no duration" → Activity verification layer
- "No sales coaching insights" → AI-driven coaching from data
- "47x gap in connect rate between reps" → Systematic quality improvement

### 📊 COMMAND — Reporting & Intelligence Layer
#### Automated Dashboards
- Lead-to-opp conversion rate (real-time, target 18-20%)
- Pipeline by stage, by rep, by product line
- Stale opp count and dollar value
- Win rate trending (track recovery from 24% back toward 48%)
#### Weekly Digest
- Auto-generated for Molly, Scott, Nathan
- What moved, what stalled, what needs attention
- No manual spreadsheet updating
#### KPI Tracking (90-day sprint targets)
- Email reply rate: 2-3% (from 0-1%)
- Net new accounts touched: 160+/month (from ~55)
- Discovery calls booked: 5+/month (from ~3-4)
- Pipeline from net new: 4-5 opps/month
- Research time per account: -50 to -70%
- Lead notification delivery: 0% → 100%
- Duplicate lead rate: ~25% → <5%
- Stale opps (90+ day): 380 → <100
#### Attribution
- Which agent action led to which outcome
- ROI per intervention type
- Cost per meeting booked via AI vs manual

### ⚡ IMPLEMENTATION PHASES

#### Phase 1: Foundation (Weeks 1-4) — Quick Wins
- SENTINEL: Fix lead notification + dedup (2-year bug)
- SCOUT: Configure 6sense net new account export
- VITALS: Deploy stale lead (8-day) + opp (14-day) alerts
- ROI: ~$150K/qtr pipeline + 40 hrs/mo reclaimed
- **Maps to:** Doc 3 Priority 1, Doc 1 Sprint 2 setup

#### Phase 2: Outreach Engine (Weeks 3-6) — Core Value
- RECON: Deploy account research automation
- FORGE: Build 3 persona-based sequences + inbound automation
- SCOUT: 6sense → Outreach pipeline live (350 accounts/SDR/mo)
- ROI: $1.35M annual incremental revenue potential
- **Maps to:** Doc 1 Sprint 1+2+3, Doc 2 all 3 interventions

#### Phase 3: Recovery & Intelligence (Weeks 5-8) — Compound
- PHOENIX: Launch closed-lost re-engagement (3 segments)
- VITALS: Pipeline forecasting + deal progression monitoring
- COMMAND: Automated reporting live
- ROI: $500K-$900K pipeline movement + $1.0-$1.4M 12-mo recovery
- **Maps to:** Doc 3 Priority 2+3

#### Phase 4: Coaching & Optimization (Weeks 8-12) — Multiply
- COACH: Rep performance scoring + activity verification
- FORGE: Self-optimization loop (A/B testing, auto-promote winners)
- CORTEX: Full cross-agent orchestration + learning loop
- ROI: Replicate Luke's performance across team, close win rate gap

### 💰 TOTAL ADDRESSABLE IMPACT
#### Conservative (90-day)
- Pipeline movement: $500K-$900K
- New pipeline created: $337K/qtr (from $1.35M annual)
- Recovered pipeline: $75K-$150K (first closed-won from re-engagement)
- Efficiency: 40+ hrs/mo reclaimed per rep, 2-3 hrs/wk reporting eliminated
#### Annual Run Rate
- Incremental revenue: $1.35M-$2.2M (from net new outbound)
- Recovered revenue: $1.0-$1.4M (from closed-lost)
- Pipeline under management: shift from $2.9M stale to active
- Win rate trajectory: 24% → 30%+ within 6 months
#### Break-Even
- 2 closed deals at $75K avg = investment recovered
- Every deal after that is pure upside

### 🏗️ TECH STACK (All Existing)
#### Already Licensed
- Salesforce (CRM)
- Outreach ($42,270.72/yr — renewal May 5)
- 6sense (intent data)
- HubSpot (inbound)
#### Coming Soon
- SFMC (May 13 go-live, replaces Eloqua)
- Gong (HC first, FS when proof points established)
- Ironclad (CLM, Q3-Q4 2026)
#### New Spend
- Relay.app: $0-38/month (6sense→Outreach orchestration)
- AI tools: Claude/ChatGPT (existing subscriptions)
- Total new: $0-174/quarter
#### Constraint: No Overlap With
- Farside project (Salesforce workflows, CRM routing, Agentforce)
- SFMC migration (Farside owns)
- Gong FS deployment (pending HC proof points)

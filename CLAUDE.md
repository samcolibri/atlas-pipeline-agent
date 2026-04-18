# ATLAS Pipeline Agent — Agent Instructions

## What This Is
ATLAS is an autonomous Tier 3 sales pipeline agent for Colibri Group's Financial Services ecosystem. It finds net new accounts that reps would never touch (93% of the GRC market), researches them, writes personalized outreach, and hands off warm replies to humans.

**Repo:** https://github.com/samcolibri/atlas-pipeline-agent
**Deploy:** Railway (Dockerfile + railway.toml)
**Runtime:** Python 3.11 + Flask health server + scheduled agent loop

## The 9 Agents
| Agent | File | Purpose | Status |
|-------|------|---------|--------|
| CORTEX | `atlas/agents/cortex.py` | Orchestration brain, priority queue, confidence gates | Build next |
| SCOUT | `atlas/agents/scout.py` | 6sense intent monitoring, account scoring | Build next |
| SENTINEL | `atlas/agents/sentinel.py` | Data quality, dedup, exclusion filters | Build next |
| RECON | `atlas/agents/recon.py` | AI account research via Claude (<60s briefs) | Build next |
| FORGE | `atlas/agents/forge.py` | Personalized outreach generation + Outreach enrollment | Build next |
| VITALS | `atlas/agents/vitals.py` | Stale LEAD detection (8-day trigger). NOT stale opps. | Build next |
| PHOENIX | `atlas/agents/phoenix.py` | Closed-lost recovery | DEFERRED to Phase 3 |
| COACH | `atlas/agents/coach.py` | Rep performance scoring | DEFERRED to Phase 4 |
| COMMAND | `atlas/agents/command.py` | Reporting, KPI dashboards, Teams weekly digest | Build next |

## Integration Layer
| Integration | File | API |
|------------|------|-----|
| Salesforce | `atlas/integrations/salesforce.py` | REST API (OAuth 2.0 Connected App) |
| Outreach | `atlas/integrations/outreach.py` | REST API (OAuth 2.0) |
| 6sense | `atlas/integrations/sixsense.py` | REST API (API Key) or CSV fallback |
| Claude | `atlas/integrations/claude.py` | Anthropic API (claude-sonnet-4-6) |
| Microsoft Teams | `atlas/integrations/teams.py` | Incoming Webhook (MessageCard format) |

## Critical Rules — DO NOT VIOLATE

### The Trust Line
- ATLAS ONLY operates on accounts where NO human relationship exists
- If any rep has had ANY meaningful contact with an account → ATLAS does not touch it
- Tier 1 (5-25 accounts, rep's best) → NEVER touch, offer research agent only
- Tier 2 (~50 accounts, hybrid) → NEVER touch autonomously
- Tier 3 (100+ accounts, nobody works) → THIS IS ATLAS TERRITORY

### Scope Boundaries
- ATLAS handles: prospect → opportunity (pre-trust only)
- ATLAS does NOT handle: active opps, stale opps, closed-lost (Phase 3), post-meeting anything
- Stale LEADS (pre-opportunity, no human relationship) → YES, ATLAS handles
- Stale OPPS (post-qualification, human has context) → NO, human handles

### Human Review Gate
- ATLAS_MODE=review (default): every outreach batch goes to human (Nader) before sending
- ATLAS_MODE=shadow: generate everything but send nothing (for testing/proving value)
- ATLAS_MODE=auto: only after confidence gates have graduated (Month 3+)
- ATLAS_MODE=paused: full stop, no actions

### Exclusion Filters (Hard — never enter pipeline)
- Current customers
- Accounts with active opportunities (any stage)
- Contacts who have unsubscribed
- Bounced email addresses
- Contacts already in an active Outreach sequence
- Accounts in Farside/Agentforce pipeline
- Any account a rep has engaged with (even one touchpoint)

### Platform
- Alerts go to Microsoft Teams (NOT Slack)
- 3 buyer personas: Compliance Officers, HR/L&D Decision Makers, Operations Leads
- GRC market: ~7,000 US banks, 93% never contacted
- Avg deal size: $75K. Break-even: 2 deals.

## Environment Variables (Railway)
```
# Salesforce
SF_CLIENT_ID=
SF_CLIENT_SECRET=
SF_USERNAME=
SF_PASSWORD=
SF_SECURITY_TOKEN=
SF_DOMAIN=login

# Outreach
OUTREACH_CLIENT_ID=
OUTREACH_CLIENT_SECRET=
OUTREACH_ACCESS_TOKEN=
OUTREACH_REFRESH_TOKEN=

# 6sense
SIXSENSE_API_KEY=

# Claude
ANTHROPIC_API_KEY=

# Microsoft Teams
TEAMS_WEBHOOK_URL=

# Agent Config
ATLAS_MODE=shadow
ATLAS_DAILY_LIMIT=25
ATLAS_CONFIDENCE_THRESHOLD=0.85
ATLAS_RUN_ON_START=false
```

## The Agent Loop (main.py)
```
6:00 AM ET  → SCOUT pulls 6sense intent signals
            → SENTINEL runs dedup + exclusion filters
            → RECON generates research briefs via Claude
            → FORGE generates personalized outreach
            → VITALS scans for stale leads (8-day trigger)
            → CORTEX packages batch for human review
9:00 AM     → Human reviews + approves (Teams notification)
9:15 AM     → FORGE executes approved sends via Outreach API
Every 30m   → CORTEX checks for replies, classifies, alerts rep
6:00 PM     → COMMAND sends daily summary
```

## Key Documents (Read Before Building)
1. `MEETING-OUTCOMES-041626.md` — Tier 3 positioning, two-product architecture
2. `RESPONSE-NET-NEW-FIRST.md` — Why net new first, what's excluded, bright line diagram
3. `PLAYBOOK.md` — Every API call, every payload, every step explained
4. `BLIND-SPOTS.md` — 14 gaps to address before go-live
5. `VISION.md` — Product thesis, event-driven architecture, learning engine
6. `EXECUTIVE-SUMMARY.md` — C-suite pitch (read for tone/framing)

## Building an Agent
When building any agent module, follow this pattern:
```python
# atlas/agents/<agent_name>.py

import logging
from atlas.config import Config

log = logging.getLogger(f"atlas.{__name__}")

class <AgentName>Agent:
    def __init__(self):
        # Initialize integrations this agent needs
        pass
    
    def run(self, context: dict) -> dict:
        """Main agent execution. Returns results dict."""
        log.info(f"[{self.name}] Starting...")
        # Agent logic here
        return {"status": "complete", "results": [...]}
```

## Financial Model
- 160 net new accounts/month → 3% reply → 5 replies → 4.5 opps → 25% close → $75K avg
- **$1.35M annual incremental** (conservative). Scales to $2.2M.
- Cost: ~$50-158/month. ROI: 570x-2375x.

## Stakeholders
- **Molly Swagler** — Chief of Staff, approver, champions expansion to all 6 ecosystems
- **Scott Roberts** — approver
- **Nathan Paldrmann** — business sponsor, confirmed buyer personas
- **Amy Ketts** — Dir Sales Ops, Outreach admin
- **Nader Rustom** — AI Consultant, quality gate on every send batch

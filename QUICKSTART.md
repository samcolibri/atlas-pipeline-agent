# ATLAS — Quickstart

## Run Locally (5 minutes)

```bash
# 1. Clone
git clone https://github.com/samcolibri/atlas-pipeline-agent.git
cd atlas-pipeline-agent

# 2. Setup
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 3. Configure (copy and fill in your credentials)
cp .env.example .env
# Edit .env with your API keys

# 4. Test connections
python atlas/test_connections.py

# 5. Run (shadow mode — generates everything, sends nothing)
ATLAS_MODE=shadow ATLAS_RUN_ON_START=true python main.py
```

## Deploy to Railway (3 minutes)

1. Go to [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub**
2. Select `samcolibri/atlas-pipeline-agent`
3. Add environment variables (Settings → Variables):

```
ANTHROPIC_API_KEY=sk-ant-...
SF_CLIENT_ID=...
SF_CLIENT_SECRET=...
SF_USERNAME=...
SF_PASSWORD=...
SF_SECURITY_TOKEN=...
OUTREACH_ACCESS_TOKEN=...
OUTREACH_REFRESH_TOKEN=...
SIXSENSE_API_KEY=...
TEAMS_WEBHOOK_URL=https://...webhook.office.com/...
ATLAS_MODE=shadow
ATLAS_DAILY_LIMIT=25
ATLAS_RUN_ON_START=true
```

4. Deploy. Railway auto-detects the Dockerfile and builds.
5. Health check: `https://your-app.railway.app/health`
6. Status: `https://your-app.railway.app/status`

## Modes

| Mode | What Happens |
|------|-------------|
| `shadow` | Generates everything, sends nothing. Good for testing and proving value. |
| `review` | Generates everything, sends Teams notification for human approval before sending. **Default for production.** |
| `auto` | Fully autonomous. Only after confidence gates have graduated (Month 3+). |
| `paused` | Full stop. No agent actions at all. |

## Endpoints

| Endpoint | Returns |
|----------|---------|
| `GET /` | Agent name, version, status, last run |
| `GET /health` | Health check (Railway needs this) |
| `GET /status` | Full agent status: last run, accounts processed, emails generated, errors |

## What Happens on Deploy

1. Agent starts, checks which APIs are configured
2. Logs status of each integration (configured / awaiting credentials)
3. Scheduler starts: daily run at 6:00 AM ET, reply check every 30 min
4. If `ATLAS_RUN_ON_START=true`: runs first cycle immediately
5. Each integration activates independently — add env vars without redeploying

## Minimum Viable Deploy

You can deploy with JUST the Claude API key. The agent will:
- Start healthy ✅
- Health check passes ✅
- Skip all operations that need other APIs ✅
- Log what it WOULD do if configured ✅

Add other API keys one by one as you get them. No redeploy needed — Railway picks up env var changes.

# ATLAS — Live Agent Playbook

> **This document is the complete step-by-step guide to getting ATLAS running for real.**
> Every API, every credential, every connection, every agent action — explained so anyone can follow along.

---

## Table of Contents

1. [What We're Connecting](#1-what-were-connecting)
2. [Get Salesforce API Access](#2-get-salesforce-api-access)
3. [Get Outreach API Access](#3-get-outreach-api-access)
4. [Get 6sense API Access](#4-get-6sense-api-access)
5. [Get Claude API Access](#5-get-claude-api-access)
6. [Get Microsoft Teams Webhook](#6-get-microsoft-teams-webhook)
7. [Set Up the Agent Environment](#7-set-up-the-agent-environment)
8. [Wire It All Together](#8-wire-it-all-together)
9. [The Agent Running Live — Step by Step](#9-the-agent-running-live--step-by-step)
10. [What the Agent Does Every Day](#10-what-the-agent-does-every-day)
11. [Monitoring & Troubleshooting](#11-monitoring--troubleshooting)

---

## 1. What We're Connecting

ATLAS needs to talk to 5 systems. Here's what each one does and why we need it:

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  SALESFORCE   │     │   6SENSE     │     │   OUTREACH   │
│              │     │              │     │              │
│  Where all   │     │  Where we    │     │  Where we    │
│  leads, opps,│     │  find WHO    │     │  SEND emails │
│  accounts,   │     │  is ready    │     │  and manage  │
│  and deals   │     │  to buy      │     │  sequences   │
│  live        │     │  right now   │     │              │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │
       └────────────────────┼────────────────────┘
                            │
                     ┌──────┴───────┐
                     │    ATLAS     │
                     │   AGENT     │
                     │  (Python)   │
                     └──────┬───────┘
                            │
              ┌─────────────┼─────────────┐
              │                           │
       ┌──────┴───────┐           ┌──────┴───────┐
       │   CLAUDE AI   │           │    TEAMS     │
       │              │           │              │
       │  The brain   │           │  Where reps  │
       │  that writes │           │  get alerts  │
       │  emails and  │           │  about hot   │
       │  researches  │           │  leads       │
       │  accounts    │           │              │
       └──────────────┘           └──────────────┘
```

### What Each API Does For Us

| System | What We READ | What We WRITE | API Type |
|--------|-------------|---------------|----------|
| **Salesforce** | Leads, contacts, accounts, opportunities, closed-lost deals, activity history | Activity logs, lead status updates, task creation, notes | REST API (OAuth 2.0) |
| **Outreach** | Sequence performance, reply notifications, prospect status | Create prospects, create/update sequences, enroll in sequences, schedule sends | REST API (OAuth 2.0) |
| **6sense** | Intent scores, "In-Market" accounts, buying stage, firmographic data | Nothing (read-only) | REST API (API Key) |
| **Claude** | Nothing (we send, it responds) | Research prompts, email generation prompts, classification prompts | REST API (API Key) |
| **Microsoft Teams** | Nothing | Alert messages to reps (hot leads, stale opps, weekly digest) | Webhook (URL) |

---

## 2. Get Salesforce API Access

### Who Can Do This
**Salesforce Admin** — At Colibri, this is likely Angel Clichy or someone on the Agentforce team. Only an admin can create a Connected App.

### What We Need From Salesforce
- A **Connected App** (this is how external systems talk to Salesforce)
- An **API user** with the right permissions
- The **OAuth credentials** (Client ID + Client Secret)

### Step-by-Step Instructions

#### Step 1: Log into Salesforce as Admin
1. Go to your Colibri Salesforce org (e.g., `colibri.my.salesforce.com`)
2. Log in with an admin account

#### Step 2: Create a Connected App
1. Click the **gear icon** (top right) → **Setup**
2. In the left sidebar search box, type **"App Manager"**
3. Click **App Manager**
4. Click **New Connected App** (top right)
5. Fill in:
   - **Connected App Name:** `ATLAS Pipeline Agent`
   - **API Name:** `ATLAS_Pipeline_Agent` (auto-fills)
   - **Contact Email:** `origin@aonxi.com`
6. Check **Enable OAuth Settings**
7. **Callback URL:** `https://localhost/callback` (we won't use this for server-to-server, but it's required)
8. **Selected OAuth Scopes** — add these:
   - `Access and manage your data (api)`
   - `Perform requests on your behalf at any time (refresh_token, offline_access)`
   - `Access your basic information (id, profile, email, address, phone)`
9. Click **Save**
10. Click **Continue**

#### Step 3: Get Your Credentials
1. After saving, you'll see the app detail page
2. Click **Manage Consumer Details**
3. You may need to verify via email code
4. You'll see:
   - **Consumer Key** (this is the Client ID) — copy and save
   - **Consumer Secret** (this is the Client Secret) — copy and save

```
Example (not real — yours will be different):
Consumer Key:    3MVG9d8..._LONG_STRING_...Zq8
Consumer Secret: 4F6B2C...SHORT_STRING...9A1
```

#### Step 4: Create an API User (or Use an Existing One)
The agent needs a Salesforce user account to authenticate as.

**Option A: Use an existing integration user**
If Colibri already has an API/integration user, get those credentials.

**Option B: Create a new one**
1. Setup → Users → New User
2. Profile: **System Administrator** or a custom profile with API access
3. Set a password (don't require reset)
4. Note the **username** and **password**
5. Get the **security token**: Log in as that user → Settings → My Personal Information → Reset My Security Token → check email

```
Example:
Username:       your-integration-user@yourcompany.com
Password:       (your password)
Security Token: (from email after reset)
```

#### Step 5: Test the Connection
The agent will authenticate like this:

```
POST https://login.salesforce.com/services/oauth2/token

Body (form-urlencoded):
  grant_type=password
  client_id=YOUR_CONSUMER_KEY
  client_secret=YOUR_CONSUMER_SECRET
  username=YOUR_SF_USERNAME
  password=YOUR_PASSWORD_PLUS_SECURITY_TOKEN
  (password + security token concatenated, no space)

Response:
{
  "access_token": "00D5g000004x..._LONG_TOKEN_...Zq8",
  "instance_url": "https://colibri.my.salesforce.com",
  "token_type": "Bearer"
}
```

**What we get:** An `access_token` that lets us read and write Salesforce data, and an `instance_url` that tells us which Salesforce server to talk to.

#### What Permissions the Agent Needs
The API user needs access to these Salesforce objects:

| Object | Access Level | Why |
|--------|-------------|-----|
| Lead | Read + Write | Pull leads, update status, log activity |
| Contact | Read + Write | Pull contacts, enrich, update |
| Account | Read + Write | Pull accounts, associate leads, update |
| Opportunity | Read + Write | Pull opps (open + closed-lost), update stage, log activity |
| Task | Read + Write | Create follow-up tasks for reps |
| Event | Read | Check meeting history |
| User | Read | Know which rep owns which lead/account |
| CampaignMember | Read | Check marketing engagement history |

#### What We Do With the Salesforce API

Once connected, ATLAS can make calls like:

```
GET /services/data/v59.0/query?q=
  SELECT Id, Name, Company, Status, OwnerId, LastActivityDate, CreatedDate
  FROM Lead
  WHERE Status = 'Attempting Contact'
  AND LastActivityDate < LAST_N_DAYS:8

→ Returns all stale leads (no activity in 8+ days)
→ This is the VITALS agent finding leads that are dying
```

```
GET /services/data/v59.0/query?q=
  SELECT Id, Name, AccountId, Amount, StageName, CloseDate, Loss_Reason__c
  FROM Opportunity
  WHERE StageName = 'Closed Lost'
  AND CloseDate > 2024-04-16
  AND Amount > 25000

→ Returns all closed-lost opportunities in last 2 years over $25K
→ This is the PHOENIX agent finding revenue to recover
```

```
POST /services/data/v59.0/sobjects/Task
{
  "Subject": "ATLAS: Stale opportunity - 14 days no activity",
  "WhoId": "003...",
  "OwnerId": "005...",
  "Status": "Open",
  "Priority": "High",
  "Description": "This opportunity has had no activity for 14 days. ..."
}

→ Creates a task for the rep to follow up on a stale deal
→ This is the VITALS agent alerting reps
```

---

## 3. Get Outreach API Access

### Who Can Do This
**Outreach Admin** — At Colibri, this is Amy Ketts. The admin creates the API app and generates credentials.

### What We Need From Outreach
- An **OAuth App** registered in Outreach
- **Client ID + Client Secret**
- **Authorization** from a user with the right scopes

### Step-by-Step Instructions

#### Step 1: Request API Access
1. Amy logs into Outreach (`app.outreach.io`)
2. Click the **user icon** (bottom left) → **Settings**
3. Click **API Access** in the left sidebar (under "Integrations")
4. If you see "Request API Access" — click it. Outreach may need to enable this for your account tier.

> **Important:** Outreach API may not be available on all contract tiers. The current Colibri contract is 23 Engage + 4 Admin + 11 Voice licenses at $42,270.72/yr. API access is typically included on Enterprise plans. If not available, Amy should contact the Outreach account rep to request it — this is a standard request.

#### Step 2: Create an OAuth App
1. Once API access is enabled, go to **Settings → API Access → OAuth Applications**
2. Click **Create New Application**
3. Fill in:
   - **Name:** `ATLAS Pipeline Agent`
   - **Redirect URI:** `https://localhost/callback`
   - **Scopes:** Select all that apply:
     - `prospects.all` (read + write prospects)
     - `sequences.all` (read + write sequences)
     - `sequenceSteps.all` (read + write sequence steps)
     - `mailings.all` (read + write mailings)
     - `tasks.all` (read + write tasks)
     - `accounts.all` (read + write accounts)
     - `users.read` (read user info)
     - `mailboxes.read` (check mailbox health)
4. Click **Save**
5. You'll see:
   - **Client ID** (Application ID) — copy and save
   - **Client Secret** — copy and save (only shown once!)

```
Example (not real):
Client ID:     Mzk2NTQ4NzY...
Client Secret:  abc123def456...
```

#### Step 3: Authorize the App (Get an Access Token)
This is a one-time step where a real Outreach user (Amy or Nader) grants the app permission:

1. Open this URL in a browser (replace YOUR_CLIENT_ID):
```
https://api.outreach.io/oauth/authorize?
  client_id=YOUR_CLIENT_ID&
  redirect_uri=https://localhost/callback&
  response_type=code&
  scope=prospects.all sequences.all sequenceSteps.all mailings.all tasks.all accounts.all
```

2. Log into Outreach when prompted
3. Click **Authorize**
4. The browser redirects to `https://localhost/callback?code=AUTHORIZATION_CODE`
5. Copy the `code` from the URL

#### Step 4: Exchange Code for Access Token
```
POST https://api.outreach.io/oauth/token

Body (JSON):
{
  "client_id": "YOUR_CLIENT_ID",
  "client_secret": "YOUR_CLIENT_SECRET",
  "redirect_uri": "https://localhost/callback",
  "grant_type": "authorization_code",
  "code": "THE_CODE_FROM_STEP_3"
}

Response:
{
  "access_token": "eyJ0eXAi..._LONG_TOKEN_...",
  "refresh_token": "eyJ0eXAi..._ANOTHER_TOKEN_...",
  "token_type": "bearer",
  "expires_in": 7200
}
```

**Save both tokens.** The `access_token` expires in 2 hours. The `refresh_token` is used to get new access tokens without re-authorizing. ATLAS handles this automatically.

#### What We Do With the Outreach API

```
POST https://api.outreach.io/api/v2/prospects

{
  "data": {
    "type": "prospect",
    "attributes": {
      "firstName": "Sarah",
      "lastName": "Johnson",
      "emails": ["sarah.johnson@firstnationalbank.com"],
      "title": "Chief Compliance Officer",
      "company": "First National Bank",
      "tags": ["atlas-phoenix", "contract-timing", "grc"]
    }
  }
}

→ Creates a prospect in Outreach
→ This is FORGE preparing someone for a sequence
```

```
POST https://api.outreach.io/api/v2/sequenceStates

{
  "data": {
    "type": "sequenceState",
    "relationships": {
      "prospect": { "data": { "type": "prospect", "id": 12345 } },
      "sequence": { "data": { "type": "sequence", "id": 678 } },
      "mailbox":  { "data": { "type": "mailbox", "id": 1 } }
    }
  }
}

→ Enrolls the prospect into a specific sequence
→ This is FORGE putting Sarah into the "Contract Timing Re-engagement" sequence
→ Outreach then handles the actual email sending on schedule
```

```
GET https://api.outreach.io/api/v2/mailings?
  filter[mailingType]=reply&
  filter[updatedAt]=2026-04-15..2026-04-16

→ Gets all replies from the last 24 hours
→ This is how ATLAS detects when someone responds
→ Agent classifies the reply and alerts the rep
```

---

## 4. Get 6sense API Access

### Who Can Do This
**6sense Admin** — This is likely someone on the Colibri marketing team. 6sense API access is managed through the 6sense platform settings.

### What We Need From 6sense
- **API Key** (also called API Token)
- Knowledge of which **segments** are configured for FS/GRC

### Step-by-Step Instructions

#### Step 1: Request API Access
1. Log into 6sense (`app.6sense.com`)
2. Go to **Settings** (gear icon, top right)
3. Navigate to **Integrations → API Configuration** (or similar — UI varies by version)
4. If API isn't enabled, contact your 6sense Customer Success Manager (CSM) to enable it
5. Once enabled, you'll see an option to **Generate API Key**

#### Step 2: Generate API Key
1. Click **Generate API Key** (or **Create New Token**)
2. Name it: `ATLAS Pipeline Agent`
3. Set permissions: **Read-only** (we never write to 6sense)
4. Copy the API key

```
Example (not real):
API Key: 6s_api_k3y_Abc123Def456Ghi789
```

> **Note:** Some 6sense plans may use OAuth instead of API keys. If so, the process is similar to Outreach OAuth above. Ask the CSM which method your plan supports.

#### Alternative: Manual Export (If API Is Not Available)
If 6sense API isn't on your plan, we can work with manual exports:

1. In 6sense, go to **Segments** → select the FS/GRC segment
2. Click **Export** → download as CSV
3. Save to `~/projects/q2-ai-sprint-fs/data/6sense_export.csv`
4. ATLAS reads the CSV instead of calling the API
5. Re-export weekly (or set up a scheduled export to SFTP if available)

This is less real-time but works perfectly for weekly batches.

#### What We Do With the 6sense API

```
GET https://api.6sense.com/v3/company/search

Headers:
  Authorization: Token 6s_api_k3y_Abc123Def456Ghi789

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

Response:
{
  "results": [
    {
      "company": "First National Bank",
      "domain": "firstnationalbank.com",
      "industry": "Banking",
      "employee_count": "501-1000",
      "buying_stage": "Decision",
      "intent_score": 92,
      "intent_topics": ["GRC software", "compliance automation", "regulatory reporting"],
      "location": "Chicago, IL"
    },
    ...
  ]
}

→ Returns the top 100 accounts that are actively looking to buy GRC solutions
→ This is SCOUT finding who to target this week
→ Intent score 92 means this company is deep in a buying cycle RIGHT NOW
```

```
GET https://api.6sense.com/v3/company/details?domain=firstnationalbank.com

Response:
{
  "company": "First National Bank",
  "annual_revenue": "$250M-$500M",
  "employee_count": 850,
  "technologies": ["Salesforce", "Microsoft 365", "SAP"],
  "buying_committee": [
    { "name": "Sarah Johnson", "title": "Chief Compliance Officer", "email": "sarah.johnson@..." },
    { "name": "Mike Chen", "title": "VP Operations", "email": "mike.chen@..." },
    { "name": "Lisa Park", "title": "Director of Training", "email": "lisa.park@..." }
  ],
  "intent_topics_trending": ["regulatory compliance", "employee training platform"],
  "web_visits": 14  // visited Colibri's GRC pages 14 times this month
}

→ Detailed enrichment data for a specific company
→ RECON uses this to generate the account research brief
→ FORGE uses the buying committee to identify which persona to target
→ Note: 14 web visits this month = this account is actively researching us
```

---

## 5. Get Claude API Access

### Who Can Do This
**Sam** — already has Anthropic API access.

### Step-by-Step Instructions

#### Step 1: Get Your API Key
1. Go to `console.anthropic.com`
2. Log in (or sign up)
3. Click **API Keys** in the left sidebar
4. Click **Create Key**
5. Name it: `ATLAS Pipeline Agent`
6. Copy the key

```
Example (not real):
API Key: sk-ant-api03-Abc123...XYZ
```

#### Step 2: Choose Your Models
ATLAS uses two Claude models for different tasks:

| Task | Model | Why | Cost |
|------|-------|-----|------|
| **Account research briefs** | Claude Sonnet (claude-sonnet-4-6) | Fast, good quality, high volume. We generate 160+ briefs/month. | ~$0.003 per brief |
| **Email copy generation** | Claude Sonnet (claude-sonnet-4-6) | Good at natural, personalized writing. Fast enough for batch generation. | ~$0.005 per email |
| **Loss reason classification** | Claude Haiku (claude-haiku-4-5) | Simple classification task, doesn't need heavy reasoning. Cheap. | ~$0.001 per classification |
| **Edge case decisions** | Claude Opus (claude-opus-4-6) | Complex judgment calls: should we contact this account? Is this reply positive or negative? | ~$0.02 per decision |
| **Estimated monthly cost** | | **160 accounts × ~$0.01 per account** | **~$50-100/month** |

#### What We Do With the Claude API

**Research Brief Generation (RECON Agent):**

```
POST https://api.anthropic.com/v1/messages

Headers:
  x-api-key: sk-ant-api03-...
  anthropic-version: 2023-06-01
  content-type: application/json

Body:
{
  "model": "claude-sonnet-4-6",
  "max_tokens": 1024,
  "messages": [
    {
      "role": "user",
      "content": "Generate a 1-page sales research brief for this account. Focus on: company overview, recent news, strategic priorities, competitive landscape, and a specific outreach angle tied to their GRC/compliance needs.\n\nCompany: First National Bank\nIndustry: Banking\nEmployees: 850\nRevenue: $250M-$500M\nLocation: Chicago, IL\nTechnologies: Salesforce, Microsoft 365, SAP\nIntent signals: GRC software, compliance automation, regulatory reporting\nBuying stage: Decision (intent score: 92)\nWeb visits to Colibri GRC pages: 14 this month\n\nFormat the brief as:\n1. Company Snapshot (2-3 lines)\n2. Why They're Looking Now (specific trigger)\n3. Key Decision Makers (who to target)\n4. Recommended Outreach Angle (specific hook)\n5. What NOT to Say (potential landmines)"
    }
  ]
}

Response:
{
  "content": [
    {
      "type": "text",
      "text": "## First National Bank — Account Brief\n\n### 1. Company Snapshot\nFirst National Bank is a mid-size regional bank ($250-500M revenue, 850 employees) headquartered in Chicago. They run Salesforce as their CRM and Microsoft 365 for productivity — notably, no dedicated GRC platform is visible in their tech stack, suggesting they may be managing compliance through manual processes or spreadsheets.\n\n### 2. Why They're Looking Now\nTheir 6sense intent score of 92 (Decision stage) combined with 14 visits to Colibri's GRC pages this month signals active evaluation. The trending topics — regulatory compliance and employee training — suggest they're likely responding to recent CFPB enforcement actions targeting mid-size banks with inadequate compliance training documentation. Q2 is also budget planning season for many banks with fiscal years starting July 1.\n\n### 3. Key Decision Makers\n- **Sarah Johnson, Chief Compliance Officer** — Primary buyer. Owns the compliance gap this product fills.\n- **Mike Chen, VP Operations** — Likely involved in vendor evaluation and implementation planning.\n- **Lisa Park, Director of Training** — Relevant if the conversation touches LMS/training compliance.\n\n### 4. Recommended Outreach Angle\nLead with the regulatory pressure angle: mid-size banks are under increasing scrutiny for compliance training documentation. Position Colibri's GRC solution as the system that turns audit prep from a 3-week scramble into an automated, always-ready state. Reference the CFPB's recent focus on banks in the $250M-$1B range.\n\n### 5. What NOT to Say\n- Don't lead with product features — they're past awareness, in Decision stage\n- Don't reference competitors by name (they may already be in eval with one)\n- Don't push for a demo immediately — offer a compliance readiness assessment first"
    }
  ]
}

→ In 3-5 seconds, RECON generated what would take a rep 15-30 minutes
→ This brief feeds directly into FORGE for email personalization
→ It also gets attached to the Salesforce record for the rep
```

**Personalized Email Generation (FORGE Agent):**

```
POST https://api.anthropic.com/v1/messages

Body:
{
  "model": "claude-sonnet-4-6",
  "max_tokens": 512,
  "messages": [
    {
      "role": "user",
      "content": "Write a cold outreach email for a B2B sales sequence. This is Step 1 of a 5-step sequence.\n\nContext:\n- Sender: Luke Pearson, SDR at Colibri Group\n- Recipient: Sarah Johnson, Chief Compliance Officer at First National Bank\n- Account brief: [the brief from above]\n- Persona: Compliance Officer\n- Trigger: Regulatory pressure on mid-size banks (CFPB enforcement)\n- Outreach angle: Compliance readiness assessment\n- Tone: Direct, knowledgeable, peer-level (not salesy)\n\nRules:\n- Under 120 words\n- No 'I hope this finds you well' or similar filler\n- Open with a specific, relevant observation (not 'I noticed your company...')\n- One clear call to action\n- No product feature dumps\n- Sound like a human who did real research, not an AI\n\nWrite 2 variants (A and B) for A/B testing."
    }
  ]
}

Response:
{
  "content": [
    {
      "type": "text",
      "text": "**Variant A:**\n\nSubject: Compliance documentation at mid-size banks\n\nSarah,\n\nThe CFPB's enforcement focus on compliance training documentation at banks in the $250M-$1B range is creating real urgency for compliance leaders who've been managing this through spreadsheets and manual processes.\n\nWe work with compliance teams at regional banks to turn audit prep from a quarterly scramble into something that's always ready — without adding headcount or a 6-month implementation.\n\nWould a 20-minute compliance readiness assessment be useful? We'd walk through the three areas CFPB examiners flag most often and where your current setup likely stands.\n\n— Luke\n\n---\n\n**Variant B:**\n\nSubject: Question about your compliance workflow\n\nSarah,\n\nQuick question — is your team still managing compliance training records manually, or have you moved to a dedicated system?\n\nAsking because we've seen a pattern with banks your size: the compliance team knows the gap exists, but the business case for fixing it doesn't crystallize until an audit finding forces the conversation.\n\nWe help compliance leaders at regional banks get ahead of that — usually a 20-minute assessment to identify what CFPB examiners would flag first.\n\nWorth a conversation?\n\n— Luke"
    }
  ]
}

→ Two personalized email variants generated in ~4 seconds
→ Both reference specific, real context (CFPB, bank size, compliance gap)
→ Both sound human, not robotic
→ A/B testing will show which style gets more replies
→ FORGE generates these for every account in the batch
```

**Reply Classification (CORTEX Agent):**

```
POST https://api.anthropic.com/v1/messages

Body:
{
  "model": "claude-haiku-4-5",
  "max_tokens": 256,
  "messages": [
    {
      "role": "user",
      "content": "Classify this email reply into one of these categories: POSITIVE (interested in meeting/learning more), OBJECTION (has a concern but door is open), NEUTRAL (asking a question, unclear intent), NEGATIVE (not interested), UNSUBSCRIBE (wants to be removed), OUT_OF_OFFICE (auto-reply).\n\nAlso extract: key concern (if any), suggested next action, urgency level (high/medium/low).\n\nReply:\n\"Luke, thanks for reaching out. We're actually in the middle of evaluating a couple of options right now. Can you send over a one-pager on what Colibri's solution covers? I'd want to share it with our VP of Ops before scheduling anything.\"\n\nRespond in JSON format."
    }
  ]
}

Response:
{
  "content": [
    {
      "type": "text",
      "text": "{\n  \"classification\": \"POSITIVE\",\n  \"confidence\": 0.92,\n  \"key_concern\": \"Needs to involve VP of Ops in decision\",\n  \"buying_signal\": \"Already evaluating options — active buying cycle confirmed\",\n  \"suggested_next_action\": \"Send one-pager immediately, then follow up in 2 days to schedule meeting with both Sarah and VP of Ops\",\n  \"urgency\": \"HIGH\",\n  \"reasoning\": \"Prospect is in active evaluation, requested materials, mentioned a specific next step (sharing with VP Ops). This is a warm lead in Decision stage.\"\n}"
    }
  ]
}

→ In <1 second, CORTEX classified the reply and recommended next action
→ This triggers an immediate Teams alert to Luke:
→ "🔥 HOT REPLY: Sarah Johnson @ First National Bank — POSITIVE. 
→  She's evaluating options and wants a one-pager for her VP of Ops. 
→  Send it NOW and follow up in 2 days."
```

---

## 6. Get Microsoft Teams Webhook

### Who Can Do This
Anyone who owns or manages the FS sales channel in Microsoft Teams.

### Step-by-Step Instructions

#### Step 1: Set Up an Incoming Webhook in Teams
1. Open **Microsoft Teams**
2. Go to the channel where you want alerts (e.g., "FS Sales Pipeline")
3. Click the **"..."** next to the channel name → **"Manage channel"**
4. Click **"Connectors"** (or in newer Teams: go to channel settings → **Workflows** → **Incoming Webhook**)
5. Find **"Incoming Webhook"** → click **"Configure"**
6. Name it: `ATLAS Pipeline Agent`
7. Optionally upload an icon
8. Click **"Create"**
9. Copy the **Webhook URL** (format: `https://xxxxx.webhook.office.com/webhookb2/...`)

```
Example (not real):
https://colibri.webhook.office.com/webhookb2/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx@xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/IncomingWebhook/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

#### What We Do With the Teams Webhook

```
POST https://colibri.webhook.office.com/webhookb2/.../IncomingWebhook/...

Body:
{
  "@type": "MessageCard",
  "@context": "http://schema.org/extensions",
  "themeColor": "FF0000",
  "summary": "Hot Reply — First National Bank",
  "sections": [{
    "activityTitle": "🔥 Hot Reply — First National Bank",
    "facts": [
      { "name": "From", "value": "Sarah Johnson (Chief Compliance Officer)" },
      { "name": "Classification", "value": "POSITIVE (92% confidence)" },
      { "name": "Buying Signal", "value": "Active evaluation in progress" },
      { "name": "Next Action", "value": "Send one-pager NOW, follow up in 2 days" },
      { "name": "Account Value", "value": "Est. $75K (GRC Enterprise)" }
    ],
    "text": "\"Thanks for reaching out. We're evaluating options. Can you send a one-pager?\""
  }],
  "potentialAction": [{
    "@type": "OpenUri",
    "name": "View in Salesforce",
    "targets": [{ "os": "default", "uri": "https://colibri.my.salesforce.com/001..." }]
  },
  {
    "@type": "OpenUri",
    "name": "View in Outreach",
    "targets": [{ "os": "default", "uri": "https://app.outreach.io/prospects/12345" }]
  }]
}

→ Luke gets this in Teams instantly when Sarah replies
→ He has everything he needs: what she said, what to do next, links to act
→ No manual checking of Outreach for replies
```

---

## 7. Set Up the Agent Environment

### What You Need on Your Machine
- Python 3.11 or higher
- pip (Python package manager)
- Git (already have it)
- A text editor (VS Code, etc.)

### Step-by-Step Setup

```bash
# 1. Clone the repo
cd ~/projects
git clone https://github.com/samcolibri/atlas-pipeline-agent.git
cd atlas-pipeline-agent

# 2. Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install anthropic        # Claude API
pip install simple-salesforce # Salesforce API
pip install requests         # HTTP requests (Outreach, 6sense, Teams)
pip install python-dotenv    # Environment variables
pip install schedule         # Task scheduling
pip install sqlite-utils     # Local database

# 4. Create the .env file (NEVER commit this to git)
cat > .env << 'EOF'
# Salesforce
SF_CLIENT_ID=your_consumer_key_here
SF_CLIENT_SECRET=your_consumer_secret_here
SF_USERNAME=your_sf_username_here
SF_PASSWORD=your_password_here
SF_SECURITY_TOKEN=your_security_token_here
SF_DOMAIN=login  # use 'test' for sandbox

# Outreach
OUTREACH_CLIENT_ID=your_client_id_here
OUTREACH_CLIENT_SECRET=your_client_secret_here
OUTREACH_ACCESS_TOKEN=your_access_token_here
OUTREACH_REFRESH_TOKEN=your_refresh_token_here

# 6sense
SIXSENSE_API_KEY=your_api_key_here

# Claude
ANTHROPIC_API_KEY=sk-ant-api03-your_key_here

# Microsoft Teams
TEAMS_WEBHOOK_URL=https://xxxxx.webhook.office.com/webhookb2/xxx/IncomingWebhook/xxx/xxx

# Agent Config
ATLAS_MODE=review          # 'review' = human gate, 'auto' = fully autonomous
ATLAS_DAILY_LIMIT=25       # max emails per day (ramp slowly)
ATLAS_CONFIDENCE_THRESHOLD=0.85  # below this → queue for human review
EOF
```

### Project Structure

```
atlas-pipeline-agent/
├── .env                          ← Your API keys (NEVER commit)
├── .gitignore                    ← Ensures .env stays local
├── README.md
├── PROPOSAL.md
├── VISION.md
├── RESPONSE-DATA-HYGIENE.md
├── PLAYBOOK.md                   ← This file
│
├── atlas/                        ← The agent code
│   ├── __init__.py
│   ├── main.py                   ← Entry point — runs the daily loop
│   ├── config.py                 ← Loads .env, sets thresholds
│   │
│   ├── agents/                   ← Each agent is a module
│   │   ├── cortex.py             ← Orchestration brain
│   │   ├── scout.py              ← 6sense signal monitoring
│   │   ├── sentinel.py           ← Data quality (dedup, enrichment)
│   │   ├── forge.py              ← Outreach generation + execution
│   │   ├── recon.py              ← Account research (Claude)
│   │   ├── vitals.py             ← Pipeline health monitoring
│   │   ├── phoenix.py            ← Closed-lost recovery
│   │   └── command.py            ← Reporting + dashboards
│   │
│   ├── integrations/             ← API connectors
│   │   ├── salesforce.py         ← Salesforce REST API wrapper
│   │   ├── outreach.py           ← Outreach REST API wrapper
│   │   ├── sixsense.py           ← 6sense API wrapper
│   │   ├── claude.py             ← Anthropic API wrapper
│   │   └── teams.py              ← Microsoft Teams webhook wrapper
│   │
│   ├── models/                   ← Data models
│   │   ├── account.py            ← Account object
│   │   ├── lead.py               ← Lead object
│   │   ├── opportunity.py        ← Opportunity object
│   │   └── sequence.py           ← Outreach sequence object
│   │
│   └── db/                       ← Local state
│       ├── atlas.db              ← SQLite database
│       └── migrations.py         ← Schema setup
│
├── architecture/
│   └── atlas-markmap.md
│
├── docs/                         ← Confidential PDFs (gitignored)
│
├── data/                         ← Data exports (gitignored)
│   └── 6sense_export.csv
│
├── logs/                         ← Agent logs (gitignored)
│   └── atlas_2026-04-16.log
│
└── tests/                        ← Test suite
    ├── test_salesforce.py
    ├── test_outreach.py
    └── test_agents.py
```

---

## 8. Wire It All Together

### The Connection Test Script

Before running the full agent, test each connection independently:

```python
# atlas/test_connections.py
# Run this first to verify all APIs are working

import os
from dotenv import load_dotenv
load_dotenv()

def test_salesforce():
    """Test: Can we connect to Salesforce and read data?"""
    from simple_salesforce import Salesforce
    
    sf = Salesforce(
        username=os.getenv('SF_USERNAME'),
        password=os.getenv('SF_PASSWORD'),
        security_token=os.getenv('SF_SECURITY_TOKEN'),
        client_id=os.getenv('SF_CLIENT_ID'),
        domain=os.getenv('SF_DOMAIN', 'login')
    )
    
    # Try a simple query
    result = sf.query("SELECT COUNT() FROM Lead")
    print(f"✅ Salesforce connected. Total leads: {result['totalSize']}")
    
    # Check closed-lost opps
    closed_lost = sf.query("""
        SELECT COUNT(), SUM(Amount) 
        FROM Opportunity 
        WHERE StageName = 'Closed Lost' 
        AND CloseDate > 2024-04-16
    """)
    print(f"   Closed-lost opps (2yr): {closed_lost['totalSize']}")

def test_outreach():
    """Test: Can we connect to Outreach and read sequences?"""
    import requests
    
    headers = {
        'Authorization': f"Bearer {os.getenv('OUTREACH_ACCESS_TOKEN')}",
        'Content-Type': 'application/vnd.api+json'
    }
    
    resp = requests.get(
        'https://api.outreach.io/api/v2/sequences?page[limit]=5',
        headers=headers
    )
    
    if resp.status_code == 200:
        sequences = resp.json()['data']
        print(f"✅ Outreach connected. Found {len(sequences)} sequences:")
        for seq in sequences:
            print(f"   - {seq['attributes']['name']} ({seq['attributes']['sequenceType']})")
    else:
        print(f"❌ Outreach failed: {resp.status_code} — {resp.text}")

def test_6sense():
    """Test: Can we connect to 6sense and pull intent data?"""
    import requests
    
    headers = {
        'Authorization': f"Token {os.getenv('SIXSENSE_API_KEY')}",
        'Content-Type': 'application/json'
    }
    
    resp = requests.get(
        'https://api.6sense.com/v3/company/search',
        headers=headers,
        json={
            "filter": {
                "industry": ["Financial Services"],
                "buying_stage": ["Decision", "Purchase"]
            },
            "limit": 5
        }
    )
    
    if resp.status_code == 200:
        accounts = resp.json().get('results', [])
        print(f"✅ 6sense connected. Top intent accounts:")
        for acc in accounts:
            print(f"   - {acc['company']} (intent: {acc.get('intent_score', 'N/A')})")
    else:
        print(f"❌ 6sense failed: {resp.status_code} — {resp.text}")
        print("   (This is OK if using CSV export instead)")

def test_claude():
    """Test: Can we connect to Claude and generate content?"""
    import anthropic
    
    client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=256,
        messages=[{
            "role": "user",
            "content": "Write one sentence about why compliance officers at mid-size banks need better GRC tools. Be specific and direct."
        }]
    )
    
    print(f"✅ Claude connected. Test generation:")
    print(f"   {message.content[0].text}")

def test_teams():
    """Test: Can we send a Teams alert?"""
    import requests
    
    resp = requests.post(
        os.getenv('TEAMS_WEBHOOK_URL'),
        json={
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "summary": "ATLAS Test",
            "sections": [{
                "activityTitle": "✅ ATLAS Pipeline Agent connected successfully",
                "text": "Test alert from ATLAS. If you see this, Teams integration is working."
            }]
        }
    )
    
    if resp.status_code == 200:
        print(f"✅ Teams connected. Check your channel for the test message.")
    else:
        print(f"❌ Teams failed: {resp.status_code}")

if __name__ == '__main__':
    print("=" * 60)
    print("ATLAS CONNECTION TEST")
    print("=" * 60)
    print()
    
    print("1. Testing Salesforce...")
    try: test_salesforce()
    except Exception as e: print(f"❌ Salesforce error: {e}")
    print()
    
    print("2. Testing Outreach...")
    try: test_outreach()
    except Exception as e: print(f"❌ Outreach error: {e}")
    print()
    
    print("3. Testing 6sense...")
    try: test_6sense()
    except Exception as e: print(f"❌ 6sense error: {e}")
    print()
    
    print("4. Testing Claude...")
    try: test_claude()
    except Exception as e: print(f"❌ Claude error: {e}")
    print()
    
    print("5. Testing Microsoft Teams...")
    try: test_teams()
    except Exception as e: print(f"❌ Teams error: {e}")
    print()
    
    print("=" * 60)
    print("CONNECTION TEST COMPLETE")
    print("=" * 60)
```

### Expected Output When Everything Works

```
============================================================
ATLAS CONNECTION TEST
============================================================

1. Testing Salesforce...
✅ Salesforce connected. Total leads: 2,847
   Closed-lost opps (2yr): 312

2. Testing Outreach...
✅ Outreach connected. Found 5 sequences:
   - GRC Inbound Follow-up (active)
   - FS Enterprise Outbound (paused)
   - Banking Cold Outreach (active)
   - Insurance Intro (active)
   - LMS Demo Request (paused)

3. Testing 6sense...
✅ 6sense connected. Top intent accounts:
   - First National Bank (intent: 92)
   - Midwest Credit Union (intent: 87)
   - Pacific Coast Banking (intent: 83)
   - Great Lakes Financial (intent: 79)
   - Southern Federal (intent: 76)

4. Testing Claude...
✅ Claude connected. Test generation:
   Mid-size banks face a compliance paradox: they're held to the same 
   regulatory standards as large institutions but manage audits with 
   spreadsheets and tribal knowledge that wouldn't survive a single 
   examiner's follow-up question.

5. Testing Microsoft Teams...
✅ Teams connected. Check your channel for the test message.

============================================================
CONNECTION TEST COMPLETE
============================================================
```

---

## 9. The Agent Running Live — Step by Step

Here's exactly what happens when ATLAS runs. Every step, in order, with what the agent sees and does.

### The Daily Run (Triggered at 6:00 AM ET)

```
═══════════════════════════════════════════════════════════
  ATLAS DAILY RUN — April 17, 2026, 06:00 AM ET
═══════════════════════════════════════════════════════════

STEP 1: SCOUT — Finding Who's Ready to Buy
─────────────────────────────────────────────

  [06:00:01] Connecting to 6sense...
  [06:00:03] Pulling top intent accounts for Financial Services...
  [06:00:05] Found 47 accounts with intent score > 70
  
  [06:00:06] Connecting to Salesforce...
  [06:00:08] Cross-referencing against existing accounts...
  
  [06:00:10] Results:
    ✓ 31 NET NEW accounts (never in Salesforce)
    ✓ 9 accounts with STALE leads (not contacted in 90+ days)
    ✗ 4 accounts excluded (current customers)
    ✗ 2 accounts excluded (active opportunities)
    ✗ 1 account excluded (in Farside pipeline)
    
  [06:00:11] Top 5 accounts for today:
    1. First National Bank     — Intent: 92, Decision stage
    2. Midwest Credit Union    — Intent: 87, Decision stage
    3. Pacific Coast Banking   — Intent: 83, Purchase stage
    4. Great Lakes Financial   — Intent: 79, Evaluation stage
    5. Southern Federal        — Intent: 76, Evaluation stage

═══════════════════════════════════════════════════════════

STEP 2: SENTINEL — Cleaning the Data
─────────────────────────────────────────────

  [06:00:15] Running deduplication check on 31 new accounts...
  [06:00:18] Found 3 potential duplicates:
    ⚠ "First National Bank" may match "First National Bancorp" in SF
      → Flagged for human review (different legal entity?)
    ⚠ "Sarah Johnson" exists in 2 Salesforce records
      → Auto-merged (same email, same company)
    ⚠ "Pacific Coast Banking" — contact email bounced last quarter
      → Flagged: find alternative contact
      
  [06:00:20] Running exclusion filters...
  [06:00:22] 28 accounts pass all filters → entering pipeline
  [06:00:22] 3 accounts flagged for human review → queued

═══════════════════════════════════════════════════════════

STEP 3: RECON — Researching Each Account
─────────────────────────────────────────────

  [06:00:25] Generating research briefs via Claude...
  
  [06:00:28] Brief 1/28: First National Bank
    → Company: Mid-size regional bank, Chicago, 850 employees
    → Trigger: CFPB enforcement focus on compliance documentation
    → Persona: Sarah Johnson, Chief Compliance Officer
    → Angle: Compliance readiness assessment
    → Time: 3.2 seconds
    
  [06:00:31] Brief 2/28: Midwest Credit Union
    → Company: Credit union, $180M assets, Milwaukee, 320 employees
    → Trigger: NCUA exam cycle approaching Q3
    → Persona: David Martinez, VP Risk & Compliance
    → Angle: Audit prep automation
    → Time: 2.8 seconds
    
  [06:00:34] Brief 3/28: Pacific Coast Banking
    → ⚠ Bounced email flagged — skipping until alt contact found
    
  ... (continues for all 28 accounts) ...
  
  [06:02:45] All briefs generated. Total time: 2 minutes 20 seconds.
  [06:02:45] Average: 5.0 seconds per brief
  [06:02:45] vs. manual research: 15-30 minutes per account = 7-14 HOURS saved

═══════════════════════════════════════════════════════════

STEP 4: FORGE — Writing Personalized Outreach
─────────────────────────────────────────────

  [06:02:50] Generating email sequences via Claude...
  
  [06:02:54] Account 1/27: First National Bank → Sarah Johnson
    → Persona: Compliance Officer
    → Template: regulatory-trigger
    → Generated: 2 A/B variants (direct vs. question-led)
    → Confidence: 0.91 (HIGH — auto-approve eligible)
    → Time: 4.1 seconds
    
  [06:02:58] Account 2/27: Midwest Credit Union → David Martinez
    → Persona: Compliance Officer
    → Template: audit-prep
    → Generated: 2 A/B variants
    → Confidence: 0.88 (HIGH)
    → Time: 3.7 seconds
    
  ... (continues for all 27 accounts) ...
  
  [06:05:30] All emails generated. Total time: 2 minutes 40 seconds.
  
  [06:05:31] CONFIDENCE BREAKDOWN:
    HIGH (>0.85):   22 accounts → auto-approve eligible
    MEDIUM (0.5-0.85): 4 accounts → queued for human review
    LOW (<0.5):      1 account → flagged (unusual profile)

═══════════════════════════════════════════════════════════

  ┌─────────────────────────────────────────────────────┐
  │                                                     │
  │  ══════════ HUMAN REVIEW GATE ══════════           │
  │                                                     │
  │  ATLAS_MODE = "review"                              │
  │                                                     │
  │  All 27 emails are queued for Nader's review.       │
  │  Teams notification sent:                           │
  │                                                     │
  │  "📋 ATLAS Daily Batch Ready for Review             │
  │   27 accounts, 54 email variants generated          │
  │   22 high-confidence, 4 medium, 1 low               │
  │   Review at: [dashboard link]                        │
  │   Est. review time: 15-20 minutes"                  │
  │                                                     │
  │  Nader reviews at 9:00 AM:                          │
  │  ✅ Approved 24 accounts (48 variants)              │
  │  ✏️ Edited 2 accounts (adjusted messaging)          │
  │  ❌ Rejected 1 account (wrong persona match)        │
  │                                                     │
  │  [SEND APPROVED BATCH]                              │
  │                                                     │
  └─────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════

STEP 5: FORGE — Executing Outreach (Post-Approval)
─────────────────────────────────────────────────────

  [09:15:00] Human approval received. Executing...
  
  [09:15:02] Creating prospects in Outreach...
    ✓ Created: Sarah Johnson (First National Bank)
    ✓ Created: David Martinez (Midwest Credit Union)
    ... (26 total) ...
    
  [09:15:30] Creating sequences in Outreach...
    ✓ Sequence "ATLAS-Net-New-Compliance-Apr17-A" created (13 prospects)
    ✓ Sequence "ATLAS-Net-New-Compliance-Apr17-B" created (13 prospects)
    → A/B split: half get Variant A, half get Variant B
    
  [09:15:45] Enrolling prospects...
    ✓ 26 prospects enrolled in sequences
    ✓ Sends scheduled: staggered over next 4 hours (deliverability)
    ✓ First emails go out at 9:30 AM ET (optimal send time)
    
  [09:15:50] Logging to Salesforce...
    ✓ 26 tasks created: "ATLAS Outreach — Step 1 Sent"
    ✓ Lead status updated: "In Sequence"
    ✓ Account notes updated with research brief

  [09:15:55] Today's sends complete.
    📊 Summary:
    - 26 net new accounts entered pipeline
    - 26 personalized emails scheduled
    - 13 in A/B Variant A, 13 in Variant B
    - Estimated delivery: 9:30 AM - 1:30 PM ET
    - Next check: replies monitored every 30 minutes

═══════════════════════════════════════════════════════════

STEP 6: VITALS — Pipeline Health Check (Runs in parallel)
─────────────────────────────────────────────────────

  [06:03:00] Scanning for stale leads...
  [06:03:05] Found 14 leads with no activity in 8+ days:
    ⚠ Jennifer Walsh (Commerce Bank) — last activity: 9 days ago
    ⚠ Robert Kim (Valley Federal) — last activity: 11 days ago
    ... (12 more) ...
    → Teams alerts sent to assigned reps
    
  [06:03:10] Scanning for stale opportunities...
  [06:03:15] Found 8 opps with no activity in 14+ days:
    🔴 $85K — Heritage Financial Group — 23 days inactive (AE: Scott)
    🔴 $62K — Mountain State Bank — 18 days inactive (AE: Nathan)
    ... (6 more) ...
    → Teams alerts sent to AEs + managers
    → Tasks created in Salesforce
    
  [06:03:20] Pipeline health summary:
    Total open pipeline: $2.9M
    Active (activity in 14 days): $1.1M (38%)
    Stale (14-90 days): $980K (34%)
    Critical (90+ days): $820K (28%)
    
    → Weekly digest scheduled for Friday 8 AM

═══════════════════════════════════════════════════════════

STEP 7: PHOENIX — Closed-Lost Recovery (Runs weekly, Mondays)
─────────────────────────────────────────────────────

  [06:04:00] Scanning closed-lost opportunities...
  [06:04:05] Pool: 312 closed-lost opps, $5.5M total value
  
  [06:04:10] Segmentation results:
    CONTRACT_TIMING: 89 opps ($1.8M)
      → 23 have competitor contracts expiring in next 6 months
      → These are READY for re-engagement NOW
      
    BUDGET_DEFERRED: 134 opps ($2.1M)
      → 41 lost in H2 2025 (fiscal year reset approaching)
      → Budget likely re-allocated for new fiscal year
      
    PLATFORM_CHANGE: 52 opps ($1.1M)
      → ⚠ HOLD — only activate when product update is ready
      
    UNCLASSIFIABLE: 37 opps ($500K)
      → Free-text loss reasons need manual classification
      → Queued for Nader/Amy to categorize
      
  [06:04:15] This week's PHOENIX batch:
    → 12 Contract Timing accounts (highest urgency)
    → Generating personalized re-engagement emails...
    → Queued for human review (Tier 2 — always reviewed)

═══════════════════════════════════════════════════════════

STEP 8: MONITOR — Reply Detection (Every 30 minutes)
─────────────────────────────────────────────────────

  [13:30:00] Checking Outreach for new replies...
  [13:30:03] 🔥 NEW REPLY DETECTED

    From: Sarah Johnson <sarah.johnson@firstnationalbank.com>
    Subject: Re: Compliance documentation at mid-size banks
    
    "Luke, thanks for reaching out. We're actually in the middle of 
    evaluating a couple of options right now. Can you send over a 
    one-pager on what Colibri's solution covers? I'd want to share 
    it with our VP of Ops before scheduling anything."

  [13:30:04] Classifying reply via Claude...
  [13:30:05] Classification: POSITIVE (confidence: 0.92)
    → Buying signal: Active evaluation in progress
    → Next action: Send one-pager, follow up in 2 days
    → Urgency: HIGH
    
  [13:30:06] Teams alert sent to Luke Pearson:
    "🔥 HOT REPLY: Sarah Johnson @ First National Bank
     She's evaluating options and wants a one-pager for VP Ops.
     SEND NOW → follow up Thursday."

  [13:30:07] Salesforce updated:
    → Lead status: "Replied — Positive"
    → Task created: "Send one-pager to Sarah Johnson"
    → Activity logged: "ATLAS outreach received positive reply"

  [13:30:08] Outreach updated:
    → Prospect marked: "Replied"
    → Sequence paused (don't send Step 2 — she already replied)

  [13:30:09] Learning engine updated:
    → Record: Variant A + Compliance persona + regulatory trigger
      + Tuesday 9:30AM + Decision stage = POSITIVE REPLY
    → This data point makes future targeting slightly smarter

═══════════════════════════════════════════════════════════

  END OF DAY SUMMARY (sent to Teams at 6:00 PM ET)

  ┌─────────────────────────────────────────────────────┐
  │  📊 ATLAS Daily Report — April 17, 2026             │
  │                                                      │
  │  OUTREACH:                                           │
  │  • 26 new accounts entered pipeline                  │
  │  • 26 personalized emails sent                       │
  │  • 1 positive reply (3.8% reply rate)                │
  │  • 0 bounces, 0 unsubscribes                         │
  │  • A/B winner: Variant A (1 reply) vs B (0 replies)  │
  │                                                      │
  │  PIPELINE HEALTH:                                    │
  │  • 14 stale lead alerts sent                         │
  │  • 8 stale opp alerts sent                           │
  │  • 3 reps acknowledged and took action               │
  │                                                      │
  │  PHOENIX (weekly):                                   │
  │  • 12 closed-lost accounts queued for re-engagement  │
  │  • Awaiting Nader's review                           │
  │                                                      │
  │  DATA QUALITY:                                       │
  │  • 1 duplicate merged automatically                  │
  │  • 3 accounts flagged for human review               │
  │  • 1 bounced email identified — alt contact needed   │
  │                                                      │
  │  WEEK-TO-DATE:                                       │
  │  • 78 accounts entered pipeline                      │
  │  • 3 positive replies (3.8% reply rate)              │
  │  • 1 meeting scheduled                               │
  │  • vs. Q1 baseline: 0.6% reply rate                  │
  │                                                      │
  └─────────────────────────────────────────────────────┘
```

---

## 10. What the Agent Does Every Day

### Daily Schedule (Automated)

| Time | Agent | Action |
|------|-------|--------|
| **6:00 AM** | SCOUT | Pull latest 6sense intent signals, identify new targets |
| **6:01 AM** | SENTINEL | Run dedup, apply exclusion filters, clean data |
| **6:03 AM** | RECON | Generate research briefs for all new targets |
| **6:06 AM** | FORGE | Generate personalized email sequences |
| **6:06 AM** | VITALS | Scan for stale leads and opps, send alerts |
| **6:10 AM** | CORTEX | Package review batch, send to Teams for human approval |
| **9:00 AM** | HUMAN | Nader reviews and approves batch (~15-20 min) |
| **9:15 AM** | FORGE | Execute approved sends via Outreach |
| **Every 30 min** | CORTEX | Check for replies, classify, alert reps |
| **6:00 PM** | COMMAND | Generate and send daily summary |
| **Monday 6 AM** | PHOENIX | Weekly closed-lost recovery batch |
| **Friday 8 AM** | COMMAND | Weekly pipeline digest to leadership |

### Monthly Cadence

| Week | Focus | Human Time Required |
|------|-------|-------------------|
| **Week 1** | Review 100% of agent output, validate quality | 1-2 hours total |
| **Week 2** | Review 50%, spot-check the rest | 30-45 min total |
| **Week 3** | Review flagged items + edge cases only | 15-20 min total |
| **Week 4+** | Review exceptions, weekly metrics review | 10-15 min total |

### The Numbers Over Time

```
MONTH 1 (Ramp-up):
  Accounts entered pipeline:  160
  Emails sent:                160
  Expected replies (3%):      ~5
  Expected meetings:          ~2-3
  Expected pipeline created:  $150K-$225K

MONTH 3 (Optimized):
  Accounts entered pipeline:  480 (cumulative)
  Emails sent:                480
  Reply rate (improving):     4-5%
  Meetings from outreach:     8-12
  Pipeline created:           $600K-$900K
  First closed-won from ATLAS: $75K

MONTH 6 (Compounding):
  Accounts entered pipeline:  960 (cumulative)
  Learning engine active:     knows what works per persona/segment
  Reply rate:                 5-7%
  PHOENIX recoveries:         3-5 re-opened deals
  Total pipeline influenced:  $1.5M-$2.5M
  Revenue attributable:       $150K-$300K closed-won
```

---

## 11. Monitoring & Troubleshooting

### Health Checks

The agent runs a self-check every morning before executing:

```
[06:00:00] ATLAS HEALTH CHECK
  ✅ Salesforce API: connected (response: 142ms)
  ✅ Outreach API: connected (response: 89ms)
  ✅ 6sense API: connected (response: 203ms)
  ✅ Claude API: connected (response: 312ms)
  ✅ Teams webhook: connected (response: 67ms)
  ✅ SQLite database: 2.3MB, 847 records
  ✅ Daily send limit: 25 (3 used today)
  ✅ Last run: successful (April 16, 06:00 AM)
  ─────────────────────────────────
  ALL SYSTEMS GO. Starting daily run.
```

### If Something Goes Wrong

| Problem | What Happens | Auto-Recovery |
|---------|-------------|---------------|
| Salesforce API down | Agent logs error, retries in 30 min, alerts Teams | Yes — retries 3x then pauses |
| Outreach API down | Emails queued locally, sent when API recovers | Yes — queue persists |
| 6sense API down | Uses last successful pull (cached) | Yes — cache valid 24 hours |
| Claude API down | Uses pre-generated templates as fallback | Yes — template mode |
| Teams down | Alerts sent via email backup | Yes — email fallback |
| Agent crashes | Systemd restarts automatically, logs preserved | Yes — auto-restart |
| Daily limit reached | Agent stops sending, resumes next day | Yes — hard cap |
| Bad data detected | Agent quarantines record, alerts human | Yes — quarantine |

### The Kill Switch

At any point, anyone can stop the agent:

```bash
# Stop all automated sends immediately
echo "ATLAS_MODE=paused" >> .env
# Agent will complete current operation then pause

# Or from Teams:
# Type: /atlas pause
# Agent responds: "⏸️ ATLAS paused. No further sends until resumed."

# Resume:
echo "ATLAS_MODE=review" >> .env
# Or: /atlas resume
```

### Logs

Every action the agent takes is logged:

```
# View today's log
tail -f logs/atlas_2026-04-17.log

# View all sends
grep "SEND" logs/atlas_2026-04-17.log

# View all errors
grep "ERROR" logs/atlas_2026-04-17.log

# View reply detections
grep "REPLY" logs/atlas_2026-04-17.log
```

---

## Quick Reference: Everything You Need

| Item | Where to Get It | Who Provides It |
|------|----------------|-----------------|
| Salesforce Consumer Key | Setup → App Manager → ATLAS app | SF Admin (Angel) |
| Salesforce Consumer Secret | Same as above | SF Admin (Angel) |
| Salesforce API User + Password | Setup → Users | SF Admin (Angel) |
| Salesforce Security Token | User Settings → Reset Token | SF Admin (Angel) |
| Outreach Client ID | Settings → API Access → OAuth Apps | Amy Ketts |
| Outreach Client Secret | Same as above | Amy Ketts |
| Outreach Access Token | OAuth authorization flow | Amy Ketts authorizes |
| Outreach Refresh Token | Same as above | Amy Ketts authorizes |
| 6sense API Key | Settings → Integrations → API | Marketing / 6sense admin |
| Claude API Key | console.anthropic.com → API Keys | Sam (already have) |
| Teams Webhook URL | Teams channel → Connectors → Incoming Webhook | Anyone with Teams channel access |

**Total setup time once credentials are provided: ~30 minutes.**
**Total setup time including credential requests: 1-3 days (waiting on admins).**

---

**Once all 5 connections test green, ATLAS is ready to run its first daily cycle.**

The first real email lands in a real prospect's inbox within 24 hours of setup.

---

*ATLAS — Autonomous Territory & Lead Acceleration System*
*Sam Chaudhary | samcolibri*

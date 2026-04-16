# ATLAS — Blind Spots, Gaps & Things Nobody Has Asked Yet

> These are the things that will bite us if we don't think about them before we go live. Not feature requests — real operational risks and gaps.

---

## 1. Email Deliverability Will Kill Us Before Content Quality Matters

**The problem nobody has addressed:** We're focused on writing better emails. But if those emails land in spam, it doesn't matter how good they are.

The Opp 2 report itself says: *"Google and Microsoft now aggressively filter high-volume sequence sends, reducing inbox rates across all platforms that rely on spray-and-pray cadences."*

### What we need to check BEFORE sending anything:

| Check | Why It Matters | How to Check |
|-------|---------------|-------------|
| **Colibri's domain reputation** | If the domain is already burned from 6,871 generic emails with 0% reply rate, new emails may go straight to spam | Check at mail-tester.com, Google Postmaster Tools, MXToolbox |
| **SPF/DKIM/DMARC records** | If these aren't properly configured on Colibri's domain, email providers will flag sends as suspicious | `dig TXT colibrigroup.com` and check for SPF/DKIM/DMARC records |
| **Outreach sending infrastructure** | Which mailboxes are we sending from? Luke's? Griffin's? A shared mailbox? Each has different reputation. | Check Outreach mailbox health scores in Settings → Mailboxes |
| **Griffin's mailbox specifically** | If Griffin was logging 573 phantom calls AND sending 3,365 generic sequence emails, his mailbox reputation could be destroyed | Check his bounce rate, spam complaint rate, and domain reputation separately |
| **Daily send volume limits** | Suddenly going from ~50 emails/day to 160/month sounds low, but if sent in batches, it could trigger spam filters | Start at 10/day for Week 1, ramp to 15, then 20, then 25 |

### What we might need:

- **A new sending subdomain** (e.g., `outreach.colibrigroup.com`) with fresh reputation, properly warmed up over 2-4 weeks before high-volume sends
- **Mailbox warming** — if we're sending from Luke or a new mailbox, gradually increase volume from 5/day → 10 → 15 → 25 over 2-3 weeks
- **Send from the assigned rep's mailbox, not a shared one** — emails from "Luke Pearson" with Luke's actual email address get better inbox placement than from "Colibri Sales Team"

**Bottom line:** We need a deliverability audit before anything else. The best AI-written email in the world doesn't matter if it lands in spam. This could be a 1-2 week prerequisite that shifts the timeline.

---

## 2. We Don't Know Colibri's Salesforce Schema

**The problem:** Every API call in the PLAYBOOK assumes field names like `Loss_Reason__c`, `StageName = 'Closed Lost'`, standard objects, etc. But every Salesforce org is different.

### What we need to discover:

| Question | Why It Matters | Impact If Wrong |
|----------|---------------|----------------|
| What are the actual stage names for opportunities? | "Closed Lost" might be "Closed - Lost" or "Lost" or a custom value | PHOENIX pulls wrong data or no data |
| Is there a Loss Reason field? What's it called? Is it a picklist or free text? | The entire PHOENIX segmentation depends on this | Can't auto-segment if field doesn't exist or is free text |
| How are leads vs contacts structured? | Some orgs use leads only, some convert to contacts, some use both | Agent might miss records or create duplicates |
| What custom fields exist on Account/Lead/Opportunity? | Custom fields often hold critical business data (territory, product line, BU) | Miss important filtering criteria |
| Are there Record Types? | GRC vs Insurance vs other business units may use different record types | Agent might pull Insurance opportunities into a GRC campaign |
| What does the lead status picklist look like? | "Attempting Contact" might be spelled differently | Stale lead detection misses records |
| How is lead ownership/assignment structured? | Round-robin? Territory-based? Manual? | Agent assigns to wrong rep |
| Are there validation rules or triggers that might block API writes? | Salesforce often has required fields or automation that fires on record update | Agent writes fail silently or cause unintended side effects |

### What to do:
Before writing a single line of agent code, run a **Salesforce schema discovery session**:
```
GET /services/data/v59.0/sobjects/Opportunity/describe
GET /services/data/v59.0/sobjects/Lead/describe
GET /services/data/v59.0/sobjects/Account/describe
```
This returns every field, every picklist value, every record type. Map the ATLAS data model to the actual Colibri schema.

---

## 3. Rep Preparedness — What Happens When Replies Come In

**The gap:** ATLAS generates outreach and detects replies. But when Sarah Johnson at First National Bank says "sure, let's talk" — is Luke actually ready for that conversation?

### What Luke needs BEFORE the first reply:

| Asset | Status | Who Creates It |
|-------|--------|----------------|
| **Discovery call framework** — what questions to ask compliance officers at mid-size banks | Doesn't exist (no standardized discovery) | Nader + Nathan |
| **Talk tracks by persona** — compliance vs HR/L&D vs operations have different conversations | Doesn't exist | Nader |
| **Competitive battlecards** — what to say when prospect mentions they're evaluating alternatives | May be outdated (Sales Enablement Content Refresh is Sprint 6 — backup) | Marketing + Nader |
| **Product one-pager** — Sarah literally asked for one in our example | Does it exist? Is it current? Is it GRC-specific? | Marketing |
| **Demo environment** — if the discovery call goes well and prospect wants to see the product | Needs confirmation | Product/Sales Engineering |
| **Handoff process** — when does Luke hand to an AE? What info transfers? | May be informal | Sales leadership |

**If ATLAS books a meeting and Luke isn't ready for it, we've wasted the opportunity AND burned a high-intent account.**

### What to do:
- Before Phase 2 (outreach engine) goes live, create a simple **"ATLAS Meeting Prep Kit"**
- RECON already generates the account brief — include a discovery question guide tailored to the persona
- Make this part of the Teams alert: "Meeting with Sarah Johnson. Here's the brief + recommended discovery questions + one-pager attached."

---

## 4. Multi-Threading — One Contact Per Account Isn't Enough

**The documents say it clearly:** Buying committees have grown to 6-10 stakeholders. Our current design targets one contact per account (the primary persona match).

### Why single-threading fails:
- Sarah Johnson (CCO) might be interested but can't make the decision alone
- Mike Chen (VP Ops) might be the actual budget holder
- Lisa Park (Dir Training) might be the day-to-day user
- If we only email Sarah and she's busy/on vacation/not the decision maker, the account stalls

### What ATLAS should actually do:
```
Account: First National Bank
  Contact 1: Sarah Johnson (CCO) — Primary sequence (compliance angle)
  Contact 2: Mike Chen (VP Ops) — Secondary sequence (efficiency angle)
  Contact 3: Lisa Park (Dir Training) — Tertiary sequence (LMS angle)
  
  Rules:
  - Stagger sends: Sarah on Day 1, Mike on Day 3, Lisa on Day 5
  - If Sarah replies positively → pause Mike and Lisa
  - If Sarah ignores → Mike becomes primary on Day 7
  - If any reply mentions a colleague → reference the thread
  - Maximum 3 contacts per account (don't spam the whole org)
```

This is Phase 2+ complexity, but it should be designed into the architecture now so we don't have to retrofit it later.

---

## 5. Sequence Cadence Design — We Haven't Defined the Actual Steps

**The gap:** We've talked about generating "personalized sequences" but haven't defined what a sequence actually looks like. How many steps? What channels? What timing?

### Recommended cadence structure (based on what works in B2B FS):

```
NET NEW (high-intent) — 5 steps over 14 days:

  Day 1:  📧 Email 1 (personalized, trigger-based)
  Day 3:  📞 Call 1 (reference email, ask for 20 min)
  Day 5:  📧 Email 2 (different angle — if compliance didn't work, try efficiency)
  Day 8:  📞 Call 2 + voicemail drop
  Day 12: 📧 Email 3 (breakup email — "last note, here if you need us")
  Day 14: 🔗 LinkedIn connection request (soft touch, no pitch)

PHOENIX (closed-lost) — 3 steps over 21 days:

  Day 1:  📧 Email 1 (re-engagement tied to trigger — contract timing, budget reset)
  Day 7:  📧 Email 2 (value-add — share relevant content or case study)
  Day 14: 📧 Email 3 (direct ask — "worth revisiting?")
  Day 21: If no reply → mark as exhausted, re-check in 6 months

INBOUND (form submission) — 4 steps over 10 days:

  Day 0:  📧 Email 1 (immediate acknowledgment, <5 min, personalized)
  Day 1:  📞 Call 1 (same-day or next morning, reference form submission)
  Day 3:  📧 Email 2 (offer specific value — assessment, demo, case study)
  Day 7:  📞 Call 2 + 📧 Email 3 (last touch, provide direct calendar link)
```

### What this means for FORGE:
- FORGE doesn't just generate one email — it generates the full multi-step, multi-channel cadence
- Each step needs different copy (can't send the same message 3 times)
- Call steps need talk track snippets (what to say when they pick up)
- LinkedIn steps need connection request messaging

---

## 6. Sandbox Testing — Don't Touch Production on Day 1

**The risk:** If we connect ATLAS directly to production Salesforce + production Outreach and something goes wrong — bad data writes, duplicate records, accidental mass emails — it's live and visible to everyone.

### What we should do:
1. **Salesforce Sandbox** — Colibri almost certainly has a sandbox (every enterprise org does). Connect ATLAS to sandbox first. Test all reads and writes against sandbox data.
2. **Outreach Staging** — Outreach doesn't have a traditional sandbox, but we can:
   - Create sequences in "Draft" mode (won't send)
   - Use a test mailbox that sends to ourselves
   - Create prospects with test email addresses
3. **6sense** — Read-only, so production is fine for testing
4. **Claude** — No risk, it's a generation engine
5. **Microsoft Teams** — Use an "ATLAS Testing" channel in Teams, not the real sales channel

### Testing checklist before going to production:
- [ ] All Salesforce queries return expected data shapes
- [ ] Salesforce writes don't trigger unexpected automation (workflows, flows, triggers)
- [ ] Outreach prospect creation doesn't create duplicates
- [ ] Outreach sequence enrollment works correctly
- [ ] Exclusion filters correctly block current customers, active deals, etc.
- [ ] Deduplication logic correctly identifies and flags real duplicates
- [ ] Claude-generated content passes human review at >90% approval rate
- [ ] Reply detection correctly classifies positive/negative/OOO
- [ ] Kill switch works (pause → all activity stops within 60 seconds)

---

## 7. Legal & Compliance — CAN-SPAM and FS-Specific Requirements

**The overlooked risk:** We're automating outreach to people at banks and financial institutions. These are heavily regulated entities with strict vendor communication policies.

### What we need to verify:

| Requirement | Status | Risk |
|-------------|--------|------|
| **CAN-SPAM compliance** — unsubscribe link in every email, physical address, no deceptive subject lines | Outreach handles this automatically — but verify templates include required elements | Low (Outreach manages) |
| **Opt-out list syncing** — if someone unsubscribes via Outreach, is that synced to Salesforce? | Unknown — need to verify | Medium (could re-email someone who unsubscribed) |
| **State-specific regulations** — California (CCPA), EU (GDPR if any international prospects) | Probably US-only for GRC, but verify | Low for now |
| **Internal compliance approval** — does Colibri's legal/compliance team need to approve automated outreach? | Unknown — Molly/Scott should confirm | Medium (could be a blocker) |
| **Financial services vendor policies** — some banks prohibit unsolicited vendor emails to specific roles | Need to research per prospect | Low (standard B2B outreach is generally acceptable) |
| **Data retention** — ATLAS stores prospect data in local SQLite. Is this acceptable per Colibri's data policies? | Unknown | Medium (may need to use Salesforce as sole data store) |
| **Email content approval** — does Colibri have a marketing/legal review process for outbound messaging? | Unknown — typical at enterprise companies | Medium (could add review cycle) |

### What to do:
Quick conversation with Molly or Colibri legal: "We're automating B2B outreach using existing Outreach platform to financial services prospects. All emails include standard CAN-SPAM compliance. Any additional requirements we should be aware of?"

---

## 8. Attribution — How We PROVE ATLAS Generated Revenue

**The problem:** If ATLAS sends an email, the prospect replies, Luke has a meeting, and the deal closes 4 months later — how do we prove ATLAS was the cause?

### Without attribution, ATLAS gets killed:
- Leadership asks "what's the ROI?"
- We say "well, we sent emails and some deals closed"
- They say "reps were going to contact those accounts anyway"
- ATLAS loses funding/support

### Attribution framework:

| Signal | What We Track | How |
|--------|-------------|-----|
| **ATLAS-sourced lead** | Account was identified by ATLAS (via 6sense intent), not by a rep | Tag in Salesforce: `Lead_Source = 'ATLAS'` |
| **ATLAS-generated outreach** | First outreach was AI-generated, not manually written | Tag in Outreach: prospect has `atlas` tag |
| **ATLAS-influenced pipeline** | Opportunity was created after ATLAS touched the account | Track `Opportunity.CreatedDate` > `Lead.FirstATLASTouch` |
| **ATLAS-recovered pipeline** | Closed-lost deal re-opened after PHOENIX sequence | Tag: `ATLAS_Recovery = true` on opportunity |
| **First-touch vs multi-touch** | ATLAS was the first to contact vs. one of many touches | Log all ATLAS touches with timestamps in Salesforce |

### Salesforce custom fields needed:
```
Lead:
  - ATLAS_First_Touch__c (DateTime)
  - ATLAS_Source__c (Picklist: Net New / Phoenix / Inbound)
  - ATLAS_Sequence__c (Text: which sequence they entered)

Opportunity:
  - ATLAS_Influenced__c (Checkbox)
  - ATLAS_Recovery__c (Checkbox)
  - ATLAS_Pipeline_Value__c (Currency: value at time of creation)
```

**Without these fields from Day 1, we can't prove ROI.** Add them before the first send.

---

## 9. The Outreach Renewal (May 5) — Timing Pressure

**The overlooked urgency:** Outreach renewal is $42,270.72/yr and due May 5, 2026. That's 19 days from now.

### Why this matters:
- Sprint 3 (Outreach Sequence Audit & Rebuild) directly justifies the Outreach renewal
- If ATLAS can show early results before May 5, it strengthens the renewal business case
- If Outreach API access isn't on the current tier, renewal negotiation is the moment to add it (free leverage)

### What to do:
1. Confirm API access is included in current contract (Amy to check)
2. If not, tell Outreach rep during renewal: "We're building an integration that will dramatically increase our utilization of the platform — we need API access included"
3. Target: have ATLAS connection tested and first batch reviewed BEFORE May 5 renewal meeting
4. Even just showing "we pulled 6sense data, generated 50 personalized sequences, and they're ready to send" is a powerful demo for renewal justification

---

## 10. What If 6sense Intent Data Isn't Good?

**The assumption we're betting on:** 6sense intent signals accurately identify companies that are ready to buy GRC solutions. Our entire SCOUT agent depends on this.

**The risk:** The Opp 2 report flags "brand mixing" — intent signals attributed to Colibri that are actually for adjacent brands. If 6sense is showing "high intent" for accounts that are actually researching a competitor's GRC product (not Colibri's), our targeting is garbage.

### What to do:
1. **Before trusting 6sense scores:** Pull the top 20 intent accounts and have Nathan/Nader manually verify — do these accounts look like real prospects? Have any of them actually engaged with Colibri content?
2. **Track intent-to-reply correlation:** After Month 1, check if higher 6sense scores actually correlate with higher reply rates. If intent score 90 and intent score 50 have the same reply rate, the signal is noise.
3. **Fallback plan:** If 6sense data isn't reliable, SCOUT switches to:
   - Firmographic targeting (company size + industry + geography)
   - Salesforce engagement history (opened emails, visited website, attended webinar)
   - LinkedIn activity signals (job changes, company news)

Don't go all-in on 6sense until we've validated the signal quality with real outreach data.

---

## 11. The Demo for Leadership — What Does Day 1 Look Like?

**Nobody has planned the demo.** At some point, Sam or Nader will need to show Molly, Scott, and Nathan what ATLAS actually does. This is make-or-break for continued support.

### The 10-Minute Demo Script:

```
MINUTE 0-2: THE PROBLEM (their data)
  "Here's what Q1 looked like: 6,871 emails, 0.6% reply rate, $5.5M 
  in closed-lost with zero follow-up. You already know this. 
  Here's what we built to fix it."

MINUTE 2-4: LIVE PULL (SCOUT + SENTINEL)
  Run ATLAS live. Show it pulling from 6sense:
  "These are the top 10 accounts showing buying intent RIGHT NOW."
  Show the exclusion filters running:
  "3 excluded — they're current customers. ATLAS caught it."

MINUTE 4-6: AI RESEARCH + OUTREACH (RECON + FORGE)
  Pick one account from the live pull. Generate a brief:
  "This took 4 seconds. It used to take 20 minutes."
  Generate the personalized email:
  "Two variants. Both reference real triggers. Both sound human."
  Ask someone in the room: "Would you reply to this? Compare to what 
  went out in Q1." (Show a Q1 generic sequence email side by side.)

MINUTE 6-8: PIPELINE HEALTH (VITALS)
  Show the stale opp scan:
  "Here are 8 deals with $680K in value that haven't been touched 
  in 2+ weeks. ATLAS caught these at 6 AM. The reps got Teams 
  alerts before they started their day."

MINUTE 8-10: THE ASK
  "We need Salesforce API access, Outreach API access, and 6sense 
  API access. Nader reviews everything before it sends. First real 
  emails go out Week 3. We'll know if it's working by Week 4.
  Break-even is 2 deals. What questions do you have?"
```

---

## 12. Handling Sequence Collisions

**The gap:** What if a prospect is already in a manually-created Outreach sequence when ATLAS tries to enroll them in a new one?

### Scenarios:
- Griffin enrolled someone in a generic sequence 3 weeks ago → ATLAS wants to enroll them in a persona-specific one
- Luke has a prospect in an active sequence → ATLAS identifies the same person through 6sense
- An old paused sequence has 200 prospects still "enrolled" but no emails going out

### Rules ATLAS needs:
```
BEFORE enrolling any prospect in an Outreach sequence:

  1. Check: Is this prospect currently in ANY active sequence?
     → YES: Do NOT enroll. Log as "skipped — active sequence"
     
  2. Check: Is this prospect in a PAUSED sequence?
     → YES: Flag for human review. Should we remove from old + add to new?
     
  3. Check: Has this prospect completed a sequence in the last 90 days?
     → YES: Do NOT enroll (too soon for re-contact)
     → Unless it's a PHOENIX recovery sequence (different context)
     
  4. Check: Is this prospect's email in the Outreach do-not-contact list?
     → YES: Do NOT enroll. Log and skip permanently.
```

---

## 13. What Happens When the Agent Finds Something Unexpected?

**Real scenarios that WILL happen:**

| Scenario | What ATLAS Should Do |
|----------|---------------------|
| 6sense shows high intent for a company that's already a Colibri customer | Exclude from outreach, but alert the account team: "Your customer is researching GRC solutions — possible upsell or churn risk" |
| A closed-lost contact has moved to a different company | This is actually an opportunity — they already know Colibri. Flag for Nader: "Former prospect now at a new company within ICP" |
| An account appears on 6sense but has a pending legal dispute with Colibri | Hard exclude. But how does ATLAS know about legal disputes? Need a "do not contact" list maintained somewhere. |
| A reply comes in that's angry or threatening ("stop emailing me, I'm reporting this as spam") | Immediate auto-remove from all sequences. Alert Nader. Add to permanent exclusion list. Log the incident. |
| ATLAS detects that a Colibri employee's email is in the prospect database | Exclude. This happens more often than you'd think in recycled Salesforce databases. |
| Two different reps at Colibri are working the same account (Luke outbound, AE inbound) | Alert both reps and their manager. Let humans coordinate. ATLAS pauses its outreach on that account. |

These edge cases need to be designed into the agent logic BEFORE go-live, not discovered after embarrassing incidents.

---

## 14. The Budget Conversation — What This Actually Costs to Run

**Everyone assumes "near-zero cost" but let's be precise:**

### Monthly Operating Costs (Once Live)

| Item | Cost | Notes |
|------|------|-------|
| Claude API (160 accounts × research + emails + classification) | $50-100/mo | Sonnet for bulk, Haiku for classification |
| Relay.app (if used for 6sense→Outreach orchestration) | $0-38/mo | Free tier may suffice |
| Hosting (if we move off local to a VPS) | $0-20/mo | Only needed for 24/7 uptime |
| Microsoft Teams (already have it) | $0 | Using existing workspace |
| Salesforce API (already licensed) | $0 | Included with enterprise license |
| Outreach API (already licensed — need to confirm) | $0 | May need tier upgrade at renewal |
| 6sense API (already licensed — need to confirm) | $0 | May be an add-on |
| **Total** | **$50-158/month** | **$600-1,900/year** |

### One-Time Setup Costs

| Item | Cost | Notes |
|------|------|-------|
| Sam's time building ATLAS | Internal | ~80-120 hours over 4 weeks |
| Nader's time reviewing/configuring | Internal | ~20-30 hours over 4 weeks |
| Amy's time on Outreach API/config | Internal | ~5-10 hours |
| Angel's time on Salesforce API setup | Internal | ~5-10 hours |

### ROI Math
```
Cost to run:          ~$1,200/year
Cost to build:        ~160 internal hours (one-time)

Revenue from 1 deal:  $75,000
Break-even:           0.016 deals (effectively: first reply that converts)

Expected Year 1:      $1.35M-$2.85M in pipeline influenced
ROI:                  1,125x - 2,375x
```

**This is not a budget conversation. This is a rounding error compared to the $42K Outreach renewal.** But having the numbers ready prevents anyone from using "cost" as an objection.

---

## Summary: The Pre-Launch Checklist

Everything above, compressed into what needs to happen before ATLAS goes live:

### Before ANY Code Runs (Week 0)
- [ ] Salesforce schema discovery (actual field names, picklist values, record types)
- [ ] Salesforce sandbox access for testing
- [ ] Outreach API access confirmed on current contract tier
- [ ] Email deliverability audit (domain reputation, SPF/DKIM/DMARC, mailbox health)
- [ ] 6sense intent signal validation (top 20 accounts manually reviewed)
- [ ] CAN-SPAM compliance verification with Colibri legal
- [ ] Nader briefed and bought in as "strategist + quality gate" (not replaced)
- [ ] Attribution fields created in Salesforce (ATLAS_First_Touch, ATLAS_Source, etc.)
- [ ] Do-not-contact list assembled (legal disputes, employees, bad data)
- [ ] Outreach renewal conversation strategy (API access as negotiation point)

### Before First Send (Week 2-3)
- [ ] All API connections tested in sandbox/staging
- [ ] Exclusion filters validated against real data
- [ ] Deduplication tested against known duplicates
- [ ] 50 AI-generated emails reviewed and approved by Nader
- [ ] Sequence cadence defined (steps, timing, channels)
- [ ] Rep prep kit created (discovery framework, talk tracks, one-pager)
- [ ] Teams alerts tested in ATLAS Testing channel
- [ ] Kill switch tested (pause → verify all activity stops)
- [ ] Sequence collision rules implemented and tested
- [ ] Demo prepared for leadership (10-minute script)

### Before Scaling Past Pilot (Week 4+)
- [ ] Reply rate exceeds Q1 baseline (0.6%)
- [ ] Zero embarrassing incidents (wrong person, current customer, angry reply)
- [ ] Nader approval rate >90% (agent output is consistently good)
- [ ] Email deliverability stable (no spike in bounces or spam complaints)
- [ ] Leadership demo completed, support confirmed
- [ ] Attribution data flowing (can prove ATLAS-sourced pipeline)

---

**If we handle these blind spots before go-live, ATLAS launches clean. If we don't, we'll discover them as incidents — and incidents kill projects faster than bad code.**

---

*ATLAS — Autonomous Territory & Lead Acceleration System*
*Sam Chaudhary | samcolibri*

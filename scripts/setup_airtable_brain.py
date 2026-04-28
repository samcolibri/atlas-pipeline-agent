"""
Create and configure the full ATLAS Airtable brain — 4 new tables.

Tables created:
  Knowledge_Base   — PDFs, Word docs, transcripts, frameworks, playbooks
                     Agent drops files here, pipeline extracts + indexes them
  AB_Results       — Live A/B test performance tracking (CTA × Framework × Lane)
  Learned_Signals  — CORTEX captures patterns from every reply over time
  Enrichment_Queue — Contacts waiting for Waterfall + ZeroBounce processing

Run once:
    python3 scripts/setup_airtable_brain.py
"""

import os, time, requests
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

TOKEN   = os.getenv("AIRTABLE_TOKEN")
BASE_ID = os.getenv("AIRTABLE_BASE_ID", "appwlGCHBaRef70gO")
headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

TABLES_URL = f"https://api.airtable.com/v0/meta/bases/{BASE_ID}/tables"

ok_tables = err_tables = 0


def checkbox():
    return {"type": "checkbox", "options": {"icon": "check", "color": "greenBright"}}

def select(choices):
    return {"type": "singleSelect", "options": {"choices": [{"name": c} for c in choices]}}

def multiselect(choices):
    return {"type": "multipleSelects", "options": {"choices": [{"name": c} for c in choices]}}

def text():
    return {"type": "singleLineText"}

def longtext():
    return {"type": "multilineText"}

def number(precision=0):
    return {"type": "number", "options": {"precision": precision}}

def date_field():
    return {"type": "date", "options": {"dateFormat": {"name": "iso"}}}

def datetime_field():
    return {
        "type": "dateTime",
        "options": {
            "dateFormat": {"name": "iso"},
            "timeFormat": {"name": "24hour"},
            "timeZone": "America/Chicago",
        },
    }

def url_field():
    return {"type": "url"}

def attachment():
    return {"type": "multipleAttachments"}

def rating(max=5):
    return {"type": "rating", "options": {"icon": "star", "max": max, "color": "yellowBright"}}

def percent(precision=1):
    return {"type": "percent", "options": {"precision": precision}}


def make_field(name, spec):
    f = {"name": name}
    f.update(spec)
    return f


def create_table(name, fields):
    global ok_tables, err_tables
    payload = {"name": name, "fields": fields}
    resp = requests.post(TABLES_URL, json=payload, headers=headers, timeout=30)
    if resp.ok:
        tid = resp.json().get("id")
        print(f"  ✓ {name} (id={tid})")
        ok_tables += 1
        return tid
    elif "already exists" in resp.text or "DUPLICATE_TABLE_NAME" in resp.text:
        print(f"  · {name} (exists)")
        ok_tables += 1
        return None
    else:
        print(f"  ✗ {name}: {resp.status_code} {resp.text[:200]}")
        err_tables += 1
        return None


# ══════════════════════════════════════════════════════════════════════
print("\n── 1. Knowledge_Base ─────────────────────────────────────────────")
print("   PDFs, Word docs, transcripts, frameworks — agent reads before LLM")

create_table("Knowledge_Base", [
    make_field("Title",            text()),
    make_field("Doc_Type",         select([
        "skill_packet", "framework", "email_example", "call_transcript",
        "research_report", "case_study", "playbook", "competitor_intel",
        "objection_handler", "persona_guide", "regulatory_update",
        "win_loss", "onboarding", "other",
    ])),
    make_field("Source_File",      attachment()),   # user drops PDF/Word here
    make_field("Extracted_Text",   longtext()),     # raw text from file
    make_field("Summary",          longtext()),     # Claude-generated 3-5 sentence summary
    make_field("Key_Insights",     longtext()),     # bullet-point learnings
    make_field("Objection_Handles",longtext()),     # objections + responses extracted
    make_field("ICP_Lane",         select(["compliance", "hr", "l_and_d", "all"])),
    make_field("Tags",             longtext()),     # comma-separated: bsa, renewal, fair_lending…
    make_field("Relevant_To",      select([
        "RECON", "FORGE", "CORTEX", "all_agents",
    ])),
    make_field("Status",           select([
        "pending_extraction", "extracting", "indexed", "active", "archived",
    ])),
    make_field("Token_Count",      number()),       # approx tokens for LLM context mgmt
    make_field("Indexed_At",       datetime_field()),
    make_field("Added_By",         text()),
    make_field("Source_Path",      text()),         # original file path if loaded from disk
    make_field("Version",          number()),
    make_field("Active",           checkbox()),
])

# ══════════════════════════════════════════════════════════════════════
print("\n── 2. AB_Results ─────────────────────────────────────────────────")
print("   Live A/B performance: CTA × Framework × Lane × Institution_Type")

create_table("AB_Results", [
    make_field("Variant_Key",      text()),         # e.g. "KCPOV_compliance_A_bank"
    make_field("Framework",        select(["5P", "KCPOV", "hybrid"])),
    make_field("CTA_Variant",      select(["A","B","C","D","E","F","G","H","I","J"])),
    make_field("ICP_Lane",         select(["compliance", "hr", "l_and_d", "all"])),
    make_field("Institution_Type", select(["bank", "credit_union", "savings", "all"])),
    make_field("Sends_Count",      number()),
    make_field("Opens_Count",      number()),
    make_field("Replies_Count",    number()),
    make_field("Interested_Count", number()),
    make_field("Meetings_Booked",  number()),
    make_field("Bounces",          number()),
    make_field("Unsubscribes",     number()),
    make_field("Open_Rate_Pct",    percent()),
    make_field("Reply_Rate_Pct",   percent()),
    make_field("Interest_Rate_Pct",percent()),
    make_field("Meeting_Rate_Pct", percent()),
    make_field("Score",            number()),       # CORTEX-computed composite score
    make_field("Is_Winner",        checkbox()),     # CORTEX promotes winner automatically
    make_field("Promoted_To_Default", checkbox()),
    make_field("Week_Of",          date_field()),
    make_field("Notes",            longtext()),
    make_field("Last_Updated",     datetime_field()),
])

# ══════════════════════════════════════════════════════════════════════
print("\n── 3. Learned_Signals ────────────────────────────────────────────")
print("   CORTEX captures patterns from every reply — builds intelligence over time")

create_table("Learned_Signals", [
    make_field("Account_Domain",   text()),
    make_field("Account_Name",     text()),
    make_field("Contact_Email",    text()),
    make_field("Signal_Type",      select([
        "vendor_mentioned",    # "we use BAI"
        "renewal_hinted",      # "contract is up in Q3"
        "renewal_confirmed",   # explicit year + month
        "referred_contact",    # "you should talk to Jane"
        "not_the_buyer",       # "that's owned by compliance"
        "budget_signal",       # mentions budget cycle
        "timing_signal",       # "check back in Q4"
        "objection_price",
        "objection_no_need",
        "objection_happy_with_vendor",
        "objection_timing",
        "objection_not_decision_maker",
        "expressed_interest",
        "requested_demo",
        "requested_info",
        "out_of_office",
        "wrong_person",
        "unsubscribe",
        "other",
    ])),
    make_field("Raw_Signal_Text",  longtext()),     # exact quote from reply
    make_field("Extracted_Value",  text()),         # e.g. "BAI" for vendor_mentioned
    make_field("Confidence",       percent()),      # CORTEX confidence 0-100
    make_field("Renewal_Year",     number()),       # if renewal signal
    make_field("Renewal_Month",    number()),
    make_field("Referred_Name",    text()),         # if referred_contact
    make_field("Referred_Title",   text()),
    make_field("Referred_Email",   text()),
    make_field("Action_Taken",     select([
        "updated_account", "queued_referred_contact", "suppressed",
        "scheduled_re_engage", "handed_to_human", "none",
    ])),
    make_field("Used_In_Training",     checkbox()),
    make_field("Outreach_Log_Ref",     text()),     # reference to Outreach_Log record
    make_field("Detected_At",      datetime_field()),
])

# ══════════════════════════════════════════════════════════════════════
print("\n── 4. Enrichment_Queue ───────────────────────────────────────────")
print("   Contacts waiting for Waterfall → ZeroBounce → Contacts table")

create_table("Enrichment_Queue", [
    make_field("Account_Name",     text()),
    make_field("Account_Domain",   text()),
    make_field("Cert_ID",          text()),
    make_field("State",            text()),
    make_field("Asset_M",          number()),
    make_field("Contact_Name",     text()),         # if already known
    make_field("Title_Hint",       text()),         # title we're searching for
    make_field("ICP_Lane",         select(["compliance", "hr", "l_and_d"])),
    make_field("Lane_Priority",    number()),       # 1, 2, 3
    make_field("Status",           select([
        "pending",
        "waterfall_searching",
        "waterfall_done",
        "zerobounce_pending",
        "zerobounce_done",
        "complete",
        "failed_no_contact",
        "failed_invalid_email",
        "suppressed",
    ])),
    make_field("Email_Found",      text()),
    make_field("Email_Status",     select([
        "valid", "invalid", "catch_all", "unknown", "spamtrap", "do_not_mail",
    ])),
    make_field("Email_Valid",          checkbox()),
    make_field("Waterfall_Attempted",  checkbox()),
    make_field("Waterfall_Source",     text()),     # which waterfall provider found it
    make_field("ZeroBounce_Attempted", checkbox()),
    make_field("ZeroBounce_Score",     number()),
    make_field("Enrichment_Source",    text()),
    make_field("Contact_ID_Created",   text()),     # Airtable record ID in Contacts table
    make_field("Priority_Score",       number()),   # composite score for queue ordering
    make_field("Retry_Count",          number()),
    make_field("Queued_At",        datetime_field()),
    make_field("Completed_At",     datetime_field()),
    make_field("Error_Notes",      text()),
])

# ══════════════════════════════════════════════════════════════════════
print(f"\n{'═'*60}")
print(f"  Tables: {ok_tables} ok, {err_tables} errors")
print(f"{'═'*60}\n")
print("Next: run scripts/index_knowledge_base.py to load OCL docs into Knowledge_Base")

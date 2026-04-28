"""
Add all missing fields to Airtable tables for ATLAS.

Adds:
  Contacts     → ICP_Lane, ICP_Priority, Title_Match, Lane_Score
  Accounts     → Current_Vendor, Renewal_Year, Renewal_Month,
                 Who_Owns_Training, Who_Owns_Budget, Vendor_Pain,
                 Renewal_Status, Outreach_Stage, Reply_Sentiment,
                 Asset_K, Website, Holding_Company
  Outreach_Log → CTA_Variant, CTA_Text, Framework, Reply_Received,
                 Bounced, Unsubscribed, Open_Count, Click_Count
  Email_Templates → Framework, Priority_Lane, CTA_Variant
  ICP_Personas    → Priority_Rank, Lane_Key
  Triggers        → Account_ID, Domain_Cert_ID

Run once:
    python3 scripts/setup_airtable_fields.py
"""

import os
import sys
import time
import requests
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

TOKEN   = os.getenv("AIRTABLE_TOKEN")
BASE_ID = os.getenv("AIRTABLE_BASE_ID", "appwlGCHBaRef70gO")

# Table IDs
TABLES = {
    "Accounts":        "tbljM7TE6NATsrSVc",
    "Contacts":        "tblkWlGGGaDhYEl3x",
    "ICP_Personas":    "tbl4r15ScLya08ycg",
    "Email_Templates": "tblGKi4aS7DkbCyCX",
    "Case_Studies":    "tblsuVt9AM31ID3Mi",
    "Triggers":        "tblktPtlYaDWCj0K7",
    "Outreach_Log":    "tblPyK6V7cqeo5rPs",
}

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}

created = 0
skipped = 0
errors  = 0


def add_field(table_name: str, field: dict):
    global created, skipped, errors
    # Airtable API requires checkbox fields to have icon+color options
    if field.get("type") == "checkbox" and "options" not in field:
        field = {**field, "options": {"icon": "check", "color": "greenBright"}}
    table_id = TABLES[table_name]
    url = f"https://api.airtable.com/v0/meta/bases/{BASE_ID}/tables/{table_id}/fields"
    resp = requests.post(url, json=field, headers=headers, timeout=15)
    if resp.ok:
        print(f"  ✓ {table_name}.{field['name']}")
        created += 1
    elif resp.status_code == 422 and "already exists" in resp.text:
        print(f"  · {table_name}.{field['name']} (exists)")
        skipped += 1
    else:
        print(f"  ✗ {table_name}.{field['name']}: {resp.status_code} {resp.text[:120]}")
        errors += 1
    time.sleep(0.3)


def select(choices: list[str]) -> dict:
    return {"choices": [{"name": c} for c in choices]}


# ════════════════════════════════════════════════════════════════════════
print("\n── Contacts ──────────────────────────────────────────────────────")

add_field("Contacts", {
    "name": "ICP_Lane",
    "type": "singleSelect",
    "options": select(["compliance", "hr", "l_and_d", "unknown"]),
})
add_field("Contacts", {
    "name": "ICP_Priority",
    "type": "number",
    "options": {"precision": 0},
})
add_field("Contacts", {
    "name": "Title_Match",
    "type": "singleLineText",
})
add_field("Contacts", {
    "name": "Lane_Score",
    "type": "number",
    "options": {"precision": 0},
    # 1=compliance, 2=hr, 3=l_and_d, 99=unknown — lower = higher priority
})
add_field("Contacts", {
    "name": "Enriched",
    "type": "checkbox",
})
add_field("Contacts", {
    "name": "Enrichment_Source",
    "type": "singleLineText",
})
add_field("Contacts", {
    "name": "Company",
    "type": "singleLineText",
})
add_field("Contacts", {
    "name": "Company_Domain",
    "type": "singleLineText",
})
add_field("Contacts", {
    "name": "Outreach_Count",
    "type": "number",
    "options": {"precision": 0},
})
add_field("Contacts", {
    "name": "Last_Contacted",
    "type": "date",
    "options": {"dateFormat": {"name": "iso"}},
})
add_field("Contacts", {
    "name": "Replied",
    "type": "checkbox",
})
add_field("Contacts", {
    "name": "Reply_Sentiment",
    "type": "singleSelect",
    "options": select(["interested", "not_interested", "wrong_person", "out_of_office", "meeting_booked", "needs_follow_up"]),
})
add_field("Contacts", {
    "name": "Do_Not_Contact",
    "type": "checkbox",
})
add_field("Contacts", {
    "name": "Notes",
    "type": "multilineText",
})

# ════════════════════════════════════════════════════════════════════════
print("\n── Accounts — Renewal Intelligence ──────────────────────────────")

add_field("Accounts", {
    "name": "Current_Vendor",
    "type": "singleLineText",
    # BAI, Skillsoft, SHRM, internal, unknown
})
add_field("Accounts", {
    "name": "Renewal_Year",
    "type": "number",
    "options": {"precision": 0},
})
add_field("Accounts", {
    "name": "Renewal_Month",
    "type": "number",
    "options": {"precision": 0},
})
add_field("Accounts", {
    "name": "Who_Owns_Training",
    "type": "singleLineText",
    # Contact name / title who owns the training decision
})
add_field("Accounts", {
    "name": "Who_Owns_Budget",
    "type": "singleLineText",
})
add_field("Accounts", {
    "name": "Vendor_Pain",
    "type": "multilineText",
    # Free-text pain with current vendor, captured from replies
})
add_field("Accounts", {
    "name": "Renewal_Status",
    "type": "singleSelect",
    "options": select(["unknown", "evaluating", "confirmed", "not_this_year", "re_engage", "do_not_contact"]),
})
add_field("Accounts", {
    "name": "Renewal_Notes",
    "type": "multilineText",
})

print("\n── Accounts — Outreach State ─────────────────────────────────────")

add_field("Accounts", {
    "name": "Outreach_Stage",
    "type": "singleSelect",
    "options": select(["not_started", "sequence_active", "replied", "meeting_booked", "disqualified", "re_engage_later"]),
})
add_field("Accounts", {
    "name": "Reply_Sentiment",
    "type": "singleSelect",
    "options": select(["interested", "not_interested", "wrong_person", "out_of_office", "objection", "meeting_booked"]),
})
add_field("Accounts", {
    "name": "Asset_K",
    "type": "number",
    "options": {"precision": 0},
})
add_field("Accounts", {
    "name": "Website",
    "type": "url",
})
add_field("Accounts", {
    "name": "Holding_Company",
    "type": "checkbox",
})
add_field("Accounts", {
    "name": "RECON_Brief",
    "type": "multilineText",
    # Claude-generated research brief — stored here for FORGE to read
})
add_field("Accounts", {
    "name": "Trigger_Score",
    "type": "number",
    "options": {"precision": 0},
})
add_field("Accounts", {
    "name": "ICP_Score",
    "type": "number",
    "options": {"precision": 0},
})

# ════════════════════════════════════════════════════════════════════════
print("\n── Outreach_Log — A/B Testing + Tracking ─────────────────────────")

add_field("Outreach_Log", {
    "name": "CTA_Variant",
    "type": "singleSelect",
    "options": select(["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]),
})
add_field("Outreach_Log", {
    "name": "CTA_Text",
    "type": "multilineText",
})
add_field("Outreach_Log", {
    "name": "Framework",
    "type": "singleSelect",
    "options": select(["5P", "KCPOV", "hybrid"]),
})
add_field("Outreach_Log", {
    "name": "Email_Sequence_Step",
    "type": "number",
    "options": {"precision": 0},
    # 1=first touch, 2=follow-up, etc.
})
add_field("Outreach_Log", {
    "name": "Reply_Received",
    "type": "checkbox",
})
add_field("Outreach_Log", {
    "name": "Bounced",
    "type": "checkbox",
})
add_field("Outreach_Log", {
    "name": "Unsubscribed",
    "type": "checkbox",
})
add_field("Outreach_Log", {
    "name": "Open_Count",
    "type": "number",
    "options": {"precision": 0},
})
add_field("Outreach_Log", {
    "name": "Click_Count",
    "type": "number",
    "options": {"precision": 0},
})
add_field("Outreach_Log", {
    "name": "Reply_Text",
    "type": "multilineText",
    # Raw reply — CORTEX classifies this
})
add_field("Outreach_Log", {
    "name": "CORTEX_Classification",
    "type": "singleSelect",
    "options": select(["interested", "not_interested", "wrong_person", "out_of_office", "objection", "meeting_booked", "unclassified"]),
})
add_field("Outreach_Log", {
    "name": "Renewal_Intel_Extracted",
    "type": "checkbox",
    # True when CORTEX pulled renewal info from this reply
})
add_field("Outreach_Log", {
    "name": "Human_Handoff",
    "type": "checkbox",
    # True when this reply was escalated to Nader/AE
})
add_field("Outreach_Log", {
    "name": "ICP_Lane",
    "type": "singleSelect",
    "options": select(["compliance", "hr", "l_and_d", "unknown"]),
})

# ════════════════════════════════════════════════════════════════════════
print("\n── Email_Templates — Framework Tags ──────────────────────────────")

add_field("Email_Templates", {
    "name": "Framework",
    "type": "singleSelect",
    "options": select(["5P", "KCPOV", "hybrid"]),
})
add_field("Email_Templates", {
    "name": "Priority_Lane",
    "type": "singleSelect",
    "options": select(["compliance", "hr", "l_and_d", "all"]),
})
add_field("Email_Templates", {
    "name": "CTA_Variant",
    "type": "singleSelect",
    "options": select(["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]),
})
add_field("Email_Templates", {
    "name": "Subject_Line",
    "type": "singleLineText",
})
add_field("Email_Templates", {
    "name": "Active",
    "type": "checkbox",
})
add_field("Email_Templates", {
    "name": "Reply_Rate_Pct",
    "type": "number",
    "options": {"precision": 1},
})
add_field("Email_Templates", {
    "name": "Sends_Count",
    "type": "number",
    "options": {"precision": 0},
})

# ════════════════════════════════════════════════════════════════════════
print("\n── ICP_Personas — Priority + Lane Key ────────────────────────────")

add_field("ICP_Personas", {
    "name": "Priority_Rank",
    "type": "number",
    "options": {"precision": 0},
    # 1=compliance (highest), 2=hr, 3=l_and_d
})
add_field("ICP_Personas", {
    "name": "Lane_Key",
    "type": "singleSelect",
    "options": select(["compliance", "hr", "l_and_d"]),
})
add_field("ICP_Personas", {
    "name": "Example_Titles",
    "type": "multilineText",
})
add_field("ICP_Personas", {
    "name": "Renewal_Question",
    "type": "multilineText",
    # The specific renewal-oriented CTA for this persona
})

# ════════════════════════════════════════════════════════════════════════
print("\n── Triggers — Extended Fields ────────────────────────────────────")

add_field("Triggers", {
    "name": "Cert_ID",
    "type": "singleLineText",
})
add_field("Triggers", {
    "name": "State",
    "type": "singleLineText",
})
add_field("Triggers", {
    "name": "Asset_M",
    "type": "number",
    "options": {"precision": 0},
})
add_field("Triggers", {
    "name": "Source",
    "type": "singleLineText",
    # serpapi, fdic_history, ncua, manual
})
add_field("Triggers", {
    "name": "Detected_At",
    "type": "dateTime",
    "options": {"dateFormat": {"name": "iso"}, "timeFormat": {"name": "24hour"}, "timeZone": "America/Chicago"},
})

# ════════════════════════════════════════════════════════════════════════
print("\n── Case_Studies — Extended ───────────────────────────────────────")

add_field("Case_Studies", {
    "name": "OCL_Product",
    "type": "singleLineText",
    # Live Private Classes, Online, Blended, etc.
})
add_field("Case_Studies", {
    "name": "Deal_Size",
    "type": "singleLineText",
})
add_field("Case_Studies", {
    "name": "Sales_Cycle_Days",
    "type": "number",
    "options": {"precision": 0},
})
add_field("Case_Studies", {
    "name": "Trigger_Type",
    "type": "singleLineText",
    # What trigger opened the deal
})

# ════════════════════════════════════════════════════════════════════════
print(f"\n{'═'*58}")
print(f"  Created: {created}   Skipped (exists): {skipped}   Errors: {errors}")
print(f"{'═'*58}\n")

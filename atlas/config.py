"""ATLAS configuration — loads from environment variables."""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Salesforce
    SF_CLIENT_ID = os.getenv("SF_CLIENT_ID")
    SF_CLIENT_SECRET = os.getenv("SF_CLIENT_SECRET")
    SF_USERNAME = os.getenv("SF_USERNAME")
    SF_PASSWORD = os.getenv("SF_PASSWORD")
    SF_SECURITY_TOKEN = os.getenv("SF_SECURITY_TOKEN", "")
    SF_DOMAIN = os.getenv("SF_DOMAIN", "login")

    # Outreach
    OUTREACH_CLIENT_ID = os.getenv("OUTREACH_CLIENT_ID")
    OUTREACH_CLIENT_SECRET = os.getenv("OUTREACH_CLIENT_SECRET")
    OUTREACH_ACCESS_TOKEN = os.getenv("OUTREACH_ACCESS_TOKEN")
    OUTREACH_REFRESH_TOKEN = os.getenv("OUTREACH_REFRESH_TOKEN")

    # 6sense
    SIXSENSE_API_KEY = os.getenv("SIXSENSE_API_KEY")

    # Claude
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

    # Microsoft Teams
    TEAMS_WEBHOOK_URL = os.getenv("TEAMS_WEBHOOK_URL")

    # Supabase (state store)
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

    # Instantly V2
    INSTANTLY_API_KEY = os.getenv("INSTANTLY_API_KEY")
    INSTANTLY_CAMPAIGN_ID = os.getenv("INSTANTLY_CAMPAIGN_ID")

    # ZeroBounce
    ZEROBOUNCE_API_KEY = os.getenv("ZEROBOUNCE_API_KEY")

    # Waterfall.io
    WATERFALL_API_KEY = os.getenv("WATERFALL_API_KEY")

    # SerpApi (job trigger signals)
    SERPAPI_KEY = os.getenv("SERPAPI_KEY")

    # Airtable (Agent Molly — agent data memory)
    AIRTABLE_TOKEN    = os.getenv("AIRTABLE_TOKEN")
    AIRTABLE_BASE_ID  = os.getenv("AIRTABLE_BASE_ID")
    AIRTABLE_ACCOUNTS_TABLE  = os.getenv("AIRTABLE_ACCOUNTS_TABLE",  "Accounts")
    AIRTABLE_CONTACTS_TABLE  = os.getenv("AIRTABLE_CONTACTS_TABLE",  "Contacts")
    AIRTABLE_PERSONAS_TABLE  = os.getenv("AIRTABLE_PERSONAS_TABLE",  "ICP_Personas")
    AIRTABLE_TEMPLATES_TABLE = os.getenv("AIRTABLE_TEMPLATES_TABLE", "Email_Templates")
    AIRTABLE_CASES_TABLE     = os.getenv("AIRTABLE_CASES_TABLE",     "Case_Studies")
    AIRTABLE_TRIGGERS_TABLE  = os.getenv("AIRTABLE_TRIGGERS_TABLE",  "Triggers")
    AIRTABLE_OUTREACH_TABLE  = os.getenv("AIRTABLE_OUTREACH_TABLE",  "Outreach_Log")

    # Agent behavior
    ATLAS_MODE = os.getenv("ATLAS_MODE", "review")  # "review" | "auto" | "shadow" | "paused"
    ATLAS_DAILY_LIMIT = int(os.getenv("ATLAS_DAILY_LIMIT", "25"))
    ATLAS_CONFIDENCE_THRESHOLD = float(os.getenv("ATLAS_CONFIDENCE_THRESHOLD", "0.85"))
    ATLAS_RUN_ON_START = os.getenv("ATLAS_RUN_ON_START", "false").lower() == "true"

    @classmethod
    def is_configured(cls, system: str) -> bool:
        checks = {
            "salesforce": bool(cls.SF_CLIENT_ID and cls.SF_USERNAME),
            "outreach": bool(cls.OUTREACH_ACCESS_TOKEN),
            "sixsense":  bool(cls.SIXSENSE_API_KEY),
            "claude":    bool(cls.ANTHROPIC_API_KEY),
            "teams":     bool(cls.TEAMS_WEBHOOK_URL),
            "supabase":  bool(cls.SUPABASE_URL and cls.SUPABASE_SERVICE_KEY),
            "instantly": bool(cls.INSTANTLY_API_KEY),
            "zerobounce":bool(cls.ZEROBOUNCE_API_KEY),
            "waterfall": bool(cls.WATERFALL_API_KEY),
            "serpapi":   bool(cls.SERPAPI_KEY),
            "airtable":  bool(cls.AIRTABLE_TOKEN and cls.AIRTABLE_BASE_ID),
        }
        return checks.get(system.lower(), False)

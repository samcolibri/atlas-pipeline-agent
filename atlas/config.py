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
            "sixsense": bool(cls.SIXSENSE_API_KEY),
            "claude": bool(cls.ANTHROPIC_API_KEY),
            "teams": bool(cls.TEAMS_WEBHOOK_URL),
        }
        return checks.get(system.lower(), False)

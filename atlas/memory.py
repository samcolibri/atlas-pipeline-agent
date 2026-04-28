"""
ATLAS Agent Memory — query layer over Airtable.

Every agent calls this BEFORE making any LLM call. This grounds the
agent in real, human-curated context (personas, case studies, templates)
and avoids hallucination of ICP details.

Usage:
    from atlas.memory import memory

    # Get the 3 buyer personas
    personas = memory.get_personas()

    # Get best template for a persona type
    tmpl = memory.get_template(persona="compliance")

    # Get matching case study for a bank
    case = memory.get_case_study(institution_type="bank")

    # Search accounts by state + status
    accounts = memory.accounts(state="IL", pipeline_status="new")

    # Log a trigger
    memory.log_trigger(domain="bylinebank.com", name="Byline Bank",
                       trigger_type="job_posting", detail="BSA Officer hiring")
"""

import logging
import os
from functools import lru_cache
from typing import Optional

log = logging.getLogger("atlas.memory")

_AIRTABLE_TOKEN = os.getenv("AIRTABLE_TOKEN")
_AIRTABLE_BASE  = os.getenv("AIRTABLE_BASE_ID", "appwlGCHBaRef70gO")


class AgentMemory:
    """High-level query interface to Airtable for ATLAS agents."""

    def __init__(self):
        from atlas.integrations.airtable_client import AirtableClient
        self._at = AirtableClient(token=_AIRTABLE_TOKEN, base_id=_AIRTABLE_BASE)
        self._tables = {
            "accounts":  os.getenv("AIRTABLE_ACCOUNTS_TABLE",  "Accounts"),
            "contacts":  os.getenv("AIRTABLE_CONTACTS_TABLE",  "Contacts"),
            "personas":  os.getenv("AIRTABLE_PERSONAS_TABLE",  "ICP_Personas"),
            "templates": os.getenv("AIRTABLE_TEMPLATES_TABLE", "Email_Templates"),
            "cases":     os.getenv("AIRTABLE_CASES_TABLE",     "Case_Studies"),
            "triggers":  os.getenv("AIRTABLE_TRIGGERS_TABLE",  "Triggers"),
            "outreach":  os.getenv("AIRTABLE_OUTREACH_TABLE",  "Outreach_Log"),
        }

    # ── ICP Context (agents read this before LLM calls) ───────────────

    def get_personas(self, active_only: bool = True) -> list[dict]:
        """Return all ICP personas. Cached — rarely changes."""
        records = self._at.all(self._tables["personas"])
        result = []
        for r in records:
            f = r.get("fields", {})
            if active_only and not f.get("Active", True):
                continue
            result.append(f)
        return result

    def get_persona(self, name: str) -> Optional[dict]:
        """Get a specific persona by name (e.g. 'compliance', 'hr', 'l_and_d')."""
        records = self._at.search(self._tables["personas"], persona_name__contains=name)
        return records[0].get("fields") if records else None

    def get_template(
        self,
        persona: Optional[str] = None,
        institution_type: Optional[str] = None,
    ) -> Optional[dict]:
        """Get best-match email template for a persona / institution type combo."""
        kwargs = {}
        if persona:
            kwargs["persona"] = persona
        if institution_type:
            kwargs["institution_type"] = institution_type
        records = self._at.search(self._tables["templates"], **kwargs)
        return records[0].get("fields") if records else None

    def get_all_templates(self) -> list[dict]:
        """Return all email templates as raw field dicts."""
        return [r.get("fields", {}) for r in self._at.all(self._tables["templates"])]

    # Maps FDIC institution_type → Case_Studies Institution_Type field values
    _CASE_TYPE_MAP = {
        "bank":         "community_bank",
        "savings":      "community_bank",
        "credit_union": "credit_union",
        "community_bank": "community_bank",
    }

    def get_case_study(
        self,
        institution_type: Optional[str] = None,
        company: Optional[str] = None,
    ) -> Optional[dict]:
        """Get a relevant case study to use in outreach."""
        kwargs = {}
        if institution_type:
            mapped = self._CASE_TYPE_MAP.get(institution_type.lower(), institution_type)
            kwargs["institution_type"] = mapped
        if company:
            kwargs["company__contains"] = company
        records = self._at.search(self._tables["cases"], **kwargs)
        return records[0].get("fields") if records else None

    def get_all_case_studies(self) -> list[dict]:
        return [r.get("fields", {}) for r in self._at.all(self._tables["cases"])]

    # ── Accounts ──────────────────────────────────────────────────────

    def accounts(self, limit: int = 100, **kwargs) -> list[dict]:
        """
        Search accounts by any field combo.
        Examples:
            memory.accounts(state="IL", pipeline_status="new")
            memory.accounts(pipeline_status="enriched", asset_m__gt=500)
        """
        records = self._at.search(self._tables["accounts"], **kwargs)
        return [r.get("fields", {}) for r in records[:limit]]

    def get_account_by_domain(self, domain: str) -> Optional[dict]:
        records = self._at.search(self._tables["accounts"], domain=domain)
        return records[0].get("fields") if records else None

    def update_account(self, record_id: str, **fields) -> bool:
        return self._at.update(self._tables["accounts"], record_id, fields)

    # ── Contacts ──────────────────────────────────────────────────────

    def contacts(self, **kwargs) -> list[dict]:
        records = self._at.search(self._tables["contacts"], **kwargs)
        return [r.get("fields", {}) for r in records]

    def upsert_contact(self, contact: dict) -> dict:
        result = self._at.upsert(
            self._tables["contacts"],
            [contact],
            match_fields=["Email"],
            show_progress=False,
        )
        return result

    # ── Triggers ──────────────────────────────────────────────────────

    def log_trigger(
        self,
        domain: str,
        name: str,
        trigger_type: str,
        detail: str,
        url: str = "",
        score: int = 1,
    ):
        """Record a trigger signal (job posting, merger, asset growth, etc.)."""
        self._at.insert(self._tables["triggers"], {
            "Account_Domain": domain,
            "Account_Name":   name,
            "Trigger_Type":   trigger_type,
            "Signal_Detail":  detail,
            "Signal_URL":     url,
            "Score":          score,
            "Processed":      False,
        })
        log.info(f"[MEMORY] Trigger logged: {trigger_type} @ {domain}")

    def get_unprocessed_triggers(self, limit: int = 50) -> list[dict]:
        records = self._at.search(self._tables["triggers"], processed=False)
        return [r.get("fields", {}) for r in records[:limit]]

    # ── Outreach log ──────────────────────────────────────────────────

    def log_outreach(self, record: dict):
        """Log an outreach attempt to Airtable for visibility."""
        self._at.insert(self._tables["outreach"], record)

    def get_outreach_log(self, domain: str) -> list[dict]:
        records = self._at.search(self._tables["outreach"], account_domain=domain)
        return [r.get("fields", {}) for r in records]

    # ── Context bundle (main agent entry point) ───────────────────────

    def build_context(self, institution_type: str = "bank") -> dict:
        """
        Returns a pre-loaded context dict for agent prompt assembly.
        Call this ONCE per account, inject into prompt, then call LLM.
        """
        personas     = self.get_personas()
        templates    = self.get_all_templates()
        case_studies = self.get_all_case_studies()

        return {
            "personas":     personas,
            "templates":    templates,
            "case_studies": [
                c for c in case_studies
                if not institution_type
                or c.get("Institution_Type", "").lower() == institution_type.lower()
            ],
        }


# Singleton — import and use directly
memory = AgentMemory()

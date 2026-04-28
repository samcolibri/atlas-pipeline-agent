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
            "accounts":         os.getenv("AIRTABLE_ACCOUNTS_TABLE",    "Accounts"),
            "contacts":         os.getenv("AIRTABLE_CONTACTS_TABLE",    "Contacts"),
            "personas":         os.getenv("AIRTABLE_PERSONAS_TABLE",    "ICP_Personas"),
            "templates":        os.getenv("AIRTABLE_TEMPLATES_TABLE",   "Email_Templates"),
            "cases":            os.getenv("AIRTABLE_CASES_TABLE",       "Case_Studies"),
            "triggers":         os.getenv("AIRTABLE_TRIGGERS_TABLE",    "Triggers"),
            "outreach":         os.getenv("AIRTABLE_OUTREACH_TABLE",    "Outreach_Log"),
            "knowledge":        "Knowledge_Base",
            "ab_results":       "AB_Results",
            "learned_signals":  "Learned_Signals",
            "enrichment_queue": "Enrichment_Queue",
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

    # ── Knowledge Base ────────────────────────────────────────────────

    def search_knowledge(
        self,
        doc_type: Optional[str] = None,
        icp_lane: Optional[str] = None,
        relevant_to: Optional[str] = None,
        active_only: bool = True,
        limit: int = 10,
    ) -> list[dict]:
        """
        Search indexed documents in Knowledge_Base.
        Agents call this to pull frameworks, personas, objection handlers
        before building a prompt.

        Examples:
            memory.search_knowledge(doc_type="skill_packet", icp_lane="compliance")
            memory.search_knowledge(relevant_to="FORGE")
            memory.search_knowledge(doc_type="objection_handler")
        """
        kwargs = {}
        if doc_type:
            kwargs["doc_type"] = doc_type
        if icp_lane:
            kwargs["icp_lane"] = icp_lane
        if relevant_to:
            kwargs["relevant_to"] = relevant_to
        if active_only:
            kwargs["active"] = True
        records = self._at.search(self._tables["knowledge"], **kwargs)
        return [r.get("fields", {}) for r in records[:limit]]

    def get_knowledge_for_agent(self, agent: str) -> list[dict]:
        """Return all KB docs relevant to a specific agent (RECON, FORGE, CORTEX)."""
        all_docs  = self.search_knowledge(relevant_to=agent, limit=20)
        universal = self.search_knowledge(relevant_to="all_agents", limit=10)
        seen = set()
        result = []
        for doc in all_docs + universal:
            title = doc.get("Title", "")
            if title not in seen:
                seen.add(title)
                result.append(doc)
        return result

    def get_skill_packets(self, icp_lane: Optional[str] = None) -> list[dict]:
        """Return 5P and KCPOV skill packet docs for FORGE to use in email generation."""
        return self.search_knowledge(doc_type="skill_packet", icp_lane=icp_lane)

    def get_frameworks(self) -> list[dict]:
        """Return StoryBrand, 5P, KCPOV framework docs."""
        return self.search_knowledge(doc_type="framework")

    def get_objection_handlers(self) -> list[dict]:
        """Return objection handler docs for CORTEX reply classification."""
        return self.search_knowledge(doc_type="objection_handler")

    def queue_for_enrichment(
        self,
        domain: str,
        name: str,
        cert_id: str = "",
        state: str = "",
        asset_m: int = 0,
        icp_lane: str = "compliance",
        title_hint: str = "",
    ):
        """Add an account to the Enrichment_Queue for Waterfall + ZeroBounce processing."""
        from datetime import datetime, timezone
        record = {
            "Account_Name":   name,
            "Account_Domain": domain,
            "Cert_ID":        cert_id,
            "State":          state,
            "Asset_M":        asset_m,
            "ICP_Lane":       icp_lane,
            "Lane_Priority":  {"compliance": 1, "hr": 2, "l_and_d": 3}.get(icp_lane, 3),
            "Title_Hint":     title_hint,
            "Status":         "pending",
            "Queued_At":      datetime.now(timezone.utc).isoformat(),
            "Priority_Score": asset_m // 100,  # larger banks = higher priority
            "Retry_Count":    0,
        }
        self._at.insert(self._tables["enrichment_queue"], record)

    def get_enrichment_queue(self, limit: int = 50) -> list[dict]:
        """Return pending enrichment jobs ordered by priority."""
        records = self._at.search(self._tables["enrichment_queue"], status="pending")
        fields  = [r.get("fields", {}) for r in records]
        return sorted(fields, key=lambda x: x.get("Priority_Score", 0), reverse=True)[:limit]

    # ── A/B Results ───────────────────────────────────────────────────

    def get_winning_variant(self, icp_lane: str, institution_type: str = "bank") -> Optional[dict]:
        """Return the current best-performing variant for a lane + institution type."""
        records = self._at.search(
            self._tables["ab_results"],
            icp_lane=icp_lane,
            institution_type=institution_type,
            is_winner=True,
        )
        if records:
            return records[0].get("fields")
        # No winner yet — return variant A as default
        records = self._at.search(
            self._tables["ab_results"],
            icp_lane=icp_lane,
            institution_type=institution_type,
            cta_variant="A",
        )
        return records[0].get("fields") if records else None

    def record_send(self, variant_key: str):
        """Increment sends count for a variant after an email goes out."""
        records = self._at.search(self._tables["ab_results"], variant_key=variant_key)
        if records:
            rid   = records[0]["id"]
            count = records[0].get("fields", {}).get("Sends_Count", 0) + 1
            self._at.update(self._tables["ab_results"], rid, {"Sends_Count": count})

    def record_reply(self, variant_key: str, outcome: str = "replied"):
        """Increment reply/interest/meeting count after CORTEX classifies a reply."""
        records = self._at.search(self._tables["ab_results"], variant_key=variant_key)
        if not records:
            return
        rid    = records[0]["id"]
        fields = records[0].get("fields", {})
        update = {"Replies_Count": fields.get("Replies_Count", 0) + 1}
        if outcome == "interested":
            update["Interested_Count"] = fields.get("Interested_Count", 0) + 1
        if outcome == "meeting_booked":
            update["Meetings_Booked"] = fields.get("Meetings_Booked", 0) + 1
        self._at.update(self._tables["ab_results"], rid, update)

    # ── Learned Signals ───────────────────────────────────────────────

    def save_signal(
        self,
        domain: str,
        name: str,
        signal_type: str,
        raw_text: str,
        extracted_value: str = "",
        confidence: float = 0.8,
        **kwargs,
    ):
        """CORTEX calls this after classifying a reply — builds intelligence over time."""
        from datetime import datetime, timezone
        record = {
            "Account_Domain":  domain,
            "Account_Name":    name,
            "Signal_Type":     signal_type,
            "Raw_Signal_Text": raw_text,
            "Extracted_Value": extracted_value,
            "Confidence":      int(confidence * 100),
            "Action_Taken":    "none",
            "Detected_At":     datetime.now(timezone.utc).isoformat(),
            **kwargs,
        }
        self._at.insert(self._tables["learned_signals"], record)
        log.info(f"[MEMORY] Signal saved: {signal_type} @ {domain} ({extracted_value})")

    def get_signals_for_account(self, domain: str) -> list[dict]:
        records = self._at.search(self._tables["learned_signals"], account_domain=domain)
        return [r.get("fields", {}) for r in records]

    # ── Context bundle (main agent entry point) ───────────────────────

    def build_context(self, institution_type: str = "bank", icp_lane: str = "compliance") -> dict:
        """
        Returns a pre-loaded context dict for agent prompt assembly.
        Call this ONCE per account, inject into prompt, then call LLM.
        Agents never hardcode ICP knowledge — they read it here.
        """
        personas     = self.get_personas()
        templates    = self.get_all_templates()
        case_studies = self.get_all_case_studies()
        skill_packets = self.get_skill_packets(icp_lane=icp_lane)
        frameworks    = self.get_frameworks()
        kb_docs       = self.get_knowledge_for_agent("RECON")

        return {
            "personas":      personas,
            "templates":     templates,
            "case_studies":  [
                c for c in case_studies
                if not institution_type
                or c.get("Institution_Type", "").lower() in (institution_type.lower(), "community_bank")
            ],
            "skill_packets": skill_packets,
            "frameworks":    frameworks,
            "kb_docs":       kb_docs,
            "icp_lane":      icp_lane,
        }


# Singleton — import and use directly
memory = AgentMemory()

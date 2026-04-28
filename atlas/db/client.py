"""
Supabase/Postgres state store client for ATLAS.

All pipeline state lives here — never inside Pipedream or the LLM.
Supabase auto-generates REST APIs from the schema, so every field
is queryable from Pipedream workflows without custom endpoints.

Usage:
    from atlas.db.client import db
    db.upsert_account(institution)
    db.is_suppressed("domain.com")
    db.mark_sent(contact_id, attempt_id)
"""

import logging
import os
from typing import Optional
from uuid import UUID

import requests

log = logging.getLogger("atlas.db")


class AtlasDB:

    def __init__(self, url: str, key: str):
        self.url = url.rstrip("/")
        self.headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

    # ── Accounts ──────────────────────────────────────────────────────

    def upsert_account(self, institution) -> Optional[dict]:
        from atlas.integrations.fdic import Institution
        payload = {
            "cert_id":          institution.cert_id,
            "source":           institution.source,
            "name":             institution.name,
            "city":             institution.city,
            "state":            institution.state,
            "zip_code":         institution.zip_code,
            "address":          institution.address,
            "asset_k":          institution.asset_k,
            "website":          institution.website,
            "domain":           institution.domain,
            "phone":            institution.phone,
            "established":      institution.established,
            "institution_type": institution.institution_type,
            "status":           "new",
        }
        resp = self._post(
            "/accounts",
            payload,
            headers={"Prefer": "resolution=merge-duplicates,return=representation"},
        )
        if resp and isinstance(resp, list):
            return resp[0]
        return None

    def get_account(self, cert_id: str, source: str) -> Optional[dict]:
        resp = self._get("/accounts", params={
            "cert_id": f"eq.{cert_id}",
            "source":  f"eq.{source}",
            "limit":   "1",
        })
        return resp[0] if resp else None

    def update_account_status(self, account_id: str, status: str, **kwargs):
        payload = {"status": status, **kwargs}
        self._patch(f"/accounts?id=eq.{account_id}", payload)

    def get_accounts_by_status(self, status: str, limit: int = 100) -> list[dict]:
        return self._get("/accounts", params={
            "status":      f"eq.{status}",
            "suppressed":  "eq.false",
            "limit":       str(limit),
            "order":       "asset_k.desc",
        }) or []

    # ── Contacts ──────────────────────────────────────────────────────

    def upsert_contact(self, contact: dict) -> Optional[dict]:
        resp = self._post(
            "/contacts",
            contact,
            headers={"Prefer": "resolution=merge-duplicates,return=representation"},
        )
        return resp[0] if isinstance(resp, list) and resp else None

    def get_contact_by_email(self, email: str) -> Optional[dict]:
        resp = self._get("/contacts", params={"email": f"eq.{email}", "limit": "1"})
        return resp[0] if resp else None

    def update_contact(self, contact_id: str, **kwargs):
        self._patch(f"/contacts?id=eq.{contact_id}", kwargs)

    # ── Suppression ───────────────────────────────────────────────────

    def is_suppressed(self, value: str) -> bool:
        resp = self._get("/suppression_list", params={
            "value": f"eq.{value}",
            "limit": "1",
        })
        return bool(resp)

    def suppress(self, scope: str, value: str, reason: str, source: str = "atlas"):
        payload = {"scope": scope, "value": value, "reason": reason, "source": source}
        self._post(
            "/suppression_list",
            payload,
            headers={"Prefer": "resolution=ignore-duplicates,return=minimal"},
        )
        log.info(f"[DB] Suppressed {scope}:{value} ({reason})")

    def bulk_suppress_from_salesforce(self, domains: list[str], reason: str):
        records = [
            {"scope": "domain", "value": d, "reason": reason, "source": "salesforce"}
            for d in domains
        ]
        if records:
            self._post(
                "/suppression_list",
                records,
                headers={"Prefer": "resolution=ignore-duplicates,return=minimal"},
            )
            log.info(f"[DB] Suppressed {len(records)} domains from Salesforce")

    # ── Outreach ──────────────────────────────────────────────────────

    def create_attempt(self, contact_id: str, account_id: str, **kwargs) -> Optional[dict]:
        payload = {"contact_id": contact_id, "account_id": account_id, **kwargs}
        resp = self._post("/outreach_attempts", payload)
        return resp[0] if isinstance(resp, list) and resp else None

    def mark_sent(self, attempt_id: str, instantly_lead_id: str = None):
        from datetime import datetime, timezone
        payload = {
            "status": "sent",
            "sent_at": datetime.now(timezone.utc).isoformat(),
        }
        if instantly_lead_id:
            payload["instantly_lead_id"] = instantly_lead_id
        self._patch(f"/outreach_attempts?id=eq.{attempt_id}", payload)

    # ── Replies ───────────────────────────────────────────────────────

    def save_reply(self, reply: dict) -> Optional[dict]:
        resp = self._post("/replies", reply)
        return resp[0] if isinstance(resp, list) and resp else None

    # ── Triggers ──────────────────────────────────────────────────────

    def save_trigger(self, account_id: str, trigger_type: str, detail: str, score: int = 1):
        payload = {
            "account_id":   account_id,
            "trigger_type": trigger_type,
            "signal_detail": detail,
            "score":        score,
        }
        self._post("/triggers", payload)
        self._patch(
            f"/accounts?id=eq.{account_id}",
            {"has_trigger": True, "trigger_type": trigger_type, "trigger_detail": detail},
        )

    def get_unprocessed_triggers(self, limit: int = 50) -> list[dict]:
        return self._get("/triggers", params={
            "processed": "eq.false",
            "order":     "score.desc",
            "limit":     str(limit),
        }) or []

    # ── Audit ─────────────────────────────────────────────────────────

    def log_action(self, entity_type: str, entity_id: str, action: str, detail: dict = None, mode: str = None):
        import json
        payload = {
            "entity_type": entity_type,
            "entity_id":   entity_id,
            "action":      action,
            "detail":      json.dumps(detail or {}),
            "atlas_mode":  mode,
        }
        self._post("/audit_log", payload, headers={"Prefer": "return=minimal"})

    # ── Stats ─────────────────────────────────────────────────────────

    def pipeline_stats(self) -> dict:
        total    = self._count("/accounts")
        enriched = self._count("/accounts", "status=eq.enriched")
        queued   = self._count("/accounts", "status=eq.queued")
        sent     = self._count("/outreach_attempts", "status=eq.sent")
        replied  = self._count("/replies")
        booked   = self._count("/replies", "meeting_booked=eq.true")
        return {
            "accounts_total":   total,
            "accounts_enriched":enriched,
            "accounts_queued":  queued,
            "emails_sent":      sent,
            "replies":          replied,
            "meetings_booked":  booked,
        }

    # ── HTTP helpers ──────────────────────────────────────────────────

    def _post(self, path: str, payload, headers: dict = None) -> Optional[list]:
        h = {**self.headers, **(headers or {})}
        resp = requests.post(f"{self.url}/rest/v1{path}", json=payload, headers=h, timeout=15)
        if not resp.ok:
            log.error(f"[DB] POST {path} → {resp.status_code}: {resp.text[:200]}")
        return resp.json() if resp.ok and resp.content else None

    def _get(self, path: str, params: dict = None) -> Optional[list]:
        resp = requests.get(f"{self.url}/rest/v1{path}", params=params, headers=self.headers, timeout=15)
        return resp.json() if resp.ok else None

    def _patch(self, path: str, payload: dict):
        resp = requests.patch(
            f"{self.url}/rest/v1{path}", json=payload, headers=self.headers, timeout=15
        )
        if not resp.ok:
            log.error(f"[DB] PATCH {path} → {resp.status_code}: {resp.text[:200]}")

    def _count(self, path: str, filter_str: str = "") -> int:
        url = f"{self.url}/rest/v1{path}"
        if filter_str:
            url += f"?{filter_str}"
        h = {**self.headers, "Prefer": "count=exact", "Range": "0-0"}
        resp = requests.get(url, headers=h, timeout=10)
        cr = resp.headers.get("Content-Range", "0/0")
        try:
            return int(cr.split("/")[-1])
        except Exception:
            return 0


def get_db() -> AtlasDB:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env")
    return AtlasDB(url, key)


db: AtlasDB = None  # initialized lazily via get_db()

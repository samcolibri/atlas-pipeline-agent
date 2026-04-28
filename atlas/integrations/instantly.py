"""
Instantly V2 API client for ATLAS.

Handles: lead management, campaign enrollment, reply event parsing.

IMPORTANT: Do NOT rely on a field named "reply_intent" in webhook payloads.
Instantly fires named event types — route on event type + raw reply text,
then let Claude classify intent. The field names in event payloads are:
  reply_received, lead_interested, lead_not_interested,
  lead_wrong_person, lead_out_of_office, lead_meeting_booked

API docs: https://developer.instantly.ai
Webhook docs: https://instantly.ai/blog/api-webhooks-custom-integrations-for-outreach/
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

import requests

log = logging.getLogger("atlas.instantly")

BASE_URL = "https://api.instantly.ai/api/v2"


class ReplyEvent(str, Enum):
    REPLY_RECEIVED     = "reply_received"
    LEAD_INTERESTED    = "lead_interested"
    LEAD_NOT_INTERESTED= "lead_not_interested"
    LEAD_WRONG_PERSON  = "lead_wrong_person"
    LEAD_OUT_OF_OFFICE = "lead_out_of_office"
    LEAD_MEETING_BOOKED= "lead_meeting_booked"
    EMAIL_BOUNCED      = "email_bounced"
    EMAIL_UNSUBSCRIBED = "email_unsubscribed"


@dataclass
class Lead:
    email: str
    first_name: str
    last_name: str
    company_name: str
    personalization: str    # the custom opening line per lead
    website: str = ""
    phone: str = ""
    custom_variables: dict = None


@dataclass
class ReplyWebhook:
    event_type: ReplyEvent
    lead_email: str
    campaign_id: str
    reply_text: str
    timestamp: str
    raw: dict

    @property
    def needs_classification(self) -> bool:
        return self.event_type == ReplyEvent.REPLY_RECEIVED

    @property
    def is_auto_classified_positive(self) -> bool:
        return self.event_type == ReplyEvent.LEAD_INTERESTED

    @property
    def is_auto_classified_negative(self) -> bool:
        return self.event_type in (
            ReplyEvent.LEAD_NOT_INTERESTED,
            ReplyEvent.EMAIL_UNSUBSCRIBED,
        )


class InstantlyClient:

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        })

    # ── Lead management ──────────────────────────────────────────────

    def add_lead(self, campaign_id: str, lead: Lead) -> dict:
        payload = {
            "campaign_id": campaign_id,
            "skip_if_in_workspace": True,
            "leads": [self._lead_to_dict(lead)],
        }
        return self._post("/leads", payload)

    def add_leads_batch(self, campaign_id: str, leads: list[Lead]) -> dict:
        if not leads:
            return {}
        payload = {
            "campaign_id": campaign_id,
            "skip_if_in_workspace": True,
            "leads": [self._lead_to_dict(l) for l in leads],
        }
        log.info(f"[Instantly] Adding {len(leads)} leads to campaign {campaign_id}")
        return self._post("/leads", payload)

    def get_lead(self, email: str) -> Optional[dict]:
        resp = self._get("/leads", params={"email": email})
        items = resp.get("items", [])
        return items[0] if items else None

    def remove_lead(self, email: str) -> dict:
        return self._delete(f"/leads/{email}")

    # ── Campaign management ──────────────────────────────────────────

    def list_campaigns(self) -> list[dict]:
        resp = self._get("/campaigns")
        return resp.get("items", [])

    def get_campaign(self, campaign_id: str) -> dict:
        return self._get(f"/campaigns/{campaign_id}")

    # ── Reply handling ───────────────────────────────────────────────

    def parse_webhook(self, payload: dict) -> Optional[ReplyWebhook]:
        """
        Parse an incoming Instantly webhook payload into a typed ReplyWebhook.
        Route on event_type — do NOT assume a 'reply_intent' field exists.
        """
        event_type_raw = payload.get("event_type", "")
        try:
            event_type = ReplyEvent(event_type_raw)
        except ValueError:
            log.warning(f"[Instantly] Unknown event type: {event_type_raw}")
            return None

        return ReplyWebhook(
            event_type=event_type,
            lead_email=payload.get("lead_email", payload.get("email", "")),
            campaign_id=payload.get("campaign_id", ""),
            reply_text=payload.get("reply_text", payload.get("text", "")),
            timestamp=payload.get("timestamp", ""),
            raw=payload,
        )

    def list_replies(self, campaign_id: Optional[str] = None) -> list[dict]:
        params = {}
        if campaign_id:
            params["campaign_id"] = campaign_id
        resp = self._get("/replies", params=params)
        return resp.get("items", [])

    # ── Analytics ────────────────────────────────────────────────────

    def campaign_analytics(self, campaign_id: str) -> dict:
        return self._get(f"/campaigns/{campaign_id}/analytics")

    # ── HTTP helpers ─────────────────────────────────────────────────

    def _post(self, path: str, payload: dict) -> dict:
        resp = self.session.post(f"{BASE_URL}{path}", json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def _get(self, path: str, params: dict = None) -> dict:
        resp = self.session.get(f"{BASE_URL}{path}", params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def _delete(self, path: str) -> dict:
        resp = self.session.delete(f"{BASE_URL}{path}", timeout=30)
        resp.raise_for_status()
        return resp.json() if resp.content else {}

    def _lead_to_dict(self, lead: Lead) -> dict:
        d = {
            "email": lead.email,
            "first_name": lead.first_name,
            "last_name": lead.last_name,
            "company_name": lead.company_name,
            "personalization": lead.personalization,
        }
        if lead.website:
            d["website"] = lead.website
        if lead.phone:
            d["phone"] = lead.phone
        if lead.custom_variables:
            d.update(lead.custom_variables)
        return d

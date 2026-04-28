"""
ZeroBounce email validation API.

Validates every email before it enters the send queue.
Invalid or risky emails never reach Instantly.

API docs: https://www.zerobounce.net/docs/
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

import requests

log = logging.getLogger("atlas.zerobounce")

VALIDATE_URL = "https://api.zerobounce.net/v2/validate"
BATCH_URL    = "https://bulkapi.zerobounce.net/v2/validatebatch"


class EmailStatus(str, Enum):
    VALID        = "valid"
    INVALID      = "invalid"
    CATCH_ALL    = "catch-all"      # domain accepts all — risky, use cautiously
    UNKNOWN      = "unknown"
    SPAMTRAP     = "spamtrap"
    ABUSE        = "abuse"
    DO_NOT_MAIL  = "do_not_mail"


# Statuses safe to send to
SENDABLE = {EmailStatus.VALID}

# Catch-all is borderline — include it but mark as risky
SENDABLE_WITH_RISK = {EmailStatus.VALID, EmailStatus.CATCH_ALL}


@dataclass
class ValidationResult:
    email: str
    status: EmailStatus
    sub_status: str         # e.g. "disposable", "role_based", "possible_typo"
    free_email: bool
    did_you_mean: Optional[str]
    is_sendable: bool
    is_risky: bool

    def display(self) -> str:
        risk = " [RISKY]" if self.risky else ""
        suggest = f" → did you mean {self.did_you_mean}?" if self.did_you_mean else ""
        return f"{self.email}: {self.status.value}{risk}{suggest}"


class ZeroBounceClient:

    def __init__(self, api_key: str):
        self.api_key = api_key

    def validate(self, email: str) -> ValidationResult:
        resp = requests.get(
            VALIDATE_URL,
            params={"api_key": self.api_key, "email": email},
            timeout=10,
        )
        resp.raise_for_status()
        return self._parse(resp.json())

    def validate_batch(self, emails: list[str]) -> list[ValidationResult]:
        if not emails:
            return []

        payload = {
            "api_key": self.api_key,
            "email_batch": [{"email_address": e} for e in emails],
        }
        resp = requests.post(BATCH_URL, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        results = []
        for item in data.get("email_batch", []):
            results.append(self._parse(item))
        return results

    def filter_sendable(
        self, emails: list[str], allow_catch_all: bool = False
    ) -> tuple[list[str], list[str]]:
        """Returns (sendable_emails, rejected_emails)."""
        results = self.validate_batch(emails)
        allowed = SENDABLE_WITH_RISK if allow_catch_all else SENDABLE
        sendable = [r.email for r in results if r.status in allowed]
        rejected = [r.email for r in results if r.status not in allowed]
        log.info(f"[ZB] {len(sendable)} sendable, {len(rejected)} rejected from {len(emails)}")
        return sendable, rejected

    def _parse(self, data: dict) -> ValidationResult:
        raw_status = data.get("status", "unknown").lower().replace(" ", "_")
        try:
            status = EmailStatus(raw_status)
        except ValueError:
            status = EmailStatus.UNKNOWN

        is_sendable = status in SENDABLE
        is_risky = status == EmailStatus.CATCH_ALL

        return ValidationResult(
            email=data.get("address", ""),
            status=status,
            sub_status=data.get("sub_status", ""),
            free_email=data.get("free_email", False),
            did_you_mean=data.get("did_you_mean") or None,
            is_sendable=is_sendable,
            is_risky=is_risky,
        )

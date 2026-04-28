"""
Airtable client for ATLAS — agent's data memory layer.

All ICP context (accounts, contacts, personas, templates, case studies,
triggers) lives here so agents can search BEFORE calling any LLM.

Airtable is used for:
  - Readable/queryable context the agent can scan
  - Human-editable master data (templates, personas, case studies)
  - Outreach log + trigger ledger

Supabase is used for:
  - Machine state (statuses, timestamps, foreign keys)
  - High-frequency writes (enrichment runs, attempt tracking)

Usage:
    from atlas.integrations.airtable_client import AirtableClient
    at = AirtableClient()
    # Search accounts
    rows = at.search("Accounts", state="IL", pipeline_status="new")
    # Get all ICP personas
    personas = at.all("ICP_Personas")
    # Get best-match template for a persona
    tmpl = at.search("Email_Templates", persona_type="compliance")
"""

import logging
import os
import time
from typing import Optional

import requests

log = logging.getLogger("atlas.airtable")

AIRTABLE_API = "https://api.airtable.com/v0"
MAX_RECORDS_PER_BATCH = 10     # Airtable hard limit
RATE_LIMIT_SLEEP = 0.25        # 4 req/sec (limit is 5/sec, leave headroom)


class AirtableClient:

    def __init__(
        self,
        token: Optional[str] = None,
        base_id: Optional[str] = None,
    ):
        self.token = token or os.getenv("AIRTABLE_TOKEN")
        self.base_id = base_id or os.getenv("AIRTABLE_BASE_ID")
        if not self.token or not self.base_id:
            raise RuntimeError(
                "AIRTABLE_TOKEN and AIRTABLE_BASE_ID must be set in .env"
            )
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    # ── Query methods ──────────────────────────────────────────────────

    def all(self, table: str, max_records: int = 1000) -> list[dict]:
        """Return all records from a table (up to max_records)."""
        return self._list(table, max_records=max_records)

    def search(self, table: str, **kwargs) -> list[dict]:
        """
        Filter records by field values. kwargs map directly to Airtable field
        names (case-insensitive, underscores become spaces optionally).

        Examples:
            at.search("Accounts", state="IL")
            at.search("Accounts", pipeline_status="new", institution_type="bank")
            at.search("Email_Templates", persona_type="compliance")
        """
        if not kwargs:
            return self.all(table)
        formula = self._build_formula(kwargs)
        return self._list(table, formula=formula)

    def get(self, table: str, record_id: str) -> Optional[dict]:
        """Fetch a single record by Airtable record ID."""
        url = f"{AIRTABLE_API}/{self.base_id}/{table}/{record_id}"
        resp = requests.get(url, headers=self.headers, timeout=15)
        if resp.ok:
            return resp.json()
        log.error(f"[AT] GET {table}/{record_id} → {resp.status_code}: {resp.text[:200]}")
        return None

    def find_one(self, table: str, **kwargs) -> Optional[dict]:
        """Return first matching record, or None."""
        results = self.search(table, **kwargs)
        return results[0] if results else None

    # ── Write methods ──────────────────────────────────────────────────

    def insert(self, table: str, fields: dict) -> Optional[dict]:
        """Insert a single record."""
        url = f"{AIRTABLE_API}/{self.base_id}/{table}"
        resp = requests.post(url, json={"fields": fields}, headers=self.headers, timeout=15)
        if resp.ok:
            return resp.json()
        log.error(f"[AT] INSERT {table} → {resp.status_code}: {resp.text[:200]}")
        return None

    def batch_insert(
        self,
        table: str,
        records: list[dict],
        show_progress: bool = True,
    ) -> int:
        """
        Insert many records efficiently. Returns count of successfully inserted.
        Respects Airtable's 10-record-per-batch and 5-req/sec limits.
        """
        inserted = 0
        total = len(records)
        url = f"{AIRTABLE_API}/{self.base_id}/{table}"

        for i in range(0, total, MAX_RECORDS_PER_BATCH):
            chunk = records[i : i + MAX_RECORDS_PER_BATCH]
            payload = {"records": [{"fields": r} for r in chunk]}
            resp = requests.post(url, json=payload, headers=self.headers, timeout=30)

            if resp.ok:
                inserted += len(chunk)
            else:
                log.error(
                    f"[AT] BATCH {i}–{i+len(chunk)} → "
                    f"{resp.status_code}: {resp.text[:200]}"
                )

            if show_progress and (i % 100 == 0 or i + MAX_RECORDS_PER_BATCH >= total):
                pct = min(100, int((i + len(chunk)) / total * 100))
                print(f"  [{pct:3d}%] {inserted:,}/{total:,} inserted", end="\r")

            time.sleep(RATE_LIMIT_SLEEP)

        if show_progress:
            print(f"  [100%] {inserted:,}/{total:,} inserted    ")
        return inserted

    def upsert(
        self,
        table: str,
        records: list[dict],
        match_fields: list[str],
        show_progress: bool = True,
    ) -> dict:
        """
        Upsert records using Airtable's native merge API.
        match_fields: field name(s) to match on for dedup.
        Returns {"created": N, "updated": N}.
        """
        created = updated = 0
        total = len(records)
        url = f"{AIRTABLE_API}/{self.base_id}/{table}"

        for i in range(0, total, MAX_RECORDS_PER_BATCH):
            chunk = records[i : i + MAX_RECORDS_PER_BATCH]
            payload = {
                "records": [{"fields": r} for r in chunk],
                "performUpsert": {"fieldsToMergeOn": match_fields},
            }
            resp = requests.patch(url, json=payload, headers=self.headers, timeout=30)

            if resp.ok:
                data = resp.json()
                created += len(data.get("createdRecords", []))
                updated += len(data.get("updatedRecords", []))
            else:
                log.error(
                    f"[AT] UPSERT {i}–{i+len(chunk)} → "
                    f"{resp.status_code}: {resp.text[:200]}"
                )

            if show_progress and (i % 100 == 0 or i + MAX_RECORDS_PER_BATCH >= total):
                pct = min(100, int((i + len(chunk)) / total * 100))
                print(f"  [{pct:3d}%] {created:,} created / {updated:,} updated", end="\r")

            time.sleep(RATE_LIMIT_SLEEP)

        if show_progress:
            print(f"  [100%] {created:,} created / {updated:,} updated    ")
        return {"created": created, "updated": updated}

    def update(self, table: str, record_id: str, fields: dict) -> bool:
        """Update a single record by ID."""
        url = f"{AIRTABLE_API}/{self.base_id}/{table}/{record_id}"
        resp = requests.patch(url, json={"fields": fields}, headers=self.headers, timeout=15)
        if not resp.ok:
            log.error(f"[AT] UPDATE {table}/{record_id} → {resp.status_code}")
        return resp.ok

    def delete(self, table: str, record_id: str) -> bool:
        """Delete a single record by ID."""
        url = f"{AIRTABLE_API}/{self.base_id}/{table}/{record_id}"
        resp = requests.delete(url, headers=self.headers, timeout=15)
        return resp.ok

    # ── Schema inspection ──────────────────────────────────────────────

    def table_fields(self, table: str) -> list[str]:
        """Return field names from the first record (quick schema peek)."""
        records = self._list(table, max_records=1)
        if records:
            return list(records[0].get("fields", {}).keys())
        return []

    # ── Helpers ────────────────────────────────────────────────────────

    def _list(
        self,
        table: str,
        formula: Optional[str] = None,
        max_records: int = 5000,
        page_size: int = 100,
    ) -> list[dict]:
        url = f"{AIRTABLE_API}/{self.base_id}/{table}"
        params: dict = {"pageSize": min(page_size, max_records)}
        if formula:
            params["filterByFormula"] = formula

        results = []
        offset = None

        while True:
            if offset:
                params["offset"] = offset
            resp = requests.get(url, params=params, headers=self.headers, timeout=20)
            if not resp.ok:
                log.error(f"[AT] LIST {table} → {resp.status_code}: {resp.text[:200]}")
                break

            data = resp.json()
            results.extend(data.get("records", []))
            offset = data.get("offset")

            if not offset or len(results) >= max_records:
                break

            time.sleep(RATE_LIMIT_SLEEP)

        return results[:max_records]

    def _build_formula(self, kwargs: dict) -> str:
        """
        Convert kwargs to Airtable filterByFormula string.

        Supported patterns:
          field=value          → {Field}="value"
          field=123            → {Field}=123
          field=None           → {Field}=""
          field__not=value     → NOT({Field}="value")
          field__gt=100        → {Field}>100
          field__lt=100        → {Field}<100
          field__contains=str  → FIND("str", {Field})>0
        """
        clauses = []
        for key, val in kwargs.items():
            if key.endswith("__not"):
                field = self._field_name(key[:-5])
                clauses.append(f'NOT({{{field}}}="{val}")')
            elif key.endswith("__gt"):
                field = self._field_name(key[:-4])
                clauses.append(f"{{{field}}}>{val}")
            elif key.endswith("__lt"):
                field = self._field_name(key[:-4])
                clauses.append(f"{{{field}}}<{val}")
            elif key.endswith("__contains"):
                field = self._field_name(key[:-10])
                clauses.append(f'FIND("{val}", {{{field}}})>0')
            elif val is None:
                field = self._field_name(key)
                clauses.append(f'{{{field}}}=""')
            elif isinstance(val, (int, float)):
                field = self._field_name(key)
                clauses.append(f"{{{field}}}={val}")
            else:
                field = self._field_name(key)
                clauses.append(f'{{{field}}}="{val}"')

        if len(clauses) == 1:
            return clauses[0]
        return "AND(" + ", ".join(clauses) + ")"

    def _field_name(self, key: str) -> str:
        """Convert python-style snake_case key to Airtable Title_Case field name."""
        return "_".join(part.capitalize() for part in key.split("_"))

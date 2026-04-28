"""
FDIC BankFind API + NCUA data client.

Account universe layer — pulls every US bank and credit union from
authoritative government sources. Zero cost, no API key required.

FDIC API: https://api.fdic.gov/banks/
NCUA data: https://www.ncua.gov/analysis/credit-union-corporate-call-report-data

Asset-to-employee proxy (rough):
  $100M–$500M   →  50–300 employees
  $500M–$2B     →  200–1,000 employees  ← core ICP
  $2B–$10B      →  500–3,000 employees  ← core ICP
  $10B+         →  enterprise (out of scope)
"""

import csv
import io
import logging
import time
from dataclasses import dataclass
from typing import Optional

import requests

log = logging.getLogger("atlas.fdic")

FDIC_API = "https://api.fdic.gov/banks/institutions"
NCUA_CSV = "https://www.ncua.gov/files/publications/analysis/call-report-data/call-report-data-2024-Q3.zip"

# ICP asset range in thousands (FDIC reports in $thousands)
# $100M = 100,000 thousands → $10B = 10,000,000 thousands
ASSET_MIN_K = 100_000      # $100M
ASSET_MAX_K = 10_000_000   # $10B

FDIC_FIELDS = [
    "NAME", "CERT", "CITY", "STALP", "ZIP", "ADDRESS",
    "ASSET", "WEBADDR", "PHONE", "ESTYMD", "HCTMULT",
    "SPECGRP", "ACTIVE",
]


@dataclass
class Institution:
    cert_id: str            # FDIC cert number or NCUA charter number
    source: str             # "fdic" | "ncua"
    name: str
    city: str
    state: str
    zip_code: str
    address: str
    asset_k: int            # total assets in $thousands
    website: str
    phone: str
    established: str
    holding_company: bool   # part of a multi-bank holding company
    institution_type: str   # "bank" | "credit_union" | "savings"

    @property
    def domain(self) -> Optional[str]:
        if not self.website:
            return None
        w = self.website.lower().strip()
        w = w.replace("https://", "").replace("http://", "").replace("www.", "")
        return w.split("/")[0] or None

    @property
    def asset_usd_m(self) -> int:
        return self.asset_k // 1000

    @property
    def employee_estimate(self) -> str:
        m = self.asset_usd_m
        if m < 200:
            return "50-200"
        elif m < 500:
            return "100-400"
        elif m < 1000:
            return "200-700"
        elif m < 2000:
            return "400-1200"
        elif m < 5000:
            return "800-2500"
        else:
            return "1500-5000"

    def is_icp(self) -> bool:
        return ASSET_MIN_K <= self.asset_k <= ASSET_MAX_K

    def display(self) -> str:
        return (
            f"{self.name} | {self.city}, {self.state} | "
            f"${self.asset_usd_m}M assets | {self.employee_estimate} emp est. | "
            f"{self.domain or 'no website'}"
        )


class FDICClient:
    """Pulls all active FDIC-insured banks in the ICP asset range."""

    PAGE_SIZE = 10_000

    def get_institutions(
        self,
        asset_min_k: int = ASSET_MIN_K,
        asset_max_k: int = ASSET_MAX_K,
        states: Optional[list[str]] = None,
    ) -> list[Institution]:
        results = []
        offset = 0

        state_filter = ""
        if states:
            state_filter = " AND (" + " OR ".join(f"STALP:{s}" for s in states) + ")"

        asset_filter = f"ASSET:[{asset_min_k} TO {asset_max_k}]"
        filters = f"ACTIVE:1 AND {asset_filter}{state_filter}"

        log.info(f"[FDIC] Pulling institutions: {filters}")

        while True:
            params = {
                "filters": filters,
                "fields": ",".join(FDIC_FIELDS),
                "limit": self.PAGE_SIZE,
                "offset": offset,
                "sort_by": "ASSET",
                "sort_order": "DESC",
            }
            resp = requests.get(FDIC_API, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            batch = data.get("data", [])
            total = data["meta"]["total"]

            for row in batch:
                r = row["data"]
                results.append(Institution(
                    cert_id=str(r.get("CERT", "")),
                    source="fdic",
                    name=r.get("NAME", ""),
                    city=r.get("CITY", ""),
                    state=r.get("STALP", ""),
                    zip_code=r.get("ZIP", ""),
                    address=r.get("ADDRESS", ""),
                    asset_k=int(r.get("ASSET", 0)),
                    website=r.get("WEBADDR", ""),
                    phone=r.get("PHONE", ""),
                    established=r.get("ESTYMD", ""),
                    holding_company=r.get("HCTMULT", "") == "1",
                    institution_type=self._classify_type(r),
                ))

            offset += len(batch)
            log.info(f"[FDIC] Fetched {offset}/{total}")

            if offset >= total:
                break

            time.sleep(0.5)

        log.info(f"[FDIC] Done — {len(results)} institutions")
        return results

    def _classify_type(self, r: dict) -> str:
        specgrp = str(r.get("SPECGRP", ""))
        name = r.get("NAME", "").lower()
        if "credit union" in name:
            return "credit_union"
        if "savings" in name or "thrift" in name or specgrp in ("3", "4"):
            return "savings"
        return "bank"


class NCUAClient:
    """
    Pulls NCUA-insured credit unions.

    NCUA publishes quarterly call report data as a ZIP of CSVs.
    We use the FS Performance Report which includes charter number,
    name, city, state, assets, and member count.
    """

    # Direct NCUA API endpoint (returns JSON for active credit unions)
    NCUA_SEARCH_URL = "https://www.ncua.gov/api/CreditUnionData/SearchCreditUnions"

    def get_institutions(
        self,
        asset_min_k: int = ASSET_MIN_K,
        asset_max_k: int = ASSET_MAX_K,
    ) -> list[Institution]:
        results = []

        # NCUA API: paginate by state to stay within limits
        states = [
            "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN",
            "IA","KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV",
            "NH","NJ","NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN",
            "TX","UT","VT","VA","WA","WV","WI","WY","DC",
        ]

        for state in states:
            try:
                batch = self._fetch_state(state, asset_min_k, asset_max_k)
                results.extend(batch)
                log.debug(f"[NCUA] {state}: {len(batch)} credit unions")
                time.sleep(0.3)
            except Exception as e:
                log.warning(f"[NCUA] {state} failed: {e}")

        log.info(f"[NCUA] Done — {len(results)} credit unions")
        return results

    def _fetch_state(
        self, state: str, asset_min_k: int, asset_max_k: int
    ) -> list[Institution]:
        results = []
        page = 1
        page_size = 200

        while True:
            params = {
                "StateCode": state,
                "ActiveCode": "Active",
                "PageNumber": page,
                "PageSize": page_size,
            }
            resp = requests.get(self.NCUA_SEARCH_URL, params=params, timeout=20)

            if resp.status_code != 200:
                break

            data = resp.json()
            if not data or not isinstance(data, list):
                break

            for cu in data:
                assets_k = int(cu.get("TotalAssets", 0)) // 1000
                if not (asset_min_k <= assets_k <= asset_max_k):
                    continue

                results.append(Institution(
                    cert_id=str(cu.get("CUNumber", "")),
                    source="ncua",
                    name=cu.get("CreditUnionName", ""),
                    city=cu.get("City", ""),
                    state=cu.get("State", state),
                    zip_code=cu.get("PostalCode", ""),
                    address=cu.get("AddressLine1", ""),
                    asset_k=assets_k,
                    website=cu.get("WebsiteURL", ""),
                    phone=cu.get("MainPhone", ""),
                    established=cu.get("CharterDate", ""),
                    holding_company=False,
                    institution_type="credit_union",
                ))

            if len(data) < page_size:
                break
            page += 1

        return results


class InstitutionUniverse:
    """Combined FDIC + NCUA universe — the full ICP account list."""

    def __init__(self):
        self.fdic = FDICClient()
        self.ncua = NCUAClient()

    def pull(
        self,
        asset_min_k: int = ASSET_MIN_K,
        asset_max_k: int = ASSET_MAX_K,
        states: Optional[list[str]] = None,
        include_credit_unions: bool = True,
    ) -> list[Institution]:
        log.info("[UNIVERSE] Pulling FDIC banks...")
        banks = self.fdic.get_institutions(asset_min_k, asset_max_k, states)

        credit_unions = []
        if include_credit_unions:
            log.info("[UNIVERSE] Pulling NCUA credit unions...")
            credit_unions = self.ncua.get_institutions(asset_min_k, asset_max_k)

        all_institutions = banks + credit_unions
        log.info(
            f"[UNIVERSE] Total: {len(all_institutions)} "
            f"({len(banks)} banks, {len(credit_unions)} credit unions)"
        )
        return all_institutions

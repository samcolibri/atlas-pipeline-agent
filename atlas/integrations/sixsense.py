"""
6sense integration for ATLAS.

Available on this token:
  - Company Firmographics  → enrich any domain with size, revenue, phone, SIC
  - People Enrichment      → enrich contacts by email

NOT available (no intent/intelligence plan):
  - Account buying stage / intent scores
  - In-market account discovery
"""

import os
import requests
from dataclasses import dataclass, field
from typing import Optional


FIRMOGRAPHICS_URL = "https://api.6sense.com/v1/enrichment/company"
PEOPLE_URL = "https://api.6sense.com/v2/enrichment/people"


@dataclass
class CompanyProfile:
    domain: str
    name: str
    industry: str
    employee_count: str          # exact e.g. "937"
    employee_range: str          # e.g. "500 - 999"
    annual_revenue: str          # exact dollars e.g. "203039000"
    revenue_range: str           # e.g. "$100M - $250M"
    city: str
    state: str
    country: str
    phone: str
    sic_code: str
    sic_description: str
    naics_code: str
    naics_description: str
    segments: list[str] = field(default_factory=list)

    @property
    def revenue_millions(self) -> Optional[float]:
        try:
            return round(int(self.annual_revenue) / 1_000_000, 1)
        except (ValueError, ZeroDivisionError):
            return None

    def summary(self) -> str:
        """One-line summary for prompt injection."""
        rev = f"${self.revenue_millions}M" if self.revenue_millions else self.revenue_range
        return (
            f"{self.name} ({self.domain}) | {self.industry} | "
            f"{self.employee_count} employees | {rev} revenue | "
            f"{self.city}, {self.state} | {self.sic_description}"
        )


@dataclass
class ContactProfile:
    email: str
    full_name: str
    job_title: str
    function: str
    level: str
    linkedin_url: str
    phone: str
    city: str
    state: str

    def summary(self) -> str:
        parts = [self.full_name or self.email]
        if self.job_title:
            parts.append(self.job_title)
        if self.city and self.state:
            parts.append(f"{self.city}, {self.state}")
        if self.linkedin_url:
            parts.append(self.linkedin_url)
        return " | ".join(parts)


class SixSenseClient:
    def __init__(self, api_key: Optional[str] = None):
        self._key = api_key or os.environ["SIXSENSE_API_KEY"]
        self._form_headers = {
            "Authorization": f"Token {self._key}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        self._json_headers = {
            "Authorization": f"Token {self._key}",
            "Content-Type": "application/json",
        }

    def get_company(self, domain: str) -> Optional[CompanyProfile]:
        """Enrich a domain with firmographic data."""
        try:
            r = requests.post(
                FIRMOGRAPHICS_URL,
                headers=self._form_headers,
                data={"domain": domain},
                timeout=15,
            )
            r.raise_for_status()
        except requests.RequestException as e:
            print(f"[6sense] firmographics error for {domain}: {e}")
            return None

        co = r.json().get("company", {})
        if not co.get("name"):
            return None

        segs = r.json().get("segments", {}).get("names", [])
        return CompanyProfile(
            domain=co.get("domain", domain),
            name=co.get("name", ""),
            industry=co.get("industry", ""),
            employee_count=co.get("employeeCount", ""),
            employee_range=co.get("employeeRange", ""),
            annual_revenue=co.get("annualRevenue", ""),
            revenue_range=co.get("revenueRange", ""),
            city=co.get("city", ""),
            state=co.get("state", ""),
            country=co.get("country", ""),
            phone=co.get("companyPhone", ""),
            sic_code=co.get("siccode", ""),
            sic_description=co.get("sicdescription", ""),
            naics_code=co.get("naicscode", ""),
            naics_description=co.get("naicsdescription", ""),
            segments=segs,
        )

    def enrich_contacts(self, emails: list[str]) -> list[ContactProfile]:
        """Enrich a list of emails with contact details."""
        if not emails:
            return []
        try:
            r = requests.post(
                PEOPLE_URL,
                headers=self._json_headers,
                json=[{"email": e} for e in emails],
                timeout=15,
            )
            r.raise_for_status()
        except requests.RequestException as e:
            print(f"[6sense] people enrichment error: {e}")
            return []

        results = []
        for c in r.json().get("contacts", []):
            if not c.get("email"):
                continue
            results.append(ContactProfile(
                email=c.get("email", ""),
                full_name=c.get("fullName", ""),
                job_title=c.get("jobTitle", ""),
                function=c.get("function", ""),
                level=c.get("level", ""),
                linkedin_url=c.get("linkedinUrl", ""),
                phone=c.get("workPhone") or c.get("phone", ""),
                city=c.get("city", ""),
                state=c.get("state", ""),
            ))
        return results

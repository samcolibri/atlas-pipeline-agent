"""
RECON Agent — Account Intelligence via 6sense.

Given a domain, returns structured firmographic data for FORGE to use.
No external AI calls — pure 6sense data.

Usage:
    from atlas.agents.recon import ReconAgent
    brief = ReconAgent().run("independentbank.com")
    print(brief.summary())
"""

import logging
from dataclasses import dataclass, field
from typing import Optional

from atlas.integrations.sixsense import SixSenseClient, CompanyProfile

log = logging.getLogger("atlas.recon")

FS_SIC_CODES = {
    "6020": "State commercial banks",
    "6021": "National commercial banks",
    "6022": "State commercial banks — Federal Reserve members",
    "6029": "Commercial banks NEC",
    "6035": "Savings institutions — federally chartered",
    "6036": "Savings institutions — not federally chartered",
    "6061": "Federal credit unions",
    "6062": "State credit unions",
}

TARGET_TITLES = [
    "CHRO", "Chief Human Resources Officer",
    "VP of Human Resources", "VP HR",
    "Head of Learning & Development", "L&D Director",
    "Chief People Officer",
]


@dataclass
class ReconBrief:
    domain: str
    name: str
    industry: str
    employee_count: str
    revenue_range: str
    annual_revenue_usd: str
    city: str
    state: str
    phone: str
    sic_code: str
    sic_description: str
    naics_description: str
    is_fs_target: bool
    pitch_angle: str
    raw: Optional[CompanyProfile] = None

    def summary(self) -> str:
        flag = "✅ FS ICP" if self.is_fs_target else "⚠️  not primary ICP"
        return (
            f"  Company:  {self.name} ({self.domain})\n"
            f"  Industry: {self.industry} — {self.sic_description}\n"
            f"  Size:     {self.employee_count} employees | {self.revenue_range}\n"
            f"  Location: {self.city}, {self.state}\n"
            f"  Phone:    {self.phone}\n"
            f"  ICP:      {flag}\n"
            f"  Angle:    {self.pitch_angle}\n"
            f"  Titles:   {', '.join(TARGET_TITLES[:3])}"
        )

    def to_dict(self) -> dict:
        return {
            "domain": self.domain,
            "name": self.name,
            "industry": self.industry,
            "employee_count": self.employee_count,
            "revenue_range": self.revenue_range,
            "annual_revenue_usd": self.annual_revenue_usd,
            "city": self.city,
            "state": self.state,
            "phone": self.phone,
            "sic_code": self.sic_code,
            "sic_description": self.sic_description,
            "naics_description": self.naics_description,
            "is_fs_target": self.is_fs_target,
            "pitch_angle": self.pitch_angle,
            "target_titles": TARGET_TITLES,
        }


class ReconAgent:
    def __init__(self):
        self._6s = SixSenseClient()

    def run(self, domain: str, known_emails: Optional[list[str]] = None) -> Optional[ReconBrief]:
        log.info(f"RECON: {domain}")

        profile = self._6s.get_company(domain)
        if not profile:
            log.warning(f"  no 6sense data for {domain}")
            return None

        contacts = []
        if known_emails:
            contacts = self._6s.enrich_contacts(known_emails)
            log.info(f"  {len(contacts)} contacts enriched")

        is_fs = profile.sic_code in FS_SIC_CODES
        angle = self._pick_angle(profile)

        log.info(f"  {profile.name} | {profile.employee_count} emp | {profile.revenue_range} | {'FS ICP' if is_fs else 'not ICP'}")

        return ReconBrief(
            domain=domain,
            name=profile.name,
            industry=profile.industry,
            employee_count=profile.employee_count,
            revenue_range=profile.revenue_range,
            annual_revenue_usd=profile.annual_revenue,
            city=profile.city,
            state=profile.state,
            phone=profile.phone,
            sic_code=profile.sic_code,
            sic_description=profile.sic_description,
            naics_description=profile.naics_description,
            is_fs_target=is_fs,
            pitch_angle=angle,
            raw=profile,
        )

    def run_batch(self, domains: list[str]) -> list[ReconBrief]:
        """Run RECON on a list of domains, skipping any with no data."""
        results = []
        for domain in domains:
            brief = self.run(domain)
            if brief:
                results.append(brief)
        return results

    def _pick_angle(self, p: CompanyProfile) -> str:
        emp = int(p.employee_count or 0)
        sic = p.sic_code
        if sic in ("6061", "6062"):
            return "credit_union_community_mission"
        if sic in ("6035", "6036"):
            return "savings_institution_compliance"
        if emp >= 5000:
            return "enterprise_bank_scale"
        if emp >= 1000:
            return "mid_market_bank_grc"
        if emp < 500:
            return "community_bank_relationship"
        return "general_fs_compliance"

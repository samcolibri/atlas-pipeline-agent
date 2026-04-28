"""
FORGE Agent — Email Writer for ATLAS.

Takes a ReconBrief and writes a personalized cold email using:
  - POV framework (trigger → complexity → risk → proof → CTA)
  - OCL case studies matched to account type
  - 6sense firmographic data filled in

No LLM required — template-based, deterministic, fast.

Usage:
    from atlas.agents.forge import ForgeAgent
    from atlas.agents.recon import ReconAgent

    brief = ReconAgent().run("heartlandbank.com")
    email = ForgeAgent().run(brief)
    print(email.subject)
    print(email.body)
"""

from dataclasses import dataclass
from typing import Optional
from atlas.agents.recon import ReconBrief, TARGET_TITLES


# ── Case studies ──────────────────────────────────────────────────────────────

CASE_STUDIES = {
    "citadel_cu": {
        "company": "Citadel Credit Union",
        "detail": "a $6B credit union in Pennsylvania with 600+ employees",
        "challenge": "needed to train all frontline, lending, and data staff on Fair Lending — fast, across 24 branches",
        "outcome": "deployed Live Private Classes that got every employee trained on schedule",
        "fit": ["credit_union_community_mission"],
    },
    "security_first": {
        "company": "Security First Bank",
        "detail": "a community bank in Nebraska with 280+ employees across 26 branches",
        "challenge": "needed consistent compliance training as they acquired new branches across two states",
        "outcome": "built a centralized training program that scaled with their growth",
        "fit": ["community_bank_relationship", "general_fs_compliance"],
    },
    "marthas_vineyard": {
        "company": "Martha's Vineyard Bank",
        "detail": "a 110-year-old Massachusetts community bank with 100+ employees",
        "challenge": "needed training that covered compliance requirements AND relationship development for each department",
        "outcome": "partnered with OCL to deliver role-specific training that aligned with their strategic goals",
        "fit": ["community_bank_relationship", "savings_institution_compliance"],
    },
}

# ── Pain points by pitch angle ────────────────────────────────────────────────

ANGLES = {
    "credit_union_community_mission": {
        "trigger": "growth in membership and branch count",
        "complexity": "your team is managing NCUA compliance and Fair Lending requirements across a larger footprint",
        "risk": "gaps in consistent compliance training across branches — which regulators catch in the next exam",
        "regulations": "NCUA, Fair Lending, BSA/AML",
        "case_study": "citadel_cu",
        "subject_hook": "compliance training across {employee_count} employees",
    },
    "community_bank_relationship": {
        "trigger": "growth through branch expansion or acquisition",
        "complexity": "your training team is keeping up with BSA/AML and TILA requirements across locations with different staffing levels",
        "risk": "inconsistent compliance knowledge across branches — which creates exam exposure and customer-facing risk",
        "regulations": "BSA/AML, TILA, fair lending",
        "case_study": "security_first",
        "subject_hook": "compliance consistency across {employee_count} employees",
    },
    "mid_market_bank_grc": {
        "trigger": "growing headcount and regulatory complexity",
        "complexity": "your L&D team is managing GRC training requirements across multiple business lines and hundreds of employees",
        "risk": "compliance training gaps at scale — inconsistency that regulators flag and that your HR team has to scramble to close",
        "regulations": "BSA/AML, CRA, fair lending, TILA",
        "case_study": "citadel_cu",
        "subject_hook": "GRC training at {employee_count} employees",
    },
    "savings_institution_compliance": {
        "trigger": "regulatory pressure on lending and deposit products",
        "complexity": "your team is managing RESPA, TILA, and fair lending training for staff across the org",
        "risk": "training that doesn't keep pace with regulatory updates — which creates liability when examiners ask",
        "regulations": "RESPA, TILA, fair lending, NCUA",
        "case_study": "marthas_vineyard",
        "subject_hook": "lending compliance training at {employee_count} employees",
    },
    "enterprise_bank_scale": {
        "trigger": "scale and multi-region operations",
        "complexity": "your L&D function is managing compliance training for thousands of employees across business lines with different regulatory requirements",
        "risk": "inconsistent compliance coverage — which creates audit exposure and CE credit gaps your HR team has to track manually",
        "regulations": "BSA/AML, CRA, TILA, fair lending, OCC/Fed requirements",
        "case_study": "citadel_cu",
        "subject_hook": "compliance training at scale",
    },
    "general_fs_compliance": {
        "trigger": "ongoing regulatory requirements",
        "complexity": "your team is managing mandatory compliance training across BSA/AML, TILA, and fair lending for all staff",
        "risk": "training gaps that surface during regulatory exams — or manual CE tracking that creates admin overhead",
        "regulations": "BSA/AML, TILA, fair lending",
        "case_study": "security_first",
        "subject_hook": "compliance training at {employee_count} employees",
    },
}


# ── Email output ──────────────────────────────────────────────────────────────

@dataclass
class EmailDraft:
    domain: str
    company_name: str
    subject: str
    body: str
    pitch_angle: str
    case_study_used: str
    target_titles: list[str]

    def display(self) -> str:
        titles = ", ".join(self.target_titles[:3])
        return (
            f"  To:       {titles} @ {self.company_name}\n"
            f"  Subject:  {self.subject}\n"
            f"\n"
            f"{self.body}\n"
            f"\n"
            f"  [Angle: {self.pitch_angle} | Proof: {self.case_study_used}]"
        )

    def to_dict(self) -> dict:
        return {
            "domain": self.domain,
            "company_name": self.company_name,
            "subject": self.subject,
            "body": self.body,
            "pitch_angle": self.pitch_angle,
            "case_study_used": self.case_study_used,
            "target_titles": self.target_titles,
        }


# ── FORGE agent ───────────────────────────────────────────────────────────────

class ForgeAgent:

    def run(self, brief: ReconBrief) -> Optional[EmailDraft]:
        angle_data = ANGLES.get(brief.pitch_angle, ANGLES["general_fs_compliance"])
        cs_key = angle_data["case_study"]
        cs = CASE_STUDIES[cs_key]

        subject = self._build_subject(brief, angle_data)
        body = self._build_body(brief, angle_data, cs)

        return EmailDraft(
            domain=brief.domain,
            company_name=brief.name,
            subject=subject,
            body=body,
            pitch_angle=brief.pitch_angle,
            case_study_used=cs["company"],
            target_titles=TARGET_TITLES,
        )

    def run_batch(self, briefs: list[ReconBrief]) -> list[EmailDraft]:
        results = []
        for brief in briefs:
            draft = self.run(brief)
            if draft:
                results.append(draft)
        return results

    def _build_subject(self, brief: ReconBrief, angle: dict) -> str:
        hook = angle["subject_hook"].format(
            employee_count=brief.employee_count,
            company=brief.name,
            city=brief.city,
        )
        return f"{brief.name}'s {hook}"

    def _build_body(self, brief: ReconBrief, angle: dict, cs: dict) -> str:
        first_name = "[First Name]"
        sender = "Sam"

        # Line 1: trigger observation (specific to this company)
        line1 = (
            f"Hi {first_name},\n\n"
            f"{brief.name}'s {angle['trigger']} likely means "
            f"{angle['complexity'].replace('{employee_count}', brief.employee_count)}."
        )

        # Line 2: the risk
        line2 = (
            f"That creates {angle['risk']}."
        )

        # Line 3: proof
        line3 = (
            f"We helped {cs['company']} — {cs['detail']} — who {cs['challenge']}. "
            f"They {cs['outcome']}."
        )

        # Line 4: CTA
        line4 = "Worth a quick conversation?\n\nBest,\n" + sender

        return "\n\n".join([line1, line2, line3, line4])

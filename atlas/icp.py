"""
ATLAS ICP constants — single source of truth for title matching,
lane prioritization, and CTA variants.

All agents (RECON, FORGE, CORTEX) import from here. Never hardcode
title strings or CTAs in agent files.
"""

# ── Title priority lanes ───────────────────────────────────────────────
# Order is fixed: compliance > hr > l_and_d
# If multiple contacts found at one account, email in this order.

COMPLIANCE_TITLES = [
    "Chief Compliance Officer",
    "CCO",
    "Compliance Officer",
    "VP Compliance",
    "VP of Compliance",
    "Director of Compliance",
    "Director, Compliance",
    "BSA Officer",
    "BSA/AML Officer",
    "BSA Compliance Officer",
    "Fair Lending Officer",
    "Fair Lending Compliance Officer",
    "Risk and Compliance Manager",
    "Compliance Manager",
    "Compliance Director",
    "Chief Risk and Compliance Officer",
    "SVP Compliance",
    "EVP Compliance",
    "Head of Compliance",
    "Head of Risk and Compliance",
    "AML Officer",
    "Anti-Money Laundering Officer",
    "Chief Risk Officer",
    "CRO",
    "Regulatory Compliance Officer",
    "Compliance and Risk Officer",
]

HR_TITLES = [
    "CHRO",
    "Chief Human Resources Officer",
    "Chief People Officer",
    "CPO",
    "VP Human Resources",
    "VP of HR",
    "VP of Human Resources",
    "HR Director",
    "Director of Human Resources",
    "Director, Human Resources",
    "HR Manager",
    "Human Resources Manager",
    "Director of People",
    "People Director",
    "SVP Human Resources",
    "EVP Human Resources",
    "Head of HR",
    "Head of People",
    "People Operations Director",
    "VP People",
    "VP of People",
]

L_AND_D_TITLES = [
    "Director of Learning & Development",
    "Director of Learning and Development",
    "L&D Director",
    "Learning & Development Director",
    "Training Director",
    "Director of Training",
    "Training Manager",
    "Director of Training and Development",
    "VP of Training",
    "VP Training",
    "Learning Manager",
    "Learning and Development Manager",
    "Learning & Development Manager",
    "Corporate Trainer",
    "Chief Learning Officer",
    "CLO",
    "Head of Learning",
    "Head of Training",
    "Training and Development Manager",
    "Talent Development Manager",
    "Director of Talent Development",
]

# Lane definitions — ordered by priority
ICP_LANES = [
    {
        "name":     "compliance",
        "label":    "Compliance",
        "priority": 1,
        "titles":   COMPLIANCE_TITLES,
    },
    {
        "name":     "hr",
        "label":    "HR",
        "priority": 2,
        "titles":   HR_TITLES,
    },
    {
        "name":     "l_and_d",
        "label":    "L&D / Training",
        "priority": 3,
        "titles":   L_AND_D_TITLES,
    },
]

# Fast lookup: title (lowercased) → (lane_name, priority)
_TITLE_INDEX: dict[str, tuple[str, int]] = {}
for _lane in ICP_LANES:
    for _title in _lane["titles"]:
        _TITLE_INDEX[_title.lower()] = (_lane["name"], _lane["priority"])


def classify_title(title: str) -> tuple[str, int]:
    """
    Match a contact title to an ICP lane.
    Returns (lane_name, priority) or ("unknown", 99) if no match.

    Matching is substring-based so partial titles work:
      "SVP, BSA Compliance" → ("compliance", 1)
      "Training and Development Manager" → ("l_and_d", 3)
    """
    title_lower = title.lower()

    # Exact match first
    if title_lower in _TITLE_INDEX:
        return _TITLE_INDEX[title_lower]

    # Substring match — find the highest-priority lane whose title appears
    best_lane = "unknown"
    best_priority = 99
    for known_title, (lane, priority) in _TITLE_INDEX.items():
        if known_title in title_lower or title_lower in known_title:
            if priority < best_priority:
                best_priority = priority
                best_lane = lane

    return best_lane, best_priority


def is_icp_title(title: str) -> bool:
    lane, priority = classify_title(title)
    return priority < 99


# ── CTA variants ───────────────────────────────────────────────────────
# Start A/B with these two. CORTEX tracks reply rate per variant.
# Add variants C-J once we hit N=50 sends per variant.

CTA_VARIANTS: dict[str, str] = {
    "A": (
        "Are you reviewing your compliance training vendor for 2026 or 2027 renewal, "
        "or is that owned by someone else on the compliance/HR side?"
    ),
    "B": (
        "If you and the team are thinking about other compliance training vendors this year, "
        "would you be opposed to a conversation?"
    ),
}

# Default starting variant (will be overridden by CORTEX based on performance)
DEFAULT_CTA_VARIANT = "A"


# ── Email frameworks ───────────────────────────────────────────────────

EMAIL_FRAMEWORKS = ["5P", "KCPOV"]


# ── Renewal status values ──────────────────────────────────────────────

RENEWAL_STATUSES = [
    "unknown",       # default — haven't asked yet
    "evaluating",    # actively looking at vendors
    "confirmed",     # confirmed renewal window + owner
    "not_this_year", # renewal is later, flag for re-engage
    "re_engage",     # came back from not_this_year
    "do_not_contact",
]


# ── Sendability gates ──────────────────────────────────────────────────
# All 8 must pass before FORGE generates an email.

SENDABILITY_GATES = [
    "account_in_fdic_ncua",
    "not_in_sf_suppression",
    "has_real_trigger",
    "contact_is_icp_title",
    "email_passes_zerobounce",
    "domain_has_deliverability",
    "message_has_specific_reason",
    "agent_has_recovery_path",
]

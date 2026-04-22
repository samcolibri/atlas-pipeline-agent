# ATLAS Agent Brain — OCL Source Intelligence

**Location:** `docs/ocl-brain/`
**Purpose:** Ground truth for RECON research briefs and FORGE outreach generation. Every file here represents verified Colibri / OnCourse Learning (OCL) intelligence that agents MUST use instead of making assumptions.

The binary files (PDFs, .docx, .pptx) are **local only — not committed to git**. This index (`BRAIN.md`) is committed so the repo documents what's available and how to use it.

---

## How Agents Use This Brain

### RECON (Account Research Agent)
Before writing a research brief for any Tier 3 account, RECON reads:
1. `Buyer Personas.pdf` + `OCL Personas 2020.pdf` + `OnCourse Learning B2B Personas.pptx` → match account to the right persona
2. `FS ICP Mapping (Session 1 - Sales).docx` → validate account fits ICP criteria
3. `OCL_5Ps_by_ICP.docx` → pull the right positioning (Product, Price, Place, Promotion, People) for that ICP
4. `2026 Research Reports/` → inject market context (CHRO priorities, HR trends, state of HR) as "why now" signals
5. `OCL Case Studies/` → find the closest matching case study for the account's profile

RECON output must reference at least one persona match + one relevant market signal from the 2026 reports.

### FORGE (Outreach Generation Agent)
Before writing any cold email, FORGE reads:
1. `POV Email and Example Templates.pdf` + `Exercises for Advanced Cold Email Copywriting POV Edition.pdf` → follow the POV email framework, not generic cold email
2. `OCL Story Brand Scripts - May 2023.docx` → use OCL's StoryBrand narrative structure
3. `Sales Story & Our Why.pptx` → ground the email in OCL's "why" — not product features
4. `SS - Why OnCourse Learning.pdf` (bank) + `SS - Why OnCourse Learning (Non-Bank).pdf` → use correct sales sheet angle by account type
5. `Corporate Brochure - B2B Financial Services.pdf` → for company-level proof points
6. `FS_Testimonials_PDF.pdf` → pull a relevant testimonial if the account matches a testimonial case

FORGE output must follow POV email structure. No generic "I wanted to reach out" openers.

---

## File Index

### Buyer Intelligence

| File | What's in it | Which Agent Uses It |
|------|-------------|---------------------|
| `Buyer Personas.pdf` | Primary ICP personas — titles, pain points, motivations, objections | RECON + FORGE |
| `OCL Personas 2020.pdf` | Deeper persona profiles from 2020 research (still foundational) | RECON |
| `OnCourse Learning B2B Personas.pptx` | Slide-format persona profiles with visual buyer journeys | RECON |
| `FS ICP Mapping (Session 1 - Sales).docx` | **HIGHEST PRIORITY** — FS sales team's direct ICP mapping from Session 1. Real sales leader input on who to target, who to exclude, what signals matter | RECON + SCOUT |
| `OCL_5Ps_by_ICP.docx` | 5Ps positioning matrix by ICP — maps each persona to the right product/price/promotion angle | RECON + FORGE |

### Messaging & Outreach

| File | What's in it | Which Agent Uses It |
|------|-------------|---------------------|
| `POV Email and Example Templates.pdf` | POV email framework + real example templates that have worked | FORGE |
| `Exercises for Advanced Cold Email Copywriting POV Edition.pdf` | Advanced POV copywriting techniques — exercises and principles | FORGE |
| `OCL Story Brand Scripts - May 2023.docx` | StoryBrand scripts — hero/villain/guide narrative for OCL positioning | FORGE |
| `Sales Story & Our Why.pptx` | OCL's brand story and "why we exist" — grounds all outreach in purpose | FORGE |
| `SS - Why OnCourse Learning.pdf` | Bank/credit union focused sales sheet | FORGE (bank accounts) |
| `SS - Why OnCourse Learning (Non-Bank).pdf` | Non-bank financial services sales sheet | FORGE (non-bank accounts) |
| `Corporate Brochure - B2B Financial Services.pdf` | Full FS brochure — product overview, proof points, company credibility | RECON + FORGE |
| `FS_Testimonials_PDF.pdf` | Customer testimonials from FS clients | FORGE |

### Case Studies (`OCL Case Studies/`)

| File | Account Type | Use When |
|------|-------------|----------|
| `Case Study - Citadel Credit Union.pdf` | Credit Union | Targeting credit unions |
| `Case Study - Martha's Vineyard Bank.pdf` | Community Bank (small) | Targeting small/community banks |
| `Case Study - Security First Bank.pdf` | Regional Bank | Targeting mid-size regional banks |

RECON: match the account's org type to the closest case study. Include the case study name in the research brief so FORGE can reference it.

### Market Intelligence (`2026 Research Reports/`)

| File | What's in it | Use For |
|------|-------------|---------|
| `gartner-2026-top-priorities-for-chros.pdf` | Gartner's top CHRO priorities for 2026 | "Why now" signals for HR/L&D buyer persona |
| `HR_Trends_Report_for_2026 (1).pdf` | 2026 HR trends — compliance, upskilling, workforce development | Market context for all personas |
| `hrci-2026-state-of-hr-report.pdf` | HRCI state of HR — certifications, compliance training demand | Compliance Officer persona context |

These give RECON the "why now" layer — what's happening in the market in 2026 that makes this account's pain urgent right now.

---

## The 3 Buyer Personas (from this brain)

ATLAS targets Tier 3 accounts in financial services. The three personas from the brain docs:

### 1. Compliance Officer / Chief Compliance Officer
- **Pain:** Regulatory audit prep is manual and reactive
- **Fear:** Failed audit, regulatory fine, reputational damage
- **Why OCL:** Automated compliance training tracking, always audit-ready
- **"Why Now" signal:** HRCI 2026 report — increasing regulatory scrutiny in banking
- **Use case study:** Security First Bank or Citadel Credit Union

### 2. HR / L&D Decision Maker (CHRO, VP HR, Dir of Training)
- **Pain:** Employee development is a spreadsheet + guesswork
- **Fear:** Talent attrition, skills gaps, board pressure on culture/development
- **Why OCL:** Structured LMS + compliance in one platform
- **"Why Now" signal:** Gartner CHRO 2026 priorities — retention, workforce planning
- **Use case study:** Martha's Vineyard Bank (community feel)

### 3. Operations Lead (COO, VP Operations)
- **Pain:** Onboarding is slow, inconsistent across branches
- **Fear:** Operational inefficiency, compliance gaps at scale
- **Why OCL:** Standardized training across all locations, one system
- **"Why Now" signal:** HR Trends 2026 — operational efficiency + compliance convergence
- **Use case study:** Match by bank size

---

## POV Email Framework (from brain docs — FORGE must follow this)

POV = Point of View. Not "I wanted to reach out." Not features. A sharp perspective on the prospect's world.

**Structure:**
1. **Hook** — Name a specific, observable thing happening in their world (regulatory change, market trend, a thing their peers are doing)
2. **POV** — Your take on what it means for them specifically ("Most banks are doing X, but the ones winning are doing Y")
3. **Bridge** — Connect the POV to the outcome OCL delivers (one sentence, no jargon)
4. **CTA** — One question, not a pitch ("Is this something you're working through right now?")

**Rules (from the copywriting exercises doc):**
- No openers with "I" (signals it's about you, not them)
- First line must earn the second line
- One idea per email
- CTA must be a question, not a request
- Under 120 words for the body

---

## Loading Instructions for Agents

When RECON or FORGE needs to read a file from this brain:

```python
import os

BRAIN_PATH = os.path.join(os.path.dirname(__file__), '../../docs/ocl-brain')

# Example: load ICP mapping doc
icp_mapping = os.path.join(BRAIN_PATH, 'FS ICP Mapping (Session 1 - Sales).docx')

# For PDFs, use pdfplumber or pypdf2
# For .docx, use python-docx
# For .pptx, use python-pptx
```

Dependencies to add to `requirements.txt`:
```
pdfplumber>=0.10.0
python-docx>=1.1.0
python-pptx>=0.6.23
```

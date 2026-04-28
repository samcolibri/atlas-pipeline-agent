"""Quick smoke test of atlas.memory interface."""
import sys
sys.path.insert(0, ".")
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(".env"))

from atlas.memory import memory

print("── ICP Personas ──────────────────────────────────")
for p in memory.get_personas():
    hook = p.get("POV_Hook", "")[:80]
    print(f"  {p.get('Persona_Name')}: {hook}...")

print()
print("── Case Study (bank) ─────────────────────────────")
cs = memory.get_case_study(institution_type="bank")
if cs:
    print(f"  {cs.get('Company')} | {cs.get('Assets')} | {cs.get('Outcome','')[:100]}")

print()
print("── IL Accounts >$1B (sample) ─────────────────────")
accts = memory.accounts(state="IL", pipeline_status="new", asset_m__gt=1000)
for a in accts[:5]:
    print(f"  {a.get('Name')} | {a.get('City')} | ${a.get('Asset_M')}M | {a.get('Domain')}")
print(f"  ... ({len(accts)} total IL accounts >$1B)")
